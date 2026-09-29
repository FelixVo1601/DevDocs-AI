# Ask (RAG) — DevDocs AI

Day 24: retrieve chunks, prompt an LLM, return a grounded answer plus citations.

## API

```http
POST /ask
Content-Type: application/json

{"question": "How does user login work?", "k": 5}
```

Session cookie required. The selected repository must already be indexed.

Response:

| Field | Meaning |
|-------|---------|
| `answer` | Chat model text grounded in the retrieved excerpts |
| `citations[]` | Chunks passed into the prompt |
| `citations[].path` | Repository file path |
| `citations[].chunk_id` | `code_chunks.id` |
| `citations[].start_line` / `end_line` | Inclusive line range |

## Env

Uses the same OpenAI-compatible base as embeddings:

| Variable | Default |
|----------|---------|
| `OPENAI_API_KEY` | required |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` |
| `CHAT_MODEL` | `gpt-4o-mini` |

## Flow

1. `retrieve_similar_chunks` embeds the question and loads the top-k chunks
2. Those excerpts are placed in the user prompt with `[n] path:start-end (chunk id)` labels
3. `POST /chat/completions` returns the answer
4. The same chunks are returned as `citations` (path + chunk id), independent of how the model phrases the answer
