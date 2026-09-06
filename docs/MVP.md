# MVP — DevDocs AI (Version 1)

This document defines what belongs in Version 1 and what is explicitly out of scope. It is the scope contract for the first shippable product.

---

## Problem statement

Developers joining an unfamiliar codebase often spend significant time searching through source files and documentation to understand how the system works. DevDocs AI aims to reduce this time by allowing developers to ask natural-language questions about a repository and receive answers grounded in the actual source code.

---

## Target users

### Primary user

Software developers working with unfamiliar or large codebases.

### Potential use cases

- New developer onboarding
- Understanding legacy code
- Finding implementation details
- Understanding API flows
- Locating authentication logic
- Understanding dependencies between components
- Generating documentation

---

## MVP features (Version 1)

### Authentication

- User registration / login
- User logout
- Protected application pages (unauthenticated users cannot access app features)

### GitHub

- Connect GitHub account
- View repositories available to the connected account
- Select a repository to index / query

### Repository processing

- Retrieve the selected repository
- Identify supported files (e.g. common source and doc extensions)
- Ignore unnecessary files (e.g. `node_modules`, build artifacts, binaries, secrets patterns)
- Process source code into an indexable form
- Split files into chunks suitable for embedding and retrieval

### AI

- Generate embeddings for code/doc chunks
- Store embeddings in a vector store
- Semantic search over stored embeddings for a user question
- Generate a RAG response grounded in retrieved chunks

### User experience

- Ask questions about the selected repository
- Display answers in the UI
- Display source citations (which files/chunks supported the answer)
- View cited source code in context

---

## Out of scope for MVP

The following are **not** part of Version 1. Documenting them here prevents scope creep.

| Deferred item | Notes |
|---------------|--------|
| AI agents | No multi-step autonomous agent loops |
| Automatic code modification | Read/query only; no write-back to the repo |
| Automatic PR creation | No generated pull requests |
| Kubernetes | No K8s deployment requirement for MVP |
| Team collaboration | Single-user experience; no shared workspaces/roles |
| Multiple LLM providers | One configured provider/path for MVP |
| Advanced analytics | No usage dashboards or deep product analytics |
| Enterprise billing | No plans, invoices, or org billing |
| Mobile application | Web application only |

---

## Success criteria for MVP

Version 1 is considered successful when a signed-in user can:

1. Connect GitHub and select a repository.
2. Wait for (or trigger) indexing of that repository.
3. Ask a natural-language question about the code.
4. Receive an answer with visible citations.
5. Open and inspect the cited source.

Anything beyond that list belongs in a later phase unless this document is explicitly revised.
