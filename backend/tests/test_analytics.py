from datetime import UTC, datetime, timedelta

from app.models.document import Document
from app.models.entity import Entity
from app.models.query_log import QueryLog
from app.services.analytics_service import get_analytics_summary


def _make_document(owner_id, status="indexed", chunk_count=3, ocr_pages=0, file_type="pdf"):
    return Document(
        owner_id=owner_id,
        filename="stored.pdf",
        original_filename="original.pdf",
        file_path="/tmp/stored.pdf",
        file_type=file_type,
        file_size_bytes=1000,
        status=status,
        chunk_count=chunk_count,
        ocr_page_count=ocr_pages,
    )


def test_empty_state_returns_zeros(db_session):
    summary = get_analytics_summary(db_session, "owner-empty")
    assert summary.total_documents == 0
    assert summary.total_chunks == 0
    assert summary.total_queries == 0
    assert len(summary.uploads_by_day) == 14


def test_counts_documents_by_status(db_session):
    db_session.add_all(
        [
            _make_document("owner-1", status="indexed"),
            _make_document("owner-1", status="indexed"),
            _make_document("owner-1", status="processing"),
            _make_document("owner-1", status="failed"),
        ]
    )
    db_session.commit()

    summary = get_analytics_summary(db_session, "owner-1")
    assert summary.total_documents == 4
    assert summary.indexed_documents == 2
    assert summary.processing_documents == 1
    assert summary.failed_documents == 1


def test_sums_chunk_and_ocr_counts(db_session):
    db_session.add_all(
        [
            _make_document("owner-2", chunk_count=5, ocr_pages=2),
            _make_document("owner-2", chunk_count=3, ocr_pages=0),
        ]
    )
    db_session.commit()

    summary = get_analytics_summary(db_session, "owner-2")
    assert summary.total_chunks == 8
    assert summary.total_ocr_pages == 2


def test_documents_by_type_breakdown(db_session):
    db_session.add_all(
        [
            _make_document("owner-3", file_type="pdf"),
            _make_document("owner-3", file_type="pdf"),
            _make_document("owner-3", file_type="txt"),
        ]
    )
    db_session.commit()

    summary = get_analytics_summary(db_session, "owner-3")
    assert summary.documents_by_type == {"pdf": 2, "txt": 1}


def test_data_scoped_to_owner(db_session):
    db_session.add_all(
        [
            _make_document("owner-a"),
            _make_document("owner-b"),
        ]
    )
    db_session.commit()

    summary_a = get_analytics_summary(db_session, "owner-a")
    assert summary_a.total_documents == 1


def test_query_log_counted(db_session):
    db_session.add(QueryLog(owner_id="owner-4", query_text="what is docbot?", result_count=3, confidence=0.8))
    db_session.commit()

    summary = get_analytics_summary(db_session, "owner-4")
    assert summary.total_queries == 1


def test_entity_count_included(db_session):
    db_session.add(Entity(owner_id="owner-5", name="DRDO", type="ORGANIZATION"))
    db_session.commit()

    summary = get_analytics_summary(db_session, "owner-5")
    assert summary.total_entities == 1


def test_uploads_older_than_lookback_excluded_from_daily_series(db_session):
    old_doc = _make_document("owner-6")
    old_doc.created_at = datetime.now(UTC) - timedelta(days=30)
    db_session.add(old_doc)
    db_session.commit()

    summary = get_analytics_summary(db_session, "owner-6")
    # Still counted in the total, just not bucketed into the 14-day series.
    assert summary.total_documents == 1
    assert sum(d.count for d in summary.uploads_by_day) == 0


def test_recent_upload_appears_in_daily_series(db_session):
    doc = _make_document("owner-7")
    db_session.add(doc)
    db_session.commit()

    summary = get_analytics_summary(db_session, "owner-7")
    assert sum(d.count for d in summary.uploads_by_day) == 1
