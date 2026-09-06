# System Architecture — DevDocs AI

This document describes how the major components communicate. It is the design reference for Day 2 onward.

Week 1 focuses on the application skeleton (frontend, backend, database, GitHub integration). The full AI ingestion pipeline is designed here but **not implemented** during Week 1.

Related docs: [MVP.md](MVP.md) · [DECISIONS.md](DECISIONS.md)

---

## Initial architecture (Week 1)

Major components and how they talk to each other:

```text
                    ┌───────────────┐
                    │    GitHub     │
                    └───────┬───────┘
                            │
                            │
┌──────────────┐            │
│              │            │
│  SvelteKit   │◄───────────┤
│   Frontend   │            │
│              │            │
└──────┬───────┘            │
       │                     │
       │ HTTP/REST           │
       ▼                     ▼
┌─────────────────────────────────┐
│            FastAPI              │
│            Backend              │
└──────────────┬──────────────────┘
               │
               ▼
       ┌───────────────┐
       │  PostgreSQL   │
       └───────────────┘
```

### Component responsibilities

| Component | Responsibility |
|-----------|----------------|
| **SvelteKit frontend** | UI for auth, GitHub connection, repository selection, and (later) Q&A. Talks to FastAPI over HTTP/REST. May also participate in OAuth redirects involving GitHub. |
| **FastAPI backend** | REST API: authentication, GitHub OAuth/token handling, repository metadata, protected routes. Orchestrates data access to PostgreSQL. Later owns ingestion and RAG endpoints. |
| **GitHub** | Source of repositories and (via OAuth) identity/authorization for accessing private/public repos the user can see. |
| **PostgreSQL** | Relational storage for users, sessions, linked GitHub accounts, and selected repositories. Later also stores embeddings via pgvector. |

### Communication patterns (Week 1)

1. **Browser → SvelteKit** — User interacts with the web app.
2. **SvelteKit → FastAPI** — JSON over HTTP/REST for login, session checks, listing/selecting repos, etc.
3. **FastAPI → GitHub API** — OAuth and repository listing/fetch (using the user’s GitHub credentials/token).
4. **FastAPI → PostgreSQL** — Persist and read application data.
5. **SvelteKit ↔ GitHub** — OAuth redirect flow as needed (authorization code returned through the app, exchanged/stored via the backend).

---

## Target architecture (post–Week 1 AI pipeline)

After Week 1, the system expands into an ingestion and RAG pipeline. Conceptual flow:

```text
GitHub
   ↓
Repository Ingestion
   ↓
Code Processing
   ↓
Chunking
   ↓
Embeddings
   ↓
PostgreSQL + pgvector
   ↓
Retriever
   ↓
LLM
   ↓
FastAPI
   ↓
SvelteKit
```

### Pipeline stages (design only — not Week 1 work)

| Stage | What happens |
|-------|----------------|
| **Repository ingestion** | Pull repository contents from GitHub for a selected repo. |
| **Code processing** | Identify supported files; ignore noise (`node_modules`, build artifacts, binaries, etc.). |
| **Chunking** | Split source into retrieval-sized chunks with path/metadata. |
| **Embeddings** | Generate vector embeddings for each chunk. |
| **PostgreSQL + pgvector** | Store chunks, metadata, and vectors in one primary database. |
| **Retriever** | Semantic search: embed the user question, find nearest chunks. |
| **LLM** | Generate an answer grounded in retrieved chunks, with citations. |
| **FastAPI** | Expose ask/answer APIs; return answer + citation metadata. |
| **SvelteKit** | Display the question UI, answer, citations, and cited source. |

### Expanded component diagram

```text
┌──────────────┐     HTTP/REST      ┌──────────────────────────────────────┐
│  SvelteKit   │◄──────────────────▶│              FastAPI                 │
│  Frontend    │                    │  auth · repos · ask · (later jobs)   │
└──────────────┘                    └───────┬───────────────┬──────────────┘
                                            │               │
                         ┌──────────────────┘               └──────────────────┐
                         ▼                                                     ▼
                ┌─────────────────┐                                  ┌─────────────────┐
                │   PostgreSQL    │                                  │     GitHub      │
                │   + pgvector    │                                  │   (repos/API)   │
                └────────▲────────┘                                  └────────┬────────┘
                         │                                                     │
                         │              ┌──────────────────────┐               │
                         │              │  Ingestion pipeline  │◄──────────────┘
                         │              │  process → chunk →   │
                         └──────────────│  embed → store       │
                                        └──────────────────────┘
                                                   │
                                        ┌──────────┴──────────┐
                                        ▼                     ▼
                                 ┌────────────┐        ┌────────────┐
                                 │ Embedding  │        │    LLM     │
                                 │   model    │        │ (RAG gen)  │
                                 └────────────┘        └────────────┘
```

---

## Request flows

### Week 1 — connect GitHub and select a repository

```text
User → SvelteKit → FastAPI → GitHub API
                      │
                      ▼
                 PostgreSQL
                 (user, token metadata, selected repo)
```

### Later — ask a question (RAG)

```text
User question
   → SvelteKit
   → FastAPI
   → Retriever (embed query → pgvector similarity search)
   → LLM (prompt + retrieved chunks)
   → FastAPI (answer + citations)
   → SvelteKit (render answer and source)
```

---

## Local development topology

Intended local layout (see also Docker decision in [DECISIONS.md](DECISIONS.md)):

| Service | Typical role |
|---------|----------------|
| `frontend` | SvelteKit app (dev server) |
| `backend` | FastAPI (Uvicorn) |
| `db` | PostgreSQL (later with pgvector) |

Docker Compose keeps frontend, backend, and database aligned across machines without requiring each developer to install every dependency globally.

---

## Week 1 boundary

**In scope for Week 1 architecture implementation:**

- SvelteKit frontend shell
- FastAPI backend shell and REST conventions
- PostgreSQL connectivity
- Auth and protected routes (as per MVP)
- GitHub connect / list / select repository paths

**Out of scope for Week 1 (designed above, built later):**

- Repository ingestion workers
- Chunking, embeddings, pgvector queries
- Retriever + LLM RAG answers
- Citation UI backed by real retrieval

Do not implement the AI pipeline during Week 1.
