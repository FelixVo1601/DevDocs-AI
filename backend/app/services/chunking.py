"""Split source/doc files into retrieval-sized chunks with line metadata."""

from __future__ import annotations

from dataclasses import dataclass

# ~40 lines is a common RAG window for code; small enough for embeddings later,
# large enough to keep a function body mostly intact.
DEFAULT_MAX_LINES = 40
DEFAULT_OVERLAP_LINES = 5


@dataclass(frozen=True)
class TextChunk:
    """One retrieval unit with citation-ready line range (1-based, inclusive)."""

    chunk_index: int
    start_line: int
    end_line: int
    content: str
    token_count: int


def estimate_token_count(text: str) -> int:
    """
    Cheap token estimate until a real tokenizer/embeddings land.

    Whitespace-separated words are stable for tests and good enough for
    size budgeting; not an OpenAI/tiktoken count.
    """
    stripped = text.strip()
    if not stripped:
        return 0
    return len(stripped.split())


def chunk_file_content(
    content: str,
    *,
    max_lines: int = DEFAULT_MAX_LINES,
    overlap_lines: int = DEFAULT_OVERLAP_LINES,
) -> list[TextChunk]:
    """
    Split ``content`` into overlapping line windows.

    Line numbers are **1-based and inclusive** so citations can render as
    ``path:start_line-end_line`` later. Empty input yields no chunks.
    """
    if max_lines < 1:
        raise ValueError("max_lines must be >= 1")
    if overlap_lines < 0:
        raise ValueError("overlap_lines must be >= 0")
    if overlap_lines >= max_lines:
        raise ValueError("overlap_lines must be < max_lines")

    if content == "":
        return []

    # splitlines() drops a trailing blank line marker; keepends=False so we
    # rejoin with "\\n" for stable, predictable chunk text in tests.
    lines = content.splitlines()
    if not lines:
        return []

    step = max_lines - overlap_lines
    chunks: list[TextChunk] = []
    start_idx = 0
    chunk_index = 0
    total = len(lines)

    while start_idx < total:
        end_idx = min(start_idx + max_lines, total)
        window = lines[start_idx:end_idx]
        text = "\n".join(window)
        start_line = start_idx + 1
        end_line = end_idx
        chunks.append(
            TextChunk(
                chunk_index=chunk_index,
                start_line=start_line,
                end_line=end_line,
                content=text,
                token_count=estimate_token_count(text),
            )
        )
        chunk_index += 1
        if end_idx >= total:
            break
        start_idx += step

    return chunks
