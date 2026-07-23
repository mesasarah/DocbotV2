# DOCBOT 2.0 — Offline Intelligent Document Assistant

An offline, privacy-first RAG assistant. Upload documents, ask questions,
get answers grounded only in what you uploaded — no internet required after
setup, no data leaves the machine.

Developed by Mesa Sarah Vasantha Zephyr and Rampalli Prajna Paramita.
Inspired by an internship project at DRDO's Advanced Systems Laboratory,
Hyderabad.

## Quick start (Docker — recommended)

Requires [Docker](https://docs.docker.com/get-docker/) and Docker Compose.

```bash
./scripts/setup.sh                    # creates backend/.env from the example
docker-compose up --build -d          # builds and starts backend, frontend, ollama
./scripts/pull-model.sh               # pulls llama3 into the ollama container
```

Open **http://localhost** — you'll land on the homepage explaining what
DOCBOT does. Click "Get started" to create an account and start uploading
documents.

Useful scripts:
```bash
./scripts/logs.sh              # tail logs from all containers
./scripts/pull-model.sh mistral # pull a different model
./scripts/reset.sh             # wipe all data for a clean slate
```

## Deploying to your own domain

See [DEPLOYMENT.md](./DEPLOYMENT.md) for running DOCBOT on a real server
with a domain and automatic HTTPS (via Caddy). Read the RAM/CPU note at the
top first — this stack runs its own LLM, which has real hardware
requirements beyond a typical cheap website host.

## Architecture

```
                    ┌─────────────┐
   browser  ──────▶ │   nginx     │  (frontend container, port 80)
                    │  + React SPA │
                    └──────┬──────┘
                           │ /api/* reverse-proxied
                           ▼
                    ┌─────────────┐        ┌──────────────┐
                    │   FastAPI    │ ─────▶ │    Ollama     │
                    │   backend    │        │  (local LLM)  │
                    └──────┬──────┘        └──────────────┘
                           │
                 ┌─────────┴──────────┐
                 ▼                    ▼
            SQLite (users,       ChromaDB
         documents, chats)    (embeddings)
```

Everything runs in Docker on your own machine (or an air-gapped server).
The only network calls the backend makes are to the `ollama` container on
the same Docker network — nothing external.

## Manual setup (without Docker)

See `backend/README.md` and `frontend/README.md` for running each service
directly with Python/Node during development.

## What's built so far

- **Layer 1 — Backend**: JWT auth, document ingestion pipeline (extract →
  chunk → embed → ChromaDB), RAG chat via local Ollama, 15 passing tests.
- **Layer 2 — Frontend**: React + TypeScript, full auth flow, document
  manager with live status, chat UI with citations, dashboard, settings.
- **Layer 3 — Docker & CI/CD**: multi-stage Dockerfiles for both services,
  nginx reverse proxy + static file serving, docker-compose with health
  checks and persistent volumes, GitHub Actions CI.
- **Layer 4 — Intelligence features**: OCR for scanned PDFs (automatic
  per-page fallback via Tesseract), a knowledge graph (LLM-based
  entity/relation extraction with an interactive SVG visualization),
  document summarization and quiz generation, and a real analytics
  dashboard with usage charts. 53 backend tests passing.
- **Layer 5 — Public landing page & production deployment** *(this layer)*:
  a marketing homepage explaining what DOCBOT is, with sign-in only
  required once you actually try to use the app (redirects back to where
  you were headed after signing in); a `docker-compose.prod.yml` + Caddy
  setup for deploying to a real domain with automatic HTTPS.

## Not yet built

- Admin panel, voice input/output, document translation, offline grammar
  correction, full OpenAPI documentation site, multi-document comparison UI.

## Project layout

```
docbot/
  backend/          # FastAPI app (see backend/README.md)
  frontend/          # React app (see frontend/README.md)
  scripts/           # setup, pull-model, logs, reset helpers
  .github/workflows/ # CI pipeline
  docker-compose.yml
```

## Notes on the Docker setup

- **Ollama models are not baked into the image** — that would make it
  multi-gigabyte and slow to build/pull. Run `./scripts/pull-model.sh`
  once after startup instead; the model persists in a named volume across
  restarts.
- **nginx proxies `/api/*` to the backend** on the same origin, so the
  browser never makes a cross-origin request in production — no CORS
  headaches, no exposed backend port needed beyond container-to-container.
- **All state is in named volumes** (`backend_data`, `backend_uploads`,
  `backend_logs`, `ollama_models`) — `docker-compose down` (without `-v`)
  preserves everything; `./scripts/reset.sh` deliberately wipes it.
- **Health checks gate startup order**: frontend won't report healthy until
  the backend does, and the backend waits on Ollama — `depends_on` uses
  `condition: service_healthy`, not just "container started."
