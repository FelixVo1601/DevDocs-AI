# pgvector setup — DevDocs AI

Day 19 enables vector storage on top of the existing Postgres database.

## Compose

`docker-compose.yml` uses **`pgvector/pgvector:pg16`** (not plain `postgres:16-alpine`) so `CREATE EXTENSION vector` works.

If you previously ran the alpine image against the same named volume, recreate it once:

```bash
docker compose down
docker compose up -d db
cd backend
alembic upgrade head
```

(Optional clean slate: `docker compose down -v` — destroys local DB data.)

## Migration `0005_pgvector`

1. `CREATE EXTENSION IF NOT EXISTS vector`
2. `code_chunks.embedding vector(1536)` (nullable until embeddings are generated)

Dimension is `EMBEDDING_DIMENSIONS` in `backend/app/embedding_config.py` (1536 — OpenAI-compatible small embeddings).

## ORM

`CodeChunk.embedding` uses `pgvector.sqlalchemy.Vector`. The Python package `pgvector` is in `requirements.txt`.

## Verify similarity

With Postgres up and migrations applied:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/test_pgvector.py -q
```

The test inserts three dummy vectors and asserts cosine distance (`<=>`) ranks the expected nearest neighbor first.

## Next

- Generate real embeddings for chunks
- Retriever query path for ask/RAG
