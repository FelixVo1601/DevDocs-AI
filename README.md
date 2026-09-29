# DevDocs AI

**MVP v1** (git tag `mvp-v1`). Frozen: log in, connect GitHub, select a repository, index it, ask, see citations, and open the cited source. Later ideas are in [docs/BACKLOG.md](docs/BACKLOG.md) and are not part of this version.

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
| **Repository processing** | Retrieve the selected repo (GitHub Trees and Blobs); filter files; chunk source |
| **AI / RAG** | Embeddings, vector storage, semantic search, grounded answers |
| **Experience** | Ask questions; view answers with source citations and cited code |

See [docs/MVP.md](docs/MVP.md) for the frozen Version 1 scope. Post-MVP ideas are in [docs/BACKLOG.md](docs/BACKLOG.md) and are out of scope.

## Technology stack

| Layer | Choice | Role |
|-------|--------|------|
| Frontend | SvelteKit | Auth UI, repo selection, Q&A experience |
| Backend / API | Python + FastAPI | Auth, GitHub integration, indexing orchestration, RAG endpoints |
| Database | PostgreSQL + pgvector | Users, sessions, repository metadata, chunk embeddings |
| Vector store | pgvector (same DB) | `code_chunks.embedding vector(1536)` |
| Auth | App auth + GitHub OAuth | Login and GitHub access |
| LLM / embeddings | OpenAI-compatible API | Embeddings (`text-embedding-3-small`, 1536 dimensions) and answers (`gpt-4o-mini`) |
| Source control API | GitHub API | List repos, fetch repository content |
| Local database | Docker Compose | PostgreSQL 16 with pgvector. The API and UI run on the host, not in Compose |

See [docs/DECISIONS.md](docs/DECISIONS.md) for why these were chosen. Library versions are pinned in `frontend/package.json` and `backend/requirements.txt`.

## High-level architecture

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

Ingestion, embeddings, retrieval, and the ask path are described in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

**Happy path:**

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
├── docs/              # MVP, architecture, env, and the smoke checklist
├── scripts/           # One-command local start (dev.ps1 / dev.sh)
├── docker-compose.yml # PostgreSQL
├── .env.example       # Root env template
└── README.md
```

## Local setup

### Prerequisites

- Docker Desktop (Postgres only)
- Node.js 20+ and npm
- Python 3.11+

### 1. Environment

From the repo root:

```bash
cp .env.example .env                    # Windows: copy .env.example .env
cp frontend/.env.example frontend/.env
```

The API reads `.env` from `backend/` or the repo root. The browser reads `frontend/.env`. Never commit either file.

Set these in the **root** `.env` before connecting GitHub or indexing. Restart the API after any edit (`get_settings()` is cached until the process restarts).

| Variable | Required for | Local value |
|----------|----------------|-------------|
| `DATABASE_URL` | API and migrations | `postgresql://devdocs:change_me@localhost:5432/devdocs` (already in the example; must match Compose) |
| `SECRET_KEY` | GitHub token encryption and OAuth state | A long random string. Empty is rejected |
| `GITHUB_CLIENT_ID` | **Connect GitHub** | From a GitHub OAuth App |
| `GITHUB_CLIENT_SECRET` | **Connect GitHub** | Same app. Never log or commit it |
| `GITHUB_REDIRECT_URI` | OAuth callback | `http://localhost:8001/auth/github/callback` (must match the OAuth App) |
| `OPENAI_API_KEY` | Index embeddings and **Ask** | OpenAI-compatible bearer token |
| `OPENAI_BASE_URL` | Embeddings and chat | `https://api.openai.com/v1` unless you use another compatible host |
| `EMBEDDING_MODEL` | Index | `text-embedding-3-small` (vectors are 1536-wide) |
| `CHAT_MODEL` | Ask | `gpt-4o-mini` |
| `PUBLIC_API_URL` | Browser, in `frontend/.env` | `http://localhost:8001` |
| `FRONTEND_URL` | CORS and OAuth return | `http://localhost:5173` |
| `COOKIE_SECURE` | Session cookie | `false` on local HTTP |

OAuth App homepage `http://localhost:5173`, callback `http://localhost:8001/auth/github/callback`. Steps: [docs/GITHUB_OAUTH.md](docs/GITHUB_OAUTH.md). Every variable: [docs/ENV.md](docs/ENV.md).

`scripts/dev.ps1` and `scripts/dev.sh` copy the example env files only when they are missing. Fill the secrets before the first start, or edit `.env` and restart the API.

