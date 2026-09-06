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
├── frontend/          # SvelteKit + TypeScript (npm run dev)
├── backend/           # FastAPI (uvicorn; /health, /db/ping)
├── docs/              # MVP, architecture, decisions
├── docker-compose.yml # PostgreSQL for local development
├── .env.example       # Env template (copy to .env; never commit .env)
├── .gitignore
└── README.md
```

## How to run

1. **Clone and enter the repo**
2. **Copy env template:** `copy .env.example .env` (Windows) or `cp .env.example .env`, then adjust secrets if needed
3. **Database:**

```bash
docker compose up -d db
```

4. **Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` — you should see **DevDocs AI**.

5. **Backend:**

```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

- Health: http://127.0.0.1:8001/health → `{"status":"ok"}`
- DB ping: http://127.0.0.1:8001/db/ping → `{"database":"ok"}`
- Schema: http://127.0.0.1:8001/db/schema → `{"users_and_sessions":true}`
- OpenAPI: http://127.0.0.1:8001/docs

Use [.env.example](.env.example) as the configuration contract. `DATABASE_URL` must match the Compose Postgres credentials.

## Development roadmap

| Phase | Focus |
|-------|--------|
| **Day 1** | Product requirements, GitHub repo, README, MVP definition |
| **Day 2** | Architecture docs, monorepo layout, env template |
| **Day 2+** | Project scaffolding, auth, database schema |
| **Next** | GitHub OAuth, repository listing and selection |
| **Next** | Ingestion pipeline (fetch → filter → chunk → embed → store) |
| **Next** | Q&A UI, RAG endpoint, citations and source preview |
| **Later (post-MVP)** | Agents, auto PRs, multi-provider LLMs, teams, analytics, billing, mobile |

## Repository

- **GitHub:** [https://github.com/FelixVo1601/DevDocs-AI](https://github.com/FelixVo1601/DevDocs-AI)
- **Suggested / project name:** `devdocs-ai` (repository: `DevDocs-AI`)

## License

See [LICENSE](LICENSE).
