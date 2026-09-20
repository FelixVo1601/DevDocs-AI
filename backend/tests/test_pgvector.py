"""Verify pgvector extension, embedding column, and cosine similarity."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.db import sqlalchemy_database_url
from app.embedding_config import EMBEDDING_DIMENSIONS


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in values) + "]"


def _unit_axis(index: int, dim: int = EMBEDDING_DIMENSIONS) -> list[float]:
    vec = [0.0] * dim
    vec[index] = 1.0
    return vec


@pytest.fixture(scope="module")
def engine():
    settings = get_settings()
    eng = create_engine(sqlalchemy_database_url(settings.database_url))
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — skip when Postgres is down
        pytest.skip(f"Postgres not available: {exc}")
    return eng


def test_pgvector_extension_enabled(engine) -> None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).fetchone()
    assert row is not None, "CREATE EXTENSION vector did not run (alembic upgrade head?)"


def test_code_chunks_embedding_column(engine) -> None:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT format_type(a.atttypid, a.atttypmod) AS col_type
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = 'public'
                  AND c.relname = 'code_chunks'
                  AND a.attname = 'embedding'
                  AND a.attnum > 0
                  AND NOT a.attisdropped
                """
            )
        ).fetchone()
    assert row is not None
    assert row[0] == f"vector({EMBEDDING_DIMENSIONS})"


def test_similarity_query_on_dummy_vectors(engine) -> None:
    """
    Nearest-neighbor with <=> (cosine distance) on three axis-aligned dummies.

    Query ≈ e0 should rank the e0 row first.
    """
    e0 = _vector_literal(_unit_axis(0))
    e1 = _vector_literal(_unit_axis(1))
    e2 = _vector_literal(_unit_axis(2))
    # Slightly noisy query still closest to e0.
    query = _vector_literal([0.95] + [0.01] * (EMBEDDING_DIMENSIONS - 1))

    with engine.begin() as conn:
        conn.execute(text("CREATE TEMP TABLE vec_demo (id int PRIMARY KEY, label text, embedding vector)"))
        conn.execute(
            text(
                f"""
                INSERT INTO vec_demo (id, label, embedding) VALUES
                  (1, 'axis-0', '{e0}'::vector),
                  (2, 'axis-1', '{e1}'::vector),
                  (3, 'axis-2', '{e2}'::vector)
                """
            )
        )
        rows = conn.execute(
            text(
                f"""
                SELECT label, embedding <=> '{query}'::vector AS distance
                FROM vec_demo
                ORDER BY embedding <=> '{query}'::vector
                LIMIT 3
                """
            )
        ).fetchall()

    assert [r[0] for r in rows] == ["axis-0", "axis-1", "axis-2"]
    assert rows[0][1] < rows[1][1] <= rows[2][1]
