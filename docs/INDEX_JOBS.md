# Index jobs — DevDocs AI

Day 21: trigger a full repository index and read job status.

## Status values

| Status | Meaning |
|--------|---------|
| `pending` | Job row created |
| `running` | Fetch / chunk / embed in progress (sync MVP) |
| `ready` | Snapshot + embeddings stored |
| `failed` | Error; see `error_message` |

(Previously `succeeded`; renamed to `ready` in migration `0006_index_job_ready`.)

## API

```http
POST /github/selected-repo/index
GET  /github/selected-repo/index-status
```

Session cookie required. Needs a selected repo, GitHub token, and `OPENAI_API_KEY` for embeddings.

`POST` runs **synchronously** for MVP: GitHub fetch → chunk → embed, then returns the final status (`ready` or raises after marking `failed`).

`GET` returns the latest job for the selected repo plus `file_count` / `chunk_count` / `embedded_count`.

## UI

On `/app`, after selecting a repository: **Index repository** button and live status (including re-index when already `ready`).

## Apply

```bash
docker compose up -d db
cd backend
alembic upgrade head   # includes 0006_index_job_ready
```

## Tests

```bash
cd backend
pytest tests/test_index_repo.py -q
```
