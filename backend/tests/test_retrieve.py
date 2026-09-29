"""Known-question retrieval on a tiny demo repo returns the expected file path."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db import sqlalchemy_database_url
from app.embedding_config import EMBEDDING_DIMENSIONS
from app.models import CodeChunk, RepositoryFile, SelectedRepository, User
from app.services.retrieve import retrieve_similar_chunks


def _axis(index: int, scale: float = 1.0) -> list[float]:
    vec = [0.0] * EMBEDDING_DIMENSIONS
    vec[index] = scale
    return vec


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


class LoginQuestionClient:
    """Maps a login question to the same axis as src/auth/login.py."""

    model = "fake-embedding-model"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        assert len(texts) == 1
        if "login" in texts[0].lower():
            return [_axis(0)]
        return [_axis(2)]


def _add_file(
    db: Session,
    selected: SelectedRepository,
    path: str,
    content: str,
    embedding: list[float],
) -> None:
    file_row = RepositoryFile(
        id=uuid4(),
        selected_repository_id=selected.id,
        path=path,
        content_sha=uuid4().hex[:12],
        language="python" if path.endswith(".py") else "markdown",
        size_bytes=len(content),
        line_count=content.count("\n") + 1,
    )
    db.add(file_row)
    db.flush()
    db.add(
        CodeChunk(
            id=uuid4(),
            file_id=file_row.id,
            chunk_index=0,
            start_line=1,
            end_line=file_row.line_count,
            content=content,
            token_count=len(content.split()),
            embedding=embedding,
        )
    )


def test_login_question_hits_auth_file(db_session: Session) -> None:
    user = User(
        id=uuid4(),
        email=f"day23-{uuid4().hex[:8]}@example.com",
        password_hash="unused",
    )
    selected = SelectedRepository(
        id=uuid4(),
        user_id=user.id,
        github_repo_id=23001,
        name="demo",
        full_name="devdocs/demo-repo",
        private=False,
        html_url="https://github.com/devdocs/demo-repo",
        default_branch="main",
        description="Day 23 demo",
    )
    other_user = User(
        id=uuid4(),
        email=f"day23-other-{uuid4().hex[:8]}@example.com",
        password_hash="unused",
    )
    other = SelectedRepository(
        id=uuid4(),
        user_id=other_user.id,
        github_repo_id=23002,
        name="other",
        full_name="devdocs/other",
        private=False,
        html_url="https://github.com/devdocs/other",
        default_branch="main",
        description=None,
    )

    db_session.add_all([user, other_user, selected, other])
    db_session.flush()

    _add_file(
        db_session,
        selected,
        "src/auth/login.py",
        "def login(email, password):\n    return session_for(email)",
        _axis(0),
    )
    # Slightly off axis 1 so it ranks after login for an axis-0 query.
    billing = _axis(1)
    billing[0] = 0.15
    _add_file(
        db_session,
        selected,
        "docs/billing.md",
        "Invoices are generated monthly.",
        billing,
    )
    _add_file(
        db_session,
        selected,
        "README.md",
        "Demo repository overview.",
        _axis(2),
    )
    # Closer decoy in another repo must not appear.
    _add_file(
        db_session,
        other,
        "src/auth/login.py",
        "other repo login",
        _axis(0),
    )
    db_session.commit()

    result = retrieve_similar_chunks(
        db_session,
        user.id,
        "How does user login work?",
        k=2,
        client=LoginQuestionClient(),  # type: ignore[arg-type]
    )

    paths = [hit["path"] for hit in result["hits"]]
    assert result["full_name"] == "devdocs/demo-repo"
    assert paths[0] == "src/auth/login.py"
    assert "src/auth/login.py" in paths
    assert "docs/billing.md" in paths
    assert "README.md" not in paths
    assert result["hits"][0]["distance"] < result["hits"][1]["distance"]
    assert "login" in result["hits"][0]["content"]


def test_empty_question_rejected(db_session: Session) -> None:
    user = db_session.scalar(
        select(User)
        .join(SelectedRepository, SelectedRepository.user_id == User.id)
        .where(SelectedRepository.full_name == "devdocs/demo-repo")
    )
    assert user is not None
    with pytest.raises(HTTPException) as exc_info:
        retrieve_similar_chunks(
            db_session,
            user.id,
            "   ",
            client=LoginQuestionClient(),  # type: ignore[arg-type]
        )
    assert exc_info.value.status_code == 400
