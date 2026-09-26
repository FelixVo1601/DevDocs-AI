"""Unit tests for embedding text prep and the OpenAI-compatible client."""

from __future__ import annotations

import json

import httpx
import pytest

from app.config import Settings
from app.embedding_config import EMBEDDING_DIMENSIONS, MAX_EMBEDDING_CHARS
from app.services.embeddings_client import (
    EmbeddingsClient,
    EmbeddingsError,
    prepare_embedding_text,
)


def _settings(**overrides: str) -> Settings:
    base = {
        "openai_api_key": "test-key",
        "openai_base_url": "https://example.test/v1",
        "embedding_model": "text-embedding-3-small",
    }
    base.update(overrides)
    return Settings(**base)


def test_prepare_skips_empty_and_whitespace() -> None:
    assert prepare_embedding_text("") is None
    assert prepare_embedding_text("   \n\t  ") is None


def test_prepare_passes_through_normal_text() -> None:
    assert prepare_embedding_text("  hello world  ") == "hello world"


def test_prepare_truncates_large_text() -> None:
    huge = "x" * (MAX_EMBEDDING_CHARS + 500)
    out = prepare_embedding_text(huge)
    assert out is not None
    assert len(out) == MAX_EMBEDDING_CHARS


def test_client_requires_api_key() -> None:
    with pytest.raises(EmbeddingsError, match="OPENAI_API_KEY"):
        EmbeddingsClient(_settings(openai_api_key=""))


def test_embed_texts_orders_and_validates_dimensions(monkeypatch: pytest.MonkeyPatch) -> None:
    vector_a = [0.1] * EMBEDDING_DIMENSIONS
    vector_b = [0.2] * EMBEDDING_DIMENSIONS

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/embeddings")
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.content.decode())
        assert body["model"] == "text-embedding-3-small"
        assert body["input"] == ["alpha", "beta"]
        payload = {
            "data": [
                {"index": 1, "embedding": vector_b},
                {"index": 0, "embedding": vector_a},
            ]
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    original = httpx.Client

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", factory)
    vectors = EmbeddingsClient(_settings()).embed_texts(["alpha", "beta"])
    assert vectors[0][0] == pytest.approx(0.1)
    assert vectors[1][0] == pytest.approx(0.2)


def test_embed_texts_rejects_wrong_dimension(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}]},
        )

    original = httpx.Client

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", factory)
    with pytest.raises(EmbeddingsError, match="dimension"):
        EmbeddingsClient(_settings()).embed_texts(["tiny"])


def test_embed_texts_empty_list() -> None:
    assert EmbeddingsClient(_settings()).embed_texts([]) == []
