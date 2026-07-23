"""
Shared test fixtures.

Uses FastAPI's dependency_overrides for get_db rather than reloading
modules with importlib -- reloading app.db.session creates a *new* Base
class each time, which desyncs from model classes already cached in
sys.modules (imported by other test files), silently leaving the real
Base.metadata empty and every table missing. Dependency overrides avoid
that whole class of bug and are the standard FastAPI testing pattern.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db

# Import every model module once so they're all registered on Base.metadata
# regardless of which test file happens to run first.
from app.models import chat as _chat  # noqa: F401
from app.models import document as _document  # noqa: F401
from app.models import entity as _entity  # noqa: F401
from app.models import query_log as _query_log  # noqa: F401
from app.models import user as _user  # noqa: F401


def _make_test_engine():
    # StaticPool keeps a single underlying connection alive for the whole
    # engine, which is required for SQLite ":memory:" -- otherwise each
    # checkout gets its own throwaway in-memory database.
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """
    Spins up the app against a throwaway in-memory DB and per-test upload/
    chroma dirs, so tests never touch real dev data and don't leak state
    between runs.
    """
    upload_dir = tmp_path / "uploads"
    chroma_dir = tmp_path / "chroma"
    upload_dir.mkdir()
    chroma_dir.mkdir()

    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(chroma_dir))
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    from app.core.config import get_settings

    get_settings.cache_clear()

    # The vector store caches its embedding model / chroma client with
    # lru_cache -- clear those too so each test gets a client pointed at
    # its own chroma_dir instead of silently reusing a previous test's.
    from app.services.vector_store import get_chroma_client, get_embedding_model

    get_chroma_client.cache_clear()
    get_embedding_model.cache_clear()

    engine = _make_test_engine()
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    get_chroma_client.cache_clear()
    get_embedding_model.cache_clear()


@pytest.fixture()
def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "full_name": "Test User", "password": "password123"},
    )
    resp = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def db_session():
    """A bare in-memory SQLite session with all tables created, for testing
    service-layer functions directly without going through the HTTP app."""
    engine = _make_test_engine()
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
