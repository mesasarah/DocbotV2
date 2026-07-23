"""
OCR fallback for scanned PDFs, using PyMuPDF to rasterize pages and
Tesseract (via pytesseract) to read them. Runs entirely offline/locally --
no cloud OCR APIs.
"""
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from app.core.logging_config import logger

# Text extracted from a native PDF page below this length is treated as
# "no real text" -- almost certainly a scanned image, not a text layer.
SCANNED_PAGE_TEXT_THRESHOLD = 20

# Higher DPI = better OCR accuracy but slower. 300 is the standard sweet
# spot for Tesseract on printed documents.
OCR_RENDER_DPI = 300


class OCRError(Exception):
    pass


def is_tesseract_available() -> bool:
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:  # noqa: BLE001 -- any failure means "not usable"
        return False


def ocr_pdf_page(pdf_path: str, page_index: int) -> str:
    """Renders a single PDF page (0-indexed) to an image and OCRs it."""
    try:
        with fitz.open(pdf_path) as doc:
            page = doc[page_index]
            zoom = OCR_RENDER_DPI / 72  # PDF points are 72 DPI natively
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    except Exception as exc:
        raise OCRError(f"Failed to render page {page_index + 1} for OCR: {exc}") from exc

    try:
        text = pytesseract.image_to_string(image)
    except Exception as exc:
        raise OCRError(f"Tesseract failed on page {page_index + 1}: {exc}") from exc

    return text.strip()


def needs_ocr(page_text: str) -> bool:
    return len(page_text.strip()) < SCANNED_PAGE_TEXT_THRESHOLD


def log_ocr_unavailable_once() -> None:
    logger.warning(
        "Tesseract is not available on this system -- scanned pages will be "
        "indexed with empty text. Install tesseract-ocr to enable OCR."
    )
