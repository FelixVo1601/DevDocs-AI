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

On `/app`, after a repository is selected, the index panel:

- **Index repository** starts `POST /github/selected-repo/index` (label becomes **Re-index repository** when status is `ready`)
- Shows the backend status word exactly: `pending`, `running`, `ready`, or `failed` (`not indexed` only when there is no job)
- While the request is in flight, the panel shows `running`, matching the job the API writes before it returns
- **Refresh status** reloads `GET /github/selected-repo/index-status`
- Failed jobs show `error_message`; a different request error is appended

Status copy lives in `frontend/src/lib/indexStatus.ts` and `frontend/src/lib/IndexPanel.svelte`.

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
