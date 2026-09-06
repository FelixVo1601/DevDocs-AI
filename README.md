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
| Frontend | Next.js (React, TypeScript) | Auth UI, repo selection, Q&A experience |
| Backend / API | Next.js Route Handlers or a Node.js API | Auth, GitHub integration, indexing orchestration, RAG endpoints |
| Database | PostgreSQL | Users, sessions, repository metadata |
| Vector store | pgvector (or equivalent) | Embedding storage and similarity search |
| Auth | Session-based auth (e.g. Auth.js) + GitHub OAuth | App login and GitHub access |
| LLM / embeddings | OpenAI-compatible API (configurable) | Embeddings and answer generation |
| Source control API | GitHub API | List repos, fetch repository content |

Exact library versions will be locked in as implementation begins; this table is the intended MVP stack.

## High-level architecture

```text
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Web client │────▶│  Application API │────▶│  PostgreSQL     │
│  (Next.js)  │     │  (auth, RAG,     │     │  + pgvector     │
└─────────────┘     │   repo jobs)     │     └─────────────────┘
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌────────────┐  ┌──────────┐
        │  GitHub  │  │ Embedding  │  │   LLM    │
        │   API    │  │   model    │  │  (RAG)   │
        └──────────┘  └────────────┘  └──────────┘
```

**Flow (happy path):**

1. User registers/logs in and connects GitHub.
2. User selects a repository; the app retrieves and filters source files.
3. Files are chunked; embeddings are generated and stored.
4. User asks a question; semantic search retrieves relevant chunks.
5. The LLM generates an answer grounded in those chunks, with citations.
6. User inspects cited source in the UI.

## Development roadmap

| Phase | Focus |
|-------|--------|
| **Day 1** | Product requirements, GitHub repo, README, MVP definition |
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
