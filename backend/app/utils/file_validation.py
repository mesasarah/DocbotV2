import os
import uuid

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


def validate_upload(file: UploadFile) -> str:
    """Validates extension and returns the normalized extension (without dot)."""
    _, ext = os.path.splitext(file.filename or "")
    ext = ext.lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )
    return ext.lstrip(".")


def generate_stored_filename(original_filename: str) -> str:
    _, ext = os.path.splitext(original_filename)
    return f"{uuid.uuid4().hex}{ext.lower()}"


def enforce_size_limit(size_bytes: int) -> None:
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )
