"""
Extracts raw text (and per-page breakdown where applicable) from uploaded files.
"""
from dataclasses import dataclass, field

import fitz  # PyMuPDF
from docx import Document as DocxDocument

from app.core.logging_config import logger
from app.services.ocr_service import (
    is_tesseract_available,
    log_ocr_unavailable_once,
    needs_ocr,
    ocr_pdf_page,
)


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    was_ocred: bool = False


@dataclass
class ExtractionResult:
    pages: list[ExtractedPage]
    full_text: str
    page_count: int
    ocr_page_count: int = 0
    ocr_pages: list[int] = field(default_factory=list)


class ExtractionError(Exception):
    pass


def extract_pdf(file_path: str, force_ocr: bool = False) -> ExtractionResult:
    pages: list[ExtractedPage] = []
    tesseract_ready: bool | None = None  # lazily checked, only if actually needed

    try:
        with fitz.open(file_path) as doc:
            for i, page in enumerate(doc):
                text = page.get_text("text") or ""
                was_ocred = False

                if force_ocr or needs_ocr(text):
                    if tesseract_ready is None:
                        tesseract_ready = is_tesseract_available()
                        if not tesseract_ready:
                            log_ocr_unavailable_once()

                    if tesseract_ready:
                        ocr_text = ocr_pdf_page(file_path, i)
                        if ocr_text.strip():
                            text = ocr_text
                            was_ocred = True
                            logger.info("OCR applied to page {} of {}", i + 1, file_path)

                pages.append(ExtractedPage(page_number=i + 1, text=text, was_ocred=was_ocred))
    except Exception as exc:
        raise ExtractionError(f"Failed to extract PDF: {exc}") from exc

    full_text = "\n\n".join(p.text for p in pages)
    ocr_pages = [p.page_number for p in pages if p.was_ocred]

    if len(full_text.strip()) < 20 and len(pages) > 0:
        logger.warning(
            "PDF has little/no extractable text even after OCR fallback: {}", file_path
        )

    return ExtractionResult(
        pages=pages,
        full_text=full_text,
        page_count=len(pages),
        ocr_page_count=len(ocr_pages),
        ocr_pages=ocr_pages,
    )


def extract_docx(file_path: str) -> ExtractionResult:
    try:
        doc = DocxDocument(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    except Exception as exc:
        raise ExtractionError(f"Failed to extract DOCX: {exc}") from exc

    full_text = "\n".join(paragraphs)
    # DOCX has no fixed pagination -- treat as a single logical page.
    return ExtractionResult(pages=[ExtractedPage(page_number=1, text=full_text)], full_text=full_text, page_count=1)


def extract_plaintext(file_path: str) -> ExtractionResult:
    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception as exc:
        raise ExtractionError(f"Failed to extract text file: {exc}") from exc

    return ExtractionResult(pages=[ExtractedPage(page_number=1, text=text)], full_text=text, page_count=1)


def extract_document(file_path: str, file_type: str, force_ocr: bool = False) -> ExtractionResult:
    file_type = file_type.lower().lstrip(".")
    if file_type == "pdf":
        return extract_pdf(file_path, force_ocr=force_ocr)
    if file_type == "docx":
        return extract_docx(file_path)
    if file_type in ("txt", "md"):
        return extract_plaintext(file_path)
    raise ExtractionError(f"Unsupported file type: {file_type}")
