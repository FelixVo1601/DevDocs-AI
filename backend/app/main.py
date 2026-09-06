"""DevDocs AI FastAPI application."""

from fastapi import FastAPI

app = FastAPI(
    title="DevDocs AI",
    description="AI-powered developer knowledge and documentation assistant API",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check for local development and later orchestration."""
    return {"status": "ok"}
