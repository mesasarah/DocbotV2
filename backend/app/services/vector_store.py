"""
Wraps ChromaDB as the vector store, using sentence-transformers for embeddings.

Design notes:
- One Chroma collection per user ("docbot_user_<id>") keeps tenants isolated
  and search fast, without needing complex metadata pre-filtering at scale.
- Each stored chunk carries document_id, filename, and page_number in its
  metadata so retrieval results can be turned directly into citations.
"""
import uuid
from dataclasses import dataclass
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging_config import logger
from app.services.chunking_service import TextChunk


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    logger.info("Loading embedding model: {}", settings.EMBEDDING_MODEL)
    return SentenceTransformer(settings.EMBEDDING_MODEL)


@lru_cache
def get_chroma_client() -> "chromadb.ClientAPI":
    # anonymized_telemetry=False: DOCBOT is offline/privacy-first by design --
    # Chroma phoning home with usage stats (even anonymized) contradicts that,
    # and its telemetry client also has a known bug against some posthog
    # versions that spams the log with harmless but noisy errors.
    settings_obj = ChromaSettings(anonymized_telemetry=False)
    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR, settings=settings_obj)


def _collection_name(owner_id: str) -> str:
    return f"docbot_user_{owner_id.replace('-', '')}"


def get_user_collection(owner_id: str):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=_collection_name(owner_id),
        metadata={"hnsw:space": "cosine"},
    )


@dataclass
class RetrievedChunk:
    document_id: str
    filename: str
    page_number: int | None
    text: str
    score: float


def embed_and_store_chunks(
    owner_id: str,
    document_id: str,
    filename: str,
    chunks: list[TextChunk],
) -> int:
    """Embeds chunks and upserts them into the user's collection. Returns count stored."""
    if not chunks:
        return 0

    model = get_embedding_model()
    collection = get_user_collection(owner_id)

    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()

    ids = [f"{document_id}_{uuid.uuid4().hex[:8]}" for _ in chunks]
    metadatas = [
        {"document_id": document_id, "filename": filename, "page_number": c.page_number}
        for c in chunks
    ]

    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    logger.info("Stored {} chunks for document {} (owner {})", len(chunks), document_id, owner_id)
    return len(chunks)


def delete_document_chunks(owner_id: str, document_id: str) -> None:
    collection = get_user_collection(owner_id)
    collection.delete(where={"document_id": document_id})


def get_document_full_text(owner_id: str, document_id: str) -> str:
    """Concatenates all stored chunks for a document, in original order.
    Used by summarization/quiz generation so they reuse already-extracted
    text instead of re-parsing (and potentially re-OCRing) the file."""
    collection = get_user_collection(owner_id)
    results = collection.get(where={"document_id": document_id})

    if not results["ids"]:
        return ""

    # Chunk order isn't guaranteed by Chroma's storage order, but chunk_index
    # was embedded in the id suffix at write time is not reliable to parse
    # back out, so we fall back to page_number order, which is meaningful
    # for citation-quality output even if not perfectly sequential within a page.
    paired = list(zip(results["documents"], results["metadatas"], strict=True))
    paired.sort(key=lambda p: p[1].get("page_number") or 0)

    return "\n\n".join(text for text, _meta in paired)


def semantic_search(
    owner_id: str,
    query: str,
    top_k: int | None = None,
    document_ids: list[str] | None = None,
) -> list[RetrievedChunk]:
    model = get_embedding_model()
    collection = get_user_collection(owner_id)

    query_embedding = model.encode([query], convert_to_numpy=True).tolist()

    where = {"document_id": {"$in": document_ids}} if document_ids else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k or settings.TOP_K,
        where=where,
    )

    retrieved: list[RetrievedChunk] = []
    if not results["ids"] or not results["ids"][0]:
        return retrieved

    for doc_text, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0], strict=True
    ):
        # Chroma cosine distance -> similarity score in [0, 1]
        similarity = max(0.0, 1.0 - distance)
        retrieved.append(
            RetrievedChunk(
                document_id=meta["document_id"],
                filename=meta["filename"],
                page_number=meta.get("page_number"),
                text=doc_text,
                score=round(similarity, 4),
            )
        )

    return retrieved
