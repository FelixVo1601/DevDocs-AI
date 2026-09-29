"""POST /ask grounds a test question in retrieved chunks with path + chunk id."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db import sqlalchemy_database_url
from app.embedding_config import EMBEDDING_DIMENSIONS
from app.models import CodeChunk, RepositoryFile, SelectedRepository, User
from app.services.ask import ask_question


def _axis(index: int) -> list[float]:
    vec = [0.0] * EMBEDDING_DIMENSIONS
    vec[index] = 1.0
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
            if (
                conn.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                ).fetchone()
                is None
            ):
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
    model = "fake-embedding-model"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_axis(0 if "login" in texts[0].lower() else 1)]


class GroundedChat:
    model = "fake-chat-model"

    def __init__(self) -> None:
        self.seen: list[str] = []

    def complete(self, messages: list[dict[str, str]]) -> str:
        user = messages[-1]["content"]
        self.seen.append(user)
        assert "src/auth/login.py" in user
        return (
            "Login builds a session for the given email [1]. "
            "That behavior is in src/auth/login.py."
        )


def test_ask_returns_grounded_answer_with_citations(db_session: Session) -> None:
    user = User(
        id=uuid4(),
        email=f"day24-{uuid4().hex[:8]}@example.com",
        password_hash="unused",
    )
    selected = SelectedRepository(
        id=uuid4(),
        user_id=user.id,
        github_repo_id=24001,
        name="demo",
        full_name="devdocs/ask-demo",
        private=False,
        html_url="https://github.com/devdocs/ask-demo",
        default_branch="main",
        description="Day 24 demo",
    )
    db_session.add_all([user, selected])
    db_session.flush()

    login_file = RepositoryFile(
        id=uuid4(),
        selected_repository_id=selected.id,
        path="src/auth/login.py",
        content_sha="loginsha",
        language="python",
        size_bytes=40,
        line_count=2,
    )
    db_session.add(login_file)
    db_session.flush()
    login_chunk = CodeChunk(
        id=uuid4(),
        file_id=login_file.id,
        chunk_index=0,
        start_line=1,
        end_line=2,
        content="def login(email, password):\n    return session_for(email)",
        token_count=6,
        embedding=_axis(0),
    )
    billing_file = RepositoryFile(
        id=uuid4(),
        selected_repository_id=selected.id,
        path="docs/billing.md",
        content_sha="billsha",
        language="markdown",
        size_bytes=20,
        line_count=1,
    )
    db_session.add(billing_file)
    db_session.flush()
    db_session.add_all(
        [
            login_chunk,
            CodeChunk(
                id=uuid4(),
                file_id=billing_file.id,
                chunk_index=0,
                start_line=1,
                end_line=1,
                content="Invoices are generated monthly.",
                token_count=4,
                embedding=_axis(1),
            ),
        ]
    )
    db_session.commit()

    chat = GroundedChat()
    result = ask_question(
        db_session,
        user.id,
        "How does user login work?",
        k=2,
        embeddings_client=LoginQuestionClient(),  # type: ignore[arg-type]
        chat_client=chat,  # type: ignore[arg-type]
    )

    assert "session" in result["answer"].lower()
    assert result["citations"]
    top = result["citations"][0]
    assert top["path"] == "src/auth/login.py"
    assert top["chunk_id"] == str(login_chunk.id)
    assert any(item["path"] == "src/auth/login.py" for item in result["citations"])
    assert "src/auth/login.py" in chat.seen[0]
