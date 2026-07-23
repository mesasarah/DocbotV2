# DOCBOT 2.0 — Frontend (Layer 2)

React 19 + TypeScript + Vite frontend for DOCBOT. Full auth flow, document
manager with live status, and RAG chat with citations — wired against the
Layer 1 backend and tested end-to-end.

## What's implemented in this layer

- **Auth**: login/register pages, JWT stored in localStorage, auto-refresh
  on 401 via axios interceptor, protected routing.
- **Documents**: drag-and-drop upload, live status polling (pending →
  processing → indexed/failed) every 2s while anything's active, retry on
  failure, delete, OCR badge showing how many pages needed OCR.
- **Chat**: session list sidebar, message thread, citations shown inline
  under each answer (filename, page, match %, snippet), loading state,
  graceful error surfacing (e.g. if Ollama isn't running).
- **Knowledge Graph**: SVG visualization of entities/relations extracted
  from a chosen document, grouped radially by entity type (person, org,
  location, technology, date), with hover-to-highlight connections and a
  color-coded legend.
- **AI features**: Summarize and Quiz buttons on each indexed document,
  opening a modal with an executive summary/bullet points/insights, or an
  interactive multiple-choice quiz with instant right/wrong feedback.
- **Dashboard**: real analytics — document/indexed/processing/entity/OCR
  counts, a 14-day uploads area chart, and a by-file-type breakdown pie
  chart (via recharts).
- **Settings**: shows active + available local Ollama models.

## Design system

Built around DOCBOT's actual premise — an offline, air-gapped document tool,
not a generic SaaS dashboard:

- **Palette**: deep graphite background, warm rose accent for primary
  actions, sage for "indexed/success," amber for "processing," muted
  crimson for errors.
- **Type**: Inter for UI chrome, JetBrains Mono for anything technical
  (file sizes, chunk counts, status badges, timestamps) — the mono/sans
  contrast signals "real tool," not marketing site.
- **Signature element**: the "Local only" pulse indicator in the header,
  present on every authenticated page — a constant, quiet reminder that
  nothing leaves the machine.

## Setup

```bash
cd frontend
npm install
cp .env.example .env    # VITE_API_URL defaults to http://localhost:8000
npm run dev
```

Requires the Layer 1 backend running (see `../backend/README.md`).

## Build

```bash
npm run build      # type-checks with tsc -b, then builds via vite
npm run preview     # serve the production build locally
```

## Project layout

```
frontend/
  src/
    api/          # axios client + typed endpoint functions
                    # (auth, documents, chat, analytics, knowledgeGraph, aiFeatures)
    components/   # Button, InputField, StatusBadge, OfflinePulse, ProtectedRoute,
                    # Modal, SummaryPanel, QuizPanel
    context/      # AuthContext (current user, login/register/logout)
    hooks/        # useAuth
    layouts/      # AppShell (sidebar + header)
    pages/        # Login, Register, Dashboard, Documents, Chat, KnowledgeGraph, Settings
    types/        # TypeScript types mirroring backend Pydantic schemas
```

## Verified working end-to-end

- Typecheck (`tsc -b`) and production build both clean, no errors.
- CORS confirmed between `localhost:5173` and backend `localhost:8000`.
- Full flow tested live against the running backend: register → JWT issued →
  upload → background pipeline indexes the doc → chat query retrieves the
  right chunk → analytics aggregation reflects real document/chunk/query
  counts → knowledge graph and AI feature endpoints fail gracefully with a
  clear message when Ollama isn't running, exactly as the UI displays it.

## Next layers (not yet built)

1. Admin panel
2. Voice input, document translation, offline grammar correction
3. Bundle size optimization (recharts pushes the main chunk over 500kB —
   worth code-splitting the Dashboard route if this becomes a real concern)
