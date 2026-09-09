# DevDocs AI

AI-powered developer knowledge and documentation assistant.

Developers ask natural-language questions about a GitHub repository and receive answers grounded in the actual source code, with citations back to the files that support each answer.

---

## Problem

Developers joining an unfamiliar codebase often spend significant time searching through source files and documentation to understand how the system works. Existing tools (IDE search, READMEs, tribal knowledge) do not scale well for large or poorly documented repositories. Onboarding, legacy maintenance, and cross-team collaboration all suffer from the same gap: there is no reliable way to ask “how does this work?” and get an answer tied to the real code.

## Proposed solution

DevDocs AI connects to a developer’s GitHub account, indexes a selected repository, and uses retrieval-augmented generation (RAG) so answers are based on that repository’s source—not generic model knowledge. Users ask questions in plain language, see cited file references, and can open the cited source directly.

## Target users

**Primary user:** Software developers working with unfamiliar or large codebases.

**Use cases:**

- New developer onboarding
- Understanding legacy code
- Finding implementation details
- Understanding API flows
- Locating authentication logic
- Understanding dependencies between components
- Generating documentation from existing code

## Core features (MVP)

| Area | Capability |
|------|------------|
| **Authentication** | Register, log in, log out; protected application pages |
| **GitHub** | Connect GitHub account; list and select repositories |
| **Repository processing** | Clone/retrieve repo; filter supported files; chunk source for indexing |
| **AI / RAG** | Embeddings, vector storage, semantic search, grounded answers |
| **Experience** | Ask questions; view answers with source citations and cited code |

See [docs/MVP.md](docs/MVP.md) for the full Version 1 scope and explicit out-of-scope items.

## Technology stack

| Layer | Choice | Role |
|-------|--------|------|
| Frontend | SvelteKit | Auth UI, repo selection, Q&A experience |
| Backend / API | Python + FastAPI | Auth, GitHub integration, indexing orchestration, RAG endpoints |
| Database | PostgreSQL | Users, sessions, repository metadata |
| Vector store | pgvector (later) | Embedding storage and similarity search |
| Auth | App auth + GitHub OAuth | Login and GitHub access |
| LLM / embeddings | OpenAI-compatible API (configurable; post–Week 1) | Embeddings and answer generation |
| Source control API | GitHub API | List repos, fetch repository content |
| Local env | Docker Compose | Consistent frontend, backend, and database |

See [docs/DECISIONS.md](docs/DECISIONS.md) for why these were chosen. Exact library versions will be locked in as implementation begins.

## High-level architecture

Week 1 skeleton (AI pipeline not implemented yet):

```text
                    ┌───────────────┐
                    │    GitHub     │
                    └───────┬───────┘
┌──────────────┐            │
│  SvelteKit   │◄───────────┤
│   Frontend   │            │
└──────┬───────┘            │
       │ HTTP/REST          │
       ▼                    ▼
┌─────────────────────────────────┐
│            FastAPI              │
└──────────────┬──────────────────┘
               ▼
       ┌───────────────┐
       │  PostgreSQL   │
       └───────────────┘
```

Full design (including the later ingestion → embed → retrieve → LLM path) is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

**Happy path (target product):**

1. User registers/logs in and connects GitHub.
2. User selects a repository; the app retrieves and filters source files.
3. Files are chunked; embeddings are generated and stored.
4. User asks a question; semantic search retrieves relevant chunks.
5. The LLM generates an answer grounded in those chunks, with citations.
6. User inspects cited source in the UI.

## Repository layout

```text
DevDocs-AI/
├── frontend/          # SvelteKit + TypeScript
├── backend/           # FastAPI
├── docs/              # MVP, architecture, decisions, ENV
├── scripts/           # One-command local start (dev.ps1 / dev.sh)
├── docker-compose.yml # PostgreSQL
├── .env.example       # Root env template
└── README.md
```

## How to run (auth end-to-end)

### Prerequisites

- Docker Desktop (for Postgres)
- Node.js 20+ and npm
- Python 3.11+

### Option A — one command

**Windows (PowerShell), from the repo root:**

```powershell
.\scripts\dev.ps1
```

**macOS / Linux:**

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

This copies missing env files, starts Postgres, migrates the DB, then opens API + UI terminals/processes.

### Option B — manual

```bash
# 1) Env
cp .env.example .env                    # Windows: copy .env.example .env
cp frontend/.env.example frontend/.env

# 2) Database
docker compose up -d db

# 3) Backend
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

# 4) Frontend (new terminal)
cd frontend
npm install
npm run dev -- --host localhost --port 5173
```

### Verify auth (no CORS hacks)

1. Open **http://localhost:5173** (use `localhost`, not `127.0.0.1`, so the session cookie matches `PUBLIC_API_URL`).
2. Register at `/register`, then open `/app` (protected).
3. Refresh — you should stay signed in.
4. Log out — `/app` should send you back to login.

API docs: http://localhost:8001/docs · Health: http://localhost:8001/health

CORS is configured on the API (`CORS_ORIGINS` + development localhost regex) with `allow_credentials=True`. Full variable reference: [docs/ENV.md](docs/ENV.md).

## Development roadmap

| Phase | Focus |
|-------|--------|
| **Day 1** | Product requirements, GitHub repo, README, MVP definition |
| **Day 2** | Architecture docs, monorepo layout, env template |
| **Days 3–9** | Frontend/backend scaffold, Postgres, auth API + UI, protected `/app` |
| **Day 10** | CORS, env docs, local DX scripts |
| **Next** | GitHub OAuth, repository listing and selection |
| **Next** | Ingestion pipeline (fetch → filter → chunk → embed → store) |
| **Next** | Q&A UI, RAG endpoint, citations and source preview |
| **Later (post-MVP)** | Agents, auto PRs, multi-provider LLMs, teams, analytics, billing, mobile |

## Repository

- **GitHub:** [https://github.com/FelixVo1601/DevDocs-AI](https://github.com/FelixVo1601/DevDocs-AI)
- **Suggested / project name:** `devdocs-ai` (repository: `DevDocs-AI`)

## License

See [LICENSE](LICENSE).
