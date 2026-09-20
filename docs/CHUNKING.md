# Chunking — DevDocs AI

How fetched repository files become retrieval units for later RAG citations.

Implementation: `backend/app/services/chunking.py` · Tests: `backend/tests/test_chunking.py`

## Goals

- Chunk size stays **reasonable** for embedding/retrieval (~40 lines).
- Each chunk carries **citation metadata**: file path (via `repository_files` + response), `chunk_index`, inclusive `start_line` / `end_line`.
- Behavior is **deterministic** so a sample file produces predictable windows.

## Algorithm

Line-based sliding windows with overlap:

| Setting | Default | Role |
|---------|---------|------|
| `max_lines` | 40 | Soft max lines per chunk |
| `overlap_lines` | 5 | Shared lines between adjacent chunks |

Step size is `max_lines - overlap_lines` (35 with defaults).

Example — 100-line sample file:

| chunk_index | start_line | end_line |
|-------------|------------|----------|
| 0 | 1 | 40 |
| 1 | 36 | 75 |
| 2 | 71 | 100 |

Empty files produce **no** chunks. Short files become a single chunk covering lines `1…N`.

`token_count` is a whitespace word estimate (not a model tokenizer) for size budgeting until embeddings land.

## Storage

On `POST /github/selected-repo/fetch`:

1. Filter + fetch blob text (Days 16–17)
2. `chunk_file_content(text)` → list of windows
3. Persist one `code_chunks` row per window (`file_id`, `chunk_index`, `start_line`, `end_line`, `content`, `token_count`)

Citation shape later: ``{path}:{start_line}-{end_line}`` joined through `repository_files.path`.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests/test_chunking.py
```

The numbered 100-line sample (`L001`…`L100`) locks the table above.
