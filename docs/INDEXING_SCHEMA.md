# Indexing schema — DevDocs AI

Schema + fetch path for repository ingestion.

## Tables

```text
users
  └── selected_repositories          # one selected GitHub repo per user (Day 14)
        ├── index_jobs               # ingestion/index run status
        └── repository_files         # discovered source/doc files
              └── code_chunks        # line-window text + optional embedding (pgvector)
```

| Table | Purpose |
|-------|---------|
| `selected_repositories` | User’s chosen repo metadata |
| `index_jobs` | Job lifecycle: `pending` → `running` → `ready` / `failed` |
| `repository_files` | File path + sha/language/size under a selected repo |
| `code_chunks` | Chunk text + inclusive start/end lines + nullable `embedding vector(1536)` |

## Fetch + chunk (Days 16–18)

`POST /github/selected-repo/fetch` (session cookie required):

1. Resolves the selected repo’s default branch → commit SHA
2. Lists blobs via GitHub **Trees** API (`recursive=1`)
3. Filters noise (`node_modules`, build dirs, binaries, secrets, large files) — see [FILE_FILTERS.md](FILE_FILTERS.md)
4. Loads each blob via **Blobs** API
5. Replaces prior `repository_files` / chunks for that selection
6. Splits each file into overlapping line windows and stores `code_chunks` — see [CHUNKING.md](CHUNKING.md)

Caps: 150 files, 200KB per file (see [FILE_FILTERS.md](FILE_FILTERS.md)). Chunk windows: 40 lines / 5-line overlap.

## pgvector (Day 19)

Compose image: `pgvector/pgvector:pg16`. Migration `0005_pgvector` enables the extension and adds `code_chunks.embedding`. See [PGVECTOR.md](PGVECTOR.md).

## Embeddings (Day 20)

`POST /github/selected-repo/embed` fills nullable embeddings via an OpenAI-compatible client. See [EMBEDDINGS.md](EMBEDDINGS.md).

## Index job (Day 21)

`POST /github/selected-repo/index` runs fetch → chunk → embed synchronously and ends in `ready` / `failed`. See [INDEX_JOBS.md](INDEX_JOBS.md).

## Retrieval (Day 23)

`POST /github/selected-repo/retrieve` embeds a question and returns the top-k chunks. See [RETRIEVAL.md](RETRIEVAL.md).

## Ask (Day 24)

`POST /ask` retrieves chunks, prompts the chat model, and returns the answer plus citations (`path`, `chunk_id`). See [ASK.md](ASK.md).

## Apply

```bash
docker compose up -d db
cd backend
alembic upgrade head
```

## Next

- Q&A UI that shows the answer and citations
