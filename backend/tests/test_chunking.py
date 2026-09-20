"""Predictable sample-file coverage for line-based chunking."""

from __future__ import annotations

import pytest

from app.services.chunking import (
    DEFAULT_MAX_LINES,
    DEFAULT_OVERLAP_LINES,
    chunk_file_content,
    estimate_token_count,
)


def _numbered_file(line_count: int) -> str:
    """Build a deterministic sample file: ``L001``, ``L002``, …"""
    return "\n".join(f"L{i:03d}" for i in range(1, line_count + 1))


def test_empty_content_yields_no_chunks() -> None:
    assert chunk_file_content("") == []


def test_short_file_is_single_chunk() -> None:
    content = _numbered_file(12)
    chunks = chunk_file_content(content, max_lines=40, overlap_lines=5)

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 12
    assert chunks[0].content.startswith("L001")
    assert chunks[0].content.endswith("L012")
    assert chunks[0].token_count == 12


def test_sample_file_produces_predictable_chunks() -> None:
    """
    100-line sample with max_lines=40 and overlap=5:

    - chunk 0: lines 1–40
    - chunk 1: lines 36–75  (step = 35)
    - chunk 2: lines 71–100
    """
    content = _numbered_file(100)
    chunks = chunk_file_content(content, max_lines=40, overlap_lines=5)

    assert [(c.chunk_index, c.start_line, c.end_line) for c in chunks] == [
        (0, 1, 40),
        (1, 36, 75),
        (2, 71, 100),
    ]
    assert chunks[0].content.splitlines()[0] == "L001"
    assert chunks[0].content.splitlines()[-1] == "L040"
    assert chunks[1].content.splitlines()[0] == "L036"
    assert chunks[1].content.splitlines()[-1] == "L075"
    assert chunks[2].content.splitlines()[0] == "L071"
    assert chunks[2].content.splitlines()[-1] == "L100"


def test_exact_window_size_is_one_chunk() -> None:
    content = _numbered_file(40)
    chunks = chunk_file_content(content, max_lines=40, overlap_lines=5)
    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 40


def test_one_line_over_window_adds_second_chunk() -> None:
    content = _numbered_file(41)
    chunks = chunk_file_content(content, max_lines=40, overlap_lines=5)
    assert [(c.start_line, c.end_line) for c in chunks] == [(1, 40), (36, 41)]


def test_defaults_match_documented_sizes() -> None:
    assert DEFAULT_MAX_LINES == 40
    assert DEFAULT_OVERLAP_LINES == 5


def test_defaults_keep_chunk_size_reasonable() -> None:
    content = _numbered_file(200)
    chunks = chunk_file_content(content)
    assert all(c.end_line - c.start_line + 1 <= DEFAULT_MAX_LINES for c in chunks)
    assert len(chunks) >= 2
    # Adjacent chunks overlap by DEFAULT_OVERLAP_LINES lines.
    assert chunks[1].start_line == chunks[0].end_line - DEFAULT_OVERLAP_LINES + 1


def test_citation_metadata_is_inclusive_and_ordered() -> None:
    content = _numbered_file(90)
    chunks = chunk_file_content(content, max_lines=40, overlap_lines=5)
    for chunk in chunks:
        assert chunk.start_line >= 1
        assert chunk.end_line >= chunk.start_line
        assert chunk.end_line - chunk.start_line + 1 == len(chunk.content.splitlines())
    indexes = [c.chunk_index for c in chunks]
    assert indexes == list(range(len(chunks)))


@pytest.mark.parametrize(
    ("max_lines", "overlap_lines"),
    [(0, 0), (10, -1), (10, 10), (10, 11)],
)
def test_invalid_parameters_raise(max_lines: int, overlap_lines: int) -> None:
    with pytest.raises(ValueError):
        chunk_file_content("a\nb\n", max_lines=max_lines, overlap_lines=overlap_lines)


def test_estimate_token_count() -> None:
    assert estimate_token_count("") == 0
    assert estimate_token_count("  ") == 0
    assert estimate_token_count("alpha beta gamma") == 3
