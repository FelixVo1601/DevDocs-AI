"""Database engine, sessions, and health helpers."""

from collections.abc import Generator

import psycopg
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def sqlalchemy_database_url(url: str) -> str:
    """Normalize DATABASE_URL for SQLAlchemy + psycopg3."""
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        sqlalchemy_database_url(settings.database_url),
        pool_pre_ping=True,
    )


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_database() -> str:
    """Run a simple SELECT 1 and return 'ok' when the DB is reachable."""
    settings = get_settings()
    try:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                row = cur.fetchone()
        if row and row[0] == 1:
            return "ok"
        raise HTTPException(status_code=503, detail="unexpected database response")
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc


def schema_ready() -> bool:
    """Return True when users and sessions tables exist."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('users', 'sessions')
                """
            )
        )
        return int(result.scalar_one()) == 2
