"""Index job trigger reaches ready for a tiny fixture (mocked GitHub + embeddings)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db import sqlalchemy_database_url
from app.config import get_settings
from app.embedding_config import EMBEDDING_DIMENSIONS
from app.models import IndexJob, IndexJobStatus, SelectedRepository, User
from app.services.index_repo import get_index_status, index_selected_repository


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
                pytest.skip("pgvector extension missing")
            # Ensure ready enum label exists (migration 0006).
            labels = {
                r[0]
                for r in conn.execute(
                    text(
                        "SELECT enumlabel FROM pg_enum e "
                        "JOIN pg_type t ON e.enumtypid = t.oid "
                        "WHERE t.typname = 'index_job_status'"
                    )
                )
            }
            if "ready" not in labels:
                pytest.skip("index_job_status.ready missing (alembic upgrade head?)")
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
    model = "fake-embedding-model"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.01 * (i + 1)] * EMBEDDING_DIMENSIONS for i, _ in enumerate(texts)]


def test_index_reaches_ready_for_small_repo(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    user = User(
        id=uuid4(),
        email=f"day21-{uuid4().hex[:8]}@example.com",
        password_hash="unused",
    )
    selected = SelectedRepository(
        id=uuid4(),
        user_id=user.id,
        github_repo_id=21001,
        name="tiny",
        full_name="devdocs/tiny",
        private=False,
        html_url="https://github.com/devdocs/tiny",
        default_branch="main",
        description="Day 21 fixture",
    )
    db_session.add_all([user, selected])
    db_session.commit()

    monkeypatch.setattr(
        "app.services.index_repo.get_github_access_token",
        lambda _db, _uid: "fake-token",
    )

    def fake_fetch(_db, sel, _token):
        from uuid import uuid4 as new_id

        from app.models import CodeChunk, RepositoryFile

        file_row = RepositoryFile(
            id=new_id(),
            selected_repository_id=sel.id,
            path="README.md",
            content_sha="deadbeef",
            language="markdown",
            size_bytes=20,
            line_count=2,
        )
        _db.add(file_row)
        _db.flush()
        _db.add(
            CodeChunk(
                id=new_id(),
                file_id=file_row.id,
                chunk_index=0,
                start_line=1,
                end_line=2,
                content="# Tiny\nHello",
                token_count=2,
            )
        )
        _db.flush()
        return {
            "full_name": sel.full_name,
            "ref": sel.default_branch,
            "commit_sha": "abc123commit",
            "file_count": 1,
            "chunk_count": 1,
            "skipped_over_cap": 0,
            "files": [],
        }

    monkeypatch.setattr(
        "app.services.index_repo.fetch_and_store_contents",
        fake_fetch,
    )

    result = index_selected_repository(
        db_session,
        user.id,
        embeddings_client=FakeEmbeddingsClient(),  # type: ignore[arg-type]
    )

    assert result["job"]["status"] == "ready"
    assert result["job"]["commit_sha"] == "abc123commit"
    assert result["file_count"] == 1
    assert result["chunk_count"] == 1
    assert result["embedded_count"] == 1
    assert result["embedded"] == 1

    status = get_index_status(db_session, user.id)
    assert status["job"]["status"] == "ready"
    assert status["embedded_count"] == 1

    job = db_session.scalar(
        select(IndexJob).where(IndexJob.selected_repository_id == selected.id)
    )
    assert job is not None
    assert job.status == IndexJobStatus.READY


def test_index_marks_failed_when_no_files(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fastapi import HTTPException

    user = User(
        id=uuid4(),
        email=f"day21-empty-{uuid4().hex[:8]}@example.com",
        password_hash="unused",
    )
    selected = SelectedRepository(
        id=uuid4(),
        user_id=user.id,
        github_repo_id=21002,
        name="empty",
        full_name="devdocs/empty",
        private=False,
        html_url="https://github.com/devdocs/empty",
        default_branch="main",
        description=None,
    )
    db_session.add_all([user, selected])
    db_session.commit()

    monkeypatch.setattr(
        "app.services.index_repo.get_github_access_token",
        lambda _db, _uid: "fake-token",
    )
    monkeypatch.setattr(
        "app.services.index_repo.fetch_and_store_contents",
        lambda _db, sel, _token: {
            "full_name": sel.full_name,
            "ref": "main",
            "commit_sha": "c0ffee",
            "file_count": 0,
            "chunk_count": 0,
            "skipped_over_cap": 0,
            "files": [],
        },
    )

    with pytest.raises(HTTPException) as exc_info:
        index_selected_repository(
            db_session,
            user.id,
            embeddings_client=FakeEmbeddingsClient(),  # type: ignore[arg-type]
        )
    assert exc_info.value.status_code == 400

    status = get_index_status(db_session, user.id)
    assert status["job"]["status"] == "failed"
    assert "No indexable files" in (status["job"]["error_message"] or "")
