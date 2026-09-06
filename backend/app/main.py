"""DevDocs AI FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import ping_database
from app.routers import auth

settings = get_settings()

app = FastAPI(
    title="DevDocs AI",
    description="AI-powered developer knowledge and documentation assistant API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check for local development and later orchestration."""
    return {"status": "ok"}


@app.get("/db/ping")
def db_ping() -> dict[str, str]:
    """Verify the API can reach PostgreSQL using DATABASE_URL."""
    return {"database": ping_database()}


@app.get("/db/schema")
def db_schema() -> dict[str, bool]:
    """Confirm auth tables exist after migrations (no UI yet)."""
    from app.db import schema_ready

    return {"users_and_sessions": schema_ready()}
