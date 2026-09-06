# Architecture Decisions — DevDocs AI

Record of important technical decisions and why they were made. Update this file when a choice changes or a new significant decision is locked in.

Related docs: [ARCHITECTURE.md](ARCHITECTURE.md) · [MVP.md](MVP.md)

---

## Decision: SvelteKit

**Choice:** SvelteKit

**Reason:**

You already have experience with SvelteKit and can therefore focus your learning time on the AI/backend portions of the project.

**Implications:**

- Frontend lives in a SvelteKit app (TypeScript preferred).
- UI talks to the backend over HTTP/REST rather than embedding Python in the frontend.
- Auth UX, repo selection, and later Q&A screens are owned by SvelteKit.

---

## Decision: FastAPI

**Choice:** Python + FastAPI

**Reason:**

Python has a strong ecosystem for LLM, embedding, NLP, and machine-learning applications.

FastAPI provides a lightweight framework for building the backend REST API.

**Implications:**

- All API routes, GitHub server-side integration, and (later) RAG orchestration live in FastAPI.
- OpenAPI docs come largely “for free,” which helps frontend integration.
- Background or pipeline work can stay in the same language as the ML libraries.

---

## Decision: PostgreSQL

**Choice:** PostgreSQL

**Reason:**

PostgreSQL provides relational data storage and can later support vector search through pgvector.

This allows the project to use one primary database instead of introducing a separate vector database initially.

**Implications:**

- Users, sessions, GitHub link metadata, and repository records use relational tables first.
- Embeddings and similarity search are planned via pgvector in a later phase—not Week 1.
- Avoids operating Redis/Pinecone/Weaviate solely for MVP vector storage.

---

## Decision: Docker

**Choice:** Docker Compose

**Reason:**

Provides a consistent development environment for the frontend, backend, and database.

**Implications:**

- Local `docker compose up` (or equivalent) brings up SvelteKit, FastAPI, and PostgreSQL together.
- Reduces “works on my machine” drift for DB versions and connection settings.
- Production deployment details (e.g. Kubernetes) remain explicitly out of MVP scope; Compose is for reliable local/dev parity.

---

## Decision: Separated frontend and backend

**Choice:** SvelteKit (UI) + FastAPI (API), not a single monolith UI framework with embedded API-only routes as the system of record

**Reason:**

Keeps clear boundaries: UI concerns in SvelteKit, domain/API/AI concerns in Python. Matches the learning goals (deepen AI/backend skills while using a familiar frontend).

**Implications:**

- CORS, auth cookies/tokens, and API versioning must be designed deliberately.
- Frontend never talks to the database directly.

---

## Decision: Session cookies (not JWT)

**Choice:** Opaque server-side sessions stored in PostgreSQL, delivered via an `HttpOnly` cookie (`devdocs_session`)

**Reason:**

Day 6 already introduced a `sessions` table (`token_hash`, `expires_at`, `revoked_at`). Cookie sessions reuse that model directly, support immediate logout/revocation, and avoid JWT refresh/secret-rotation complexity for the MVP.

**Implications:**

- Passwords are hashed with bcrypt; only a SHA-256 hash of the session token is stored.
- `POST /auth/login` sets the cookie; `POST /auth/logout` revokes the row and clears the cookie.
- Protected routes (e.g. `GET /auth/me`) require a valid, non-revoked, non-expired session.
- CORS must allow credentials when the SvelteKit frontend talks to FastAPI.
- JWT remains an option later if we need mobile/third-party API clients without cookies.

---

## Decision: Defer the AI pipeline past Week 1

**Choice:** Design the full ingestion → embed → retrieve → LLM flow in architecture docs; implement only the non-AI skeleton in Week 1

**Reason:**

Prevents scope creep and lets auth, GitHub integration, and data modeling stabilize before adding embeddings and LLM cost/complexity.

**Implications:**

- See [ARCHITECTURE.md](ARCHITECTURE.md) for the target pipeline.
- Week 1 success does not require working RAG answers.
- pgvector and LLM provider wiring land in a later milestone.

---

## How to add a new decision

When locking a new choice, append a section with:

1. **Decision** — short title  
2. **Choice** — what you picked  
3. **Reason** — why (trade-offs welcome)  
4. **Implications** — what this forces on the codebase  

Prefer updating this file over scattering rationale only in chat or commit messages.
