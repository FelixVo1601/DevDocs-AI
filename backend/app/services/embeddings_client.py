"""OpenAI-compatible embeddings HTTP client. Never log API keys."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.embedding_config import EMBEDDING_DIMENSIONS, MAX_EMBEDDING_CHARS

logger = logging.getLogger(__name__)


class EmbeddingsError(Exception):
    """Raised when the embeddings provider fails or returns invalid data."""


def prepare_embedding_text(content: str, *, max_chars: int = MAX_EMBEDDING_CHARS) -> str | None:
    """
    Normalize chunk text for embedding.

    Returns ``None`` for empty / whitespace-only input (caller should skip).
    Truncates oversized text instead of failing the whole job.
    """
    if max_chars < 1:
        raise ValueError("max_chars must be >= 1")
    text = content.strip()
    if not text:
        return None
    if len(text) <= max_chars:
        return text
    logger.warning(
        "Truncating embedding input from %s to %s chars",
        len(text),
        max_chars,
    )
    return text[:max_chars]


class EmbeddingsClient:
    """Minimal OpenAI-compatible ``POST {base}/embeddings`` client."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.api_key = (self.settings.openai_api_key or "").strip()
        self.base_url = (self.settings.openai_base_url or "").rstrip("/")
        self.model = (self.settings.embedding_model or "").strip()
        if not self.api_key:
            raise EmbeddingsError(
                "OPENAI_API_KEY is not set. Add it to .env to generate embeddings."
            )
        if not self.base_url:
            raise EmbeddingsError("OPENAI_BASE_URL is empty")
        if not self.model:
            raise EmbeddingsError("EMBEDDING_MODEL is empty")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed one or more non-empty strings; order matches input."""
        if not texts:
            return []
        if any(not isinstance(t, str) or not t.strip() for t in texts):
            raise EmbeddingsError("embed_texts requires non-empty strings")

        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "input": texts if len(texts) > 1 else texts[0],
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            logger.exception("Embeddings request failed")
            raise EmbeddingsError("Could not reach embeddings provider") from exc
        finally:
            # Avoid lingering references to the key on the instance during errors.
            pass

        if response.status_code == 401:
            raise EmbeddingsError("Embeddings provider rejected the API key")
        if response.status_code == 429:
            raise EmbeddingsError("Embeddings provider rate-limited the request")
        if response.status_code >= 400:
            logger.error(
                "Embeddings provider returned HTTP %s",
                response.status_code,
            )
            raise EmbeddingsError("Embeddings provider returned an error")

        try:
            body = response.json()
        except ValueError as exc:
            raise EmbeddingsError("Embeddings provider returned non-JSON") from exc

        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or not data:
            raise EmbeddingsError("Unexpected embeddings response shape")

        # OpenAI returns items with an ``index`` field; sort to preserve order.
        try:
            ordered = sorted(data, key=lambda item: int(item.get("index", 0)))
        except (TypeError, ValueError, AttributeError) as exc:
            raise EmbeddingsError("Unexpected embeddings response indexes") from exc

        vectors: list[list[float]] = []
        for item in ordered:
            if not isinstance(item, dict):
                raise EmbeddingsError("Unexpected embeddings item type")
            embedding = item.get("embedding")
            if not isinstance(embedding, list) or not embedding:
                raise EmbeddingsError("Missing embedding vector in response")
            try:
                vector = [float(x) for x in embedding]
            except (TypeError, ValueError) as exc:
                raise EmbeddingsError("Embedding vector was not numeric") from exc
            if len(vector) != EMBEDDING_DIMENSIONS:
                raise EmbeddingsError(
                    f"Embedding dimension {len(vector)} != {EMBEDDING_DIMENSIONS}. "
                    "Use a model that returns 1536 dims or change EMBEDDING_DIMENSIONS."
                )
            vectors.append(vector)

        if len(vectors) != len(texts):
            raise EmbeddingsError(
                f"Expected {len(texts)} embeddings, got {len(vectors)}"
            )
        return vectors