### 2. Start

**Windows (PowerShell), from the repo root:**

```powershell
.\scripts\dev.ps1
```

**macOS / Linux:**

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

That starts Postgres (`pgvector/pgvector:pg16`, container `devdocs-db`), creates `backend/.venv` if needed, installs API dependencies, runs `alembic upgrade head`, then starts:

| Process | Address |
|---------|---------|
| API | http://127.0.0.1:8001 (`uvicorn app.main:app --reload`) |
| UI | http://localhost:5173 |

**Manual equivalent:**

```bash
docker compose up -d db
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

```bash
cd frontend
npm install
npm run dev -- --host localhost --port 5173
```

Port 8000 is often unavailable on Windows; the app uses **8001**.

### 3. Confirm the stack

```bash
python scripts/smoke.py
```

Expect `smoke ok`. That covers health, Postgres, register/login/logout, and the “not connected” / “no repository” API errors. It does not index a repo. The matching checklist is [docs/SMOKE.md](docs/SMOKE.md).

- Health: http://localhost:8001/health → `{"status":"ok"}`
- DB: http://localhost:8001/db/ping → `{"database":"ok"}`
- API docs: http://localhost:8001/docs

Open the UI at **http://localhost:5173** (not `127.0.0.1`). The session cookie is `devdocs_session` (HttpOnly). In development, CORS allows `http://localhost:<port>` and `http://127.0.0.1:<port>` with credentials.

### Demo walkthrough

1. Register at http://localhost:5173/register (password at least 8 characters). You land on `/app`.
2. **Repositories** shows **Not connected** and **Connect GitHub**. **Ask** says **GitHub is not connected** and has no question box.
3. Connect GitHub and authorize. `/app` shows **GitHub connected successfully.** and **Connected as** your login.
4. Select a small repository you can access (at most 150 files are indexed; files over 200 KB are skipped).
5. **Index repository**. Wait on that request. Status goes **running**, then **ready** (“This repository is indexed and ready to search.”). **Ask a question** appears.
6. On **Ask**, the form says the index status is ready. Ask something about that repo. **Answer** and **Sources** appear (`[n] path`, line range, chunk id).
7. Click a source or an `[n]` marker. **Source preview** shows that chunk, read-only.
8. **Log out**. `/app` sends you back to login.

If indexing fails, the panel shows status **failed** and the error. Ask stays closed until status is **ready**.

Backend tests (Postgres must be up; DB tests skip when it is not):

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Development roadmap

| Phase | Focus |
|-------|--------|
| **Day 1** | Product requirements, GitHub repo, README, MVP definition |
| **Day 2** | Architecture docs, monorepo layout, env template |
| **Days 3–9** | Frontend/backend scaffold, Postgres, auth API + UI, protected `/app` |
| **Day 10** | CORS, env docs, local DX scripts |
| **Day 11** | GitHub OAuth backend (encrypted token storage) |
| **Day 12** | GitHub connect UI |
| **Day 13** | List repositories API |
| **Day 14** | Select repository (API + UI) — Week 2 skeleton complete |
| **Day 15** | Indexing schema: jobs, files, chunks (vectors later) |
| **Day 16** | Fetch selected-repo file list + content (GitHub Trees/Blobs) |
| **Day 17** | File filter rules (documented + unit-tested) |
| **Day 18** | Chunking with path + start/end line metadata |
| **Day 19** | pgvector Compose image + embedding column |
| **Day 20** | OpenAI-compatible embeddings for selected-repo chunks |
| **Day 21** | Index job trigger + status (`ready` / `failed`) |
| **Day 22** | Index status UI (button, status, errors) |
| **Day 23** | Semantic retrieval (embed question → top-k chunks) |
| **Day 24** | RAG `POST /ask` with path + chunk id citations |
| **Day 25** | Ask UI: question input and answer text |
| **Day 26** | Citations UI: cited files under the answer |
| **Day 27** | Cited source preview (read-only chunk panel) |
| **Day 28** | Happy-path polish: empty, loading, and basic error states |
| **Day 29** | Local setup, demo walkthrough, and smoke checklist |
| **Day 30** | MVP v1 freeze (`mvp-v1`); post-MVP ideas in `docs/BACKLOG.md` |

## Repository

- **GitHub:** [https://github.com/FelixVo1601/DevDocs-AI](https://github.com/FelixVo1601/DevDocs-AI)
- **Suggested / project name:** `devdocs-ai` (repository: `DevDocs-AI`)

## License

See [LICENSE](LICENSE).
