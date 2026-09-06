"""Database helpers."""

import psycopg
from fastapi import HTTPException

from app.config import get_settings


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
