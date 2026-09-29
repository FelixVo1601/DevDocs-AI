# Retrieval — DevDocs AI

Day 23: embed a question and return the nearest chunks for the selected repository.

## API

```http
POST /github/selected-repo/retrieve
Content-Type: application/json

{"question": "How does user login work?", "k": 5}
```

Session cookie required. The selected repo must already have embeddings (`POST /github/selected-repo/index`).

| Field | Default | Notes |
|-------|---------|--------|
| `question` | required | Empty/whitespace → `400` |
| `k` | `5` | `1`–`20` |

Each hit includes `path`, `chunk_index`, `start_line`, `end_line`, `content`, and cosine `distance` (lower is closer). Search is limited to the signed-in user’s selected repository.

## How it works

1. Normalize the question (same truncation rules as chunk embeddings)
2. Embed it with the OpenAI-compatible client
3. `ORDER BY embedding <=> question_vector LIMIT k` on `code_chunks` joined to `repository_files`

## Demo expectation

On a fixture repo, the question “How does user login work?” ranks `src/auth/login.py` first. Covered by `backend/tests/test_retrieve.py`.
