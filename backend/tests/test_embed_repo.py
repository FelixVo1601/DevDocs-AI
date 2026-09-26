"""Embed a tiny fixture repo: vectors land in DB; empty/large chunks are safe."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.db import sqlalchemy_database_url
from app.embedding_config import EMBEDDING_DIMENSIONS, MAX_EMBEDDING_CHARS
from app.models import CodeChunk, RepositoryFile, SelectedRepository, User
from app.services.embed_repo import embed_selected_repository_chunks
from app.services.embeddings_client import EmbeddingsClient


@pytest.fixture(scope="module")
def db_session() -> Session:
    settings = get_settings()
    eng = create_engine(
        sqlalchemy_database_url(settings.database_url),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
            ext = conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).fetchone()
            if ext is None:
                pytest.skip("pgvector extension missing (alembic upgrade head?)")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Postgres not available: {exc}")

    SessionLocal = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        eng.dispose()


class FakeEmbeddingsClient:
    """Deterministic stand-in for the HTTP embeddings provider."""

    model = "fake-embedding-model"

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        vectors: list[list[float]] = []
        for i, text in enumerate(texts):
            # Distinct, valid-length vectors derived from call order + text length.
            base = ((i + 1) * 0.001) + (len(text) % 100) * 0.00001
            vectors.append([base] * EMBEDDING_DIMENSIONS)
        return vectors


def _seed_tiny_fixture(db: Session) -> tuple[User, SelectedRepository, list[CodeChunk]]:
    """
    Tiny fixture repo with three chunks:
    - normal README text
    - empty content (must be skipped)
    - oversized content (must truncate, still embed)
    """
    user = User(
        id=uuid4(),
        email=f"day20-{uuid4().hex[:8]}@example.com",
        password_hash="not-used-in-this-test",
    )
    selected = SelectedRepository(
        id=uuid4(),
        user_id=user.id,
        github_repo_id=999001,
        name="fixture-repo",
        full_name="devdocs/fixture-repo",
        private=False,
        html_url="https://github.com/devdocs/fixture-repo",
        default_branch="main",
        description="Day 20 tiny fixture",
    )
    file_row = RepositoryFile(
        id=uuid4(),
        selected_repository_id=selected.id,
        path="README.md",
        content_sha="abc123",
        language="markdown",
        size_bytes=100,
        line_count=3,
    )
    chunks = [
        CodeChunk(
            id=uuid4(),
            file_id=file_row.id,
            chunk_index=0,
            start_line=1,
            end_line=2,
            content="# Fixture\nHello embeddings.",
            token_count=3,
        ),
        CodeChunk(
            id=uuid4(),
            file_id=file_row.id,
            chunk_index=1,
            start_line=3,
            end_line=3,
            content="   \n\t  ",
            token_count=0,
        ),
        CodeChunk(
            id=uuid4(),
            file_id=file_row.id,
            chunk_index=2,
            start_line=4,
            end_line=4,
            content="Y" * (MAX_EMBEDDING_CHARS + 200),
            token_count=None,
        ),
    ]
    db.add_all([user, selected, file_row, *chunks])
    db.commit()
    for chunk in chunks:
        db.refresh(chunk)
    return user, selected, chunks


def test_embed_writes_vectors_for_tiny_fixture_repo(db_session: Session) -> None:
    user, selected, chunks = _seed_tiny_fixture(db_session)
    fake = FakeEmbeddingsClient()

    result = embed_selected_repository_chunks(
        db_session, user.id, client=fake  # type: ignore[arg-type]
    )

    assert result["full_name"] == "devdocs/fixture-repo"
    assert result["embedded"] == 2
    assert result["skipped_empty"] == 1
    assert result["truncated"] == 1
    assert result["skipped_existing"] == 0

    # Provider saw truncated text for the large chunk, never the empty one.
    assert len(fake.calls) == 1
    assert len(fake.calls[0]) == 2
    assert fake.calls[0][0] == "# Fixture\nHello embeddings."
    assert len(fake.calls[0][1]) == MAX_EMBEDDING_CHARS

    db_session.expire_all()
    stored = {
        c.chunk_index: c
        for c in db_session.scalars(
            select(CodeChunk).where(CodeChunk.file_id == chunks[0].file_id)
        ).all()
    }
    assert stored[0].embedding is not None
    assert len(stored[0].embedding) == EMBEDDING_DIMENSIONS
    assert stored[1].embedding is None  # empty skipped
    assert stored[2].embedding is not None
    assert len(stored[2].embedding) == EMBEDDING_DIMENSIONS

    # Second run without force skips existing vectors.
    again = embed_selected_repository_chunks(
        db_session, user.id, client=fake  # type: ignore[arg-type]
    )
    assert again["embedded"] == 0
    assert again["skipped_existing"] == 2
    assert again["skipped_empty"] == 1


def test_embed_requires_configured_api_key(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    user, _, _ = _seed_tiny_fixture(db_session)
    monkeypatch.setattr(
        "app.services.embed_repo.EmbeddingsClient",
        lambda: EmbeddingsClient(
            Settings(
                openai_api_key="",
                openai_base_url="https://example.test/v1",
                embedding_model="text-embedding-3-small",
            )
        ),
    )
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        embed_selected_repository_chunks(db_session, user.id)
    assert exc_info.value.status_code == 400
    assert "OPENAI_API_KEY" in str(exc_info.value.detail)
