from app.services.ocr_service import is_tesseract_available, needs_ocr


def test_needs_ocr_true_for_empty_text():
    assert needs_ocr("") is True


def test_needs_ocr_true_for_whitespace_only():
    assert needs_ocr("   \n\n   ") is True


def test_needs_ocr_true_for_very_short_text():
    assert needs_ocr("ab") is True


def test_needs_ocr_false_for_real_content():
    assert needs_ocr("This page contains a full paragraph of real extracted text content.") is False


def test_tesseract_unavailable_reported_gracefully():
    # In this test environment tesseract isn't installed -- confirms the
    # check fails closed (returns False) rather than raising.
    assert is_tesseract_available() is False
