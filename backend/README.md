# DOCBOT 2.0 — Backend (Layer 1: Core)

Offline, privacy-first document intelligence assistant. This is the backend
core: auth, document ingestion pipeline, and RAG chat — fully working and
tested. Frontend, OCR, knowledge graph, analytics, Docker/CI layers come next.

## What's implemented in this layer

- **Auth**: register/login/refresh with JWT, bcrypt password hashing, first
  registered user auto-promoted to admin, role-based `require_admin` dependency.
- **Document pipeline**: upload (PDF/DOCX/TXT/MD) → extract text → chunk →
  embed (sentence-transformers) → store in ChromaDB, all as a background task
  with live status (`pending` → `processing` → `indexed`/`failed`).
- **OCR for scanned PDFs**: each PDF page is checked for extractable text;
  pages with little/none are automatically rasterized and read via
  Tesseract. `ocr_page_count` on each document tracks how many pages needed
  it. Manual re-run with forced OCR is available via
  `POST /documents/{id}/retry?force_ocr=true`.
- **RAG chat**: semantic search over your own documents → context-grounded
  answer from a local Ollama model → citations with filename/page/score.
  Each successful query is logged for analytics.
- **Knowledge graph**: `POST /knowledge-graph/documents/{id}/extract` asks
  the local LLM to pull entities (people/orgs/locations/tech/dates) and
  relations out of a document's indexed text, deduping entities per user by
  name+type. `GET /knowledge-graph` returns the full graph (optionally
  scoped to one document) as nodes/edges.
- **Summarization & quiz generation**: `POST /documents/{id}/summarize`
  (executive summary, bullet points, key insights) and
  `POST /documents/{id}/quiz` (multiple-choice questions with explanations),
  both LLM-based with defensive JSON parsing — a malformed model response
  is caught and surfaced as a clean error, never a crash.
- **Analytics**: `GET /analytics/summary` aggregates document counts by
  status/type, chunk and OCR totals, entity counts, and 14-day daily series
  for uploads and queries.
- **Multi-tenant isolation**: each user gets their own ChromaDB collection;
  documents, chats, entities, and query logs are all scoped by `owner_id`.
- **Tests**: 53 passing pytest tests covering auth, document isolation,
  validation, the ingestion pipeline, OCR trigger logic, knowledge graph
  parsing/dedup, AI feature response validation, and analytics aggregation.

## Prerequisites

- Python 3.12
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for scanned
  PDF support (`apt install tesseract-ocr` / `brew install tesseract`).
  Without it, scanned pages are indexed with empty text and a warning is
  logged — everything else still works.
- [Ollama](https://ollama.com) running locally, with a model pulled:
  ```bash
  ollama pull llama3
  ```

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env            # then edit SECRET_KEY for anything beyond local testing
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Run tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Quick smoke test (curl)

```bash
# Register (first user becomes admin)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","full_name":"You","password":"password123"}'

# Use the access_token from the response below
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/some.pdf"

curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is this document about?"}'
```

## Project layout

```
backend/
  app/
    api/          # FastAPI routers (auth, documents, chat, knowledge_graph, ai_features, analytics, health)
    core/         # config, security, logging
    db/           # SQLAlchemy engine/session
    models/       # SQLAlchemy ORM models (User, Document, ChatSession, ChatMessage, Entity, QueryLog)
    schemas/       # Pydantic request/response schemas
    services/      # extraction, OCR, chunking, embeddings/vector store, LLM client, pipeline,
                    # knowledge graph extraction, AI features (summary/quiz), analytics
    utils/         # file validation helpers
  tests/           # pytest suite (53 tests)
  requirements.txt
  .env.example
```

## Notes on the RAG design

- Retrieval is per-user: each user's ChromaDB collection (`docbot_user_<id>`)
  keeps documents private without extra filtering overhead.
- The LLM system prompt instructs the model to answer **only** from the
  retrieved context and to say so explicitly when the documents don't contain
  the answer — this is what keeps DOCBOT from hallucinating like a general
  chatbot.
- `confidence` in the chat response is the mean cosine similarity of the
  retrieved chunks — a rough signal, not a calibrated probability.
- Summarization, quiz generation, and knowledge graph extraction all reuse
  the already-indexed chunk text from ChromaDB (via `get_document_full_text`)
  rather than re-parsing the original file — faster, and avoids re-running
  OCR on every request.

## Next layers (not yet built)

1. Admin panel, full OpenAPI documentation site
2. Voice input/output, document translation, offline grammar correction
3. Multi-document cross-referencing in chat (currently scoped per query via
   `document_ids`, but no dedicated "compare documents" UI yet)
