from pydantic import BaseModel


class DailyCount(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class AnalyticsSummary(BaseModel):
    total_documents: int
    indexed_documents: int
    processing_documents: int
    failed_documents: int
    total_chunks: int
    total_ocr_pages: int
    total_queries: int
    total_entities: int
    uploads_by_day: list[DailyCount]
    queries_by_day: list[DailyCount]
    documents_by_type: dict[str, int]
