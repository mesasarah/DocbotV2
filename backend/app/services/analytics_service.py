"""
Aggregation queries for the analytics dashboard. All pure SQL/ORM counting
-- nothing here touches the LLM, so it's fast and fully testable offline.

Daily bucketing is done in Python rather than with SQL date functions:
model timestamps are timezone-aware (UTC) Python datetimes but stored in a
plain (non-timezone) DateTime column, which makes SQL-level date-function
comparisons dialect-fragile (SQLite/Postgres differ on how they'd compare a
naive cutoff against an aware-looking stored string). Fetching rows and
grouping in Python sidesteps that entirely, and dataset sizes here (one
user's documents/queries) are small enough that it's not a performance
concern.
"""
from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.entity import Entity
from app.models.query_log import QueryLog
from app.schemas.analytics import AnalyticsSummary, DailyCount

DEFAULT_LOOKBACK_DAYS = 14


def _normalize(dt: datetime) -> datetime:
    """Treats naive timestamps as UTC so subtraction/comparison never raises."""
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _daily_counts(timestamps: list[datetime], days: int = DEFAULT_LOOKBACK_DAYS) -> list[DailyCount]:
    now = datetime.now(UTC)
    since = now - timedelta(days=days)

    counts_by_date: Counter[str] = Counter()
    for ts in timestamps:
        ts = _normalize(ts)
        if ts >= since:
            counts_by_date[ts.date().isoformat()] += 1

    result: list[DailyCount] = []
    for i in range(days):
        day = (since + timedelta(days=i + 1)).date().isoformat()
        result.append(DailyCount(date=day, count=counts_by_date.get(day, 0)))
    return result


def get_analytics_summary(db: Session, owner_id: str) -> AnalyticsSummary:
    documents = db.query(Document).filter(Document.owner_id == owner_id).all()
    query_logs = db.query(QueryLog).filter(QueryLog.owner_id == owner_id).all()

    total_documents = len(documents)
    indexed = sum(1 for d in documents if d.status == "indexed")
    processing = sum(1 for d in documents if d.status in ("pending", "processing"))
    failed = sum(1 for d in documents if d.status == "failed")
    total_chunks = sum(d.chunk_count for d in documents)
    total_ocr_pages = sum(d.ocr_page_count for d in documents)
    documents_by_type = dict(Counter(d.file_type for d in documents))

    total_entities = db.query(Entity).filter(Entity.owner_id == owner_id).count()

    return AnalyticsSummary(
        total_documents=total_documents,
        indexed_documents=indexed,
        processing_documents=processing,
        failed_documents=failed,
        total_chunks=total_chunks,
        total_ocr_pages=total_ocr_pages,
        total_queries=len(query_logs),
        total_entities=total_entities,
        uploads_by_day=_daily_counts([d.created_at for d in documents]),
        queries_by_day=_daily_counts([q.created_at for q in query_logs]),
        documents_by_type=documents_by_type,
    )
