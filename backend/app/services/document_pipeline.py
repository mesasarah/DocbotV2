"""
Orchestrates the full ingestion pipeline for a single document:

    extract -> chunk -> embed -> store in vector DB -> update DB status

Runs synchronously inline for now (called from a FastAPI BackgroundTask).
For heavier workloads this is the natural place to hand off to Celery --
the function signature (document_id) is already queue-friendly.
"""
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.document import Document
from app.services.chunking_service import chunk_pages
from app.services.extraction_service import ExtractionError, extract_document
from app.services.vector_store import embed_and_store_chunks


def process_document(db: Session, document_id: str, force_ocr: bool = False) -> None:
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        logger.error("process_document called with unknown document_id: {}", document_id)
        return

    document.status = "processing"
    db.commit()

    try:
        extraction = extract_document(document.file_path, document.file_type, force_ocr=force_ocr)
        chunks = chunk_pages(extraction.pages)

        stored_count = embed_and_store_chunks(
            owner_id=document.owner_id,
            document_id=document.id,
            filename=document.original_filename,
            chunks=chunks,
        )

        document.page_count = extraction.page_count
        document.chunk_count = stored_count
        document.ocr_page_count = extraction.ocr_page_count
        document.status = "indexed"
        document.indexed_at = datetime.now(UTC)
        document.error_message = ""

    except ExtractionError as exc:
        logger.error("Extraction failed for document {}: {}", document_id, exc)
        document.status = "failed"
        document.error_message = str(exc)

    except Exception as exc:  # noqa: BLE001 -- pipeline boundary, must not crash the worker
        logger.exception("Unexpected error processing document {}", document_id)
        document.status = "failed"
        document.error_message = f"Unexpected error: {exc}"

    finally:
        db.commit()
