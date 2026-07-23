from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    status: str
    page_count: int
    chunk_count: int
    ocr_page_count: int
    error_message: str
    created_at: datetime
    indexed_at: datetime | None = None


class DocumentListResponse(BaseModel):
    total: int
    documents: list[DocumentRead]
