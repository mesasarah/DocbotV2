"""
Splits extracted page text into overlapping chunks suitable for embedding,
while preserving page-number metadata for citation.
"""
from dataclasses import dataclass

from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.extraction_service import ExtractedPage


@dataclass
class TextChunk:
    text: str
    page_number: int
    chunk_index: int


def chunk_pages(pages: list[ExtractedPage]) -> list[TextChunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[TextChunk] = []
    idx = 0
    for page in pages:
        if not page.text.strip():
            continue
        for piece in splitter.split_text(page.text):
            if piece.strip():
                chunks.append(TextChunk(text=piece, page_number=page.page_number, chunk_index=idx))
                idx += 1
    return chunks
