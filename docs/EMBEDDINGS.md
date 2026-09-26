# Embeddings — DevDocs AI

Day 20: OpenAI-compatible embeddings client + write vectors for a selected repo’s chunks.

## Env

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | _(required)_ | Bearer token for the provider |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible `/embeddings` base |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Must return **1536** dims (see `EMBEDDING_DIMENSIONS`) |

Never log the API key.

## API

```http
POST /github/selected-repo/embed?force=false
```

Session cookie required. Prerequisites: GitHub selected + `POST /github/selected-repo/fetch` already ran.

| Query | Effect |
|-------|--------|
| `force=false` (default) | Only embed rows where `embedding` is NULL |
| `force=true` | Re-embed all non-empty chunks |

Response includes `embedded`, `skipped_empty`, `skipped_existing`, `truncated`.

## Edge cases

| Case | Behavior |
|------|----------|
| Empty / whitespace chunk | Skipped (`skipped_empty`) — no crash |
| Oversized chunk | Truncated to `MAX_EMBEDDING_CHARS` (28 000), still embedded |
| Missing API key | `400` with clear message |
| Wrong vector width | `502` — refuses to store non-1536 vectors |
| No files fetched yet | `400` — run fetch first |

## Implementation

- `app/services/embeddings_client.py` — HTTP client + `prepare_embedding_text`
- `app/services/embed_repo.py` — load chunks for selected repo, batch embed, write `code_chunks.embedding`
- Batches of `EMBEDDING_BATCH_SIZE` (16)

## Tests

```bash
cd backend
pytest tests/test_embeddings_client.py tests/test_embed_repo.py -q
```

`test_embed_repo.py` seeds a tiny fixture repo (normal + empty + oversized chunk), mocks the provider, and asserts vectors land in Postgres.

## Next

- Retriever: embed the user question → cosine search over `code_chunks.embedding`
- Ask / RAG endpoint with citations
