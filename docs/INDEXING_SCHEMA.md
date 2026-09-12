# Indexing schema — DevDocs AI

Schema + fetch path for repository ingestion.

## Tables

```text
users
  └── selected_repositories          # one selected GitHub repo per user (Day 14)
        ├── index_jobs               # ingestion/index run status
        └── repository_files         # discovered source/doc files
              └── code_chunks        # text (full file on Day 16; chunked later)
```

| Table | Purpose |
|-------|---------|
| `selected_repositories` | User’s chosen repo metadata |
| `index_jobs` | Job lifecycle: `pending` → `running` → `succeeded` / `failed` |
| `repository_files` | File path + sha/language/size under a selected repo |
| `code_chunks` | Chunk text + line range; **no vector column yet** |

## Fetch contents (Day 16)

`POST /github/selected-repo/fetch` (session cookie required):

1. Resolves the selected repo’s default branch → commit SHA
2. Lists blobs via GitHub **Trees** API (`recursive=1`)
3. Filters noise (`node_modules`, build dirs, binaries, large files) and keeps common source/doc extensions
4. Loads each blob via **Blobs** API
5. Replaces prior `repository_files` / chunks for that selection
6. Stores each file as `code_chunks.chunk_index = 0` (full file) and returns paths + content

Caps: 150 files, 200KB per file (see `app/services/repo_filters.py`).

## Apply

```bash
docker compose up -d db
cd backend
alembic upgrade head
```

## Next

- Split full-file chunks into retrieval-sized pieces
- Embeddings via pgvector
