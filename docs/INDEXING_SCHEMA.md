# Indexing schema — DevDocs AI

Schema ready for repository ingestion (Day 15). **No ingestion/RAG implementation yet.**

## Tables

```text
users
  └── selected_repositories          # one selected GitHub repo per user (Day 14)
        ├── index_jobs               # ingestion/index run status
        └── repository_files         # discovered source/doc files
              └── code_chunks        # text chunks (embeddings later via pgvector)
```

| Table | Purpose |
|-------|---------|
| `selected_repositories` | User’s chosen repo metadata |
| `index_jobs` | Job lifecycle: `pending` → `running` → `succeeded` / `failed` |
| `repository_files` | File path + sha/language/size under a selected repo |
| `code_chunks` | Chunk text + line range; **no vector column yet** |

## Apply

```bash
docker compose up -d db
cd backend
alembic upgrade head
```

## Next (not this PR)

- Start an `index_jobs` row and fetch files from GitHub
- Chunk into `code_chunks`
- Add pgvector embedding column / extension
