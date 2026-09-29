"""OpenAI-compatible chat completions client. Never log API keys."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class ChatError(Exception):
    """Raised when the chat provider fails or returns invalid data."""


class ChatClient:
    """Minimal ``POST {base}/chat/completions`` client."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.api_key = (self.settings.openai_api_key or "").strip()
        self.base_url = (self.settings.openai_base_url or "").rstrip("/")
        self.model = (self.settings.chat_model or "").strip()
        if not self.api_key:
            raise ChatError(
                "OPENAI_API_KEY is not set. Add it to .env to generate answers."
            )
        if not self.base_url:
            raise ChatError("OPENAI_BASE_URL is empty")
        if not self.model:
            raise ChatError("CHAT_MODEL is empty")

    def complete(self, messages: list[dict[str, str]]) -> str:
        if not messages:
            raise ChatError("Chat completion requires at least one message")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            logger.exception("Chat completion request failed")
            raise ChatError("Could not reach chat provider") from exc

        if response.status_code == 401:
            raise ChatError("Chat provider rejected the API key")
        if response.status_code == 429:
            raise ChatError("Chat provider rate-limited the request")
        if response.status_code >= 400:
            logger.error("Chat provider returned HTTP %s", response.status_code)
            raise ChatError("Chat provider returned an error")

        try:
            body = response.json()
        except ValueError as exc:
            raise ChatError("Chat provider returned non-JSON") from exc

        choices = body.get("choices") if isinstance(body, dict) else None
        if not isinstance(choices, list) or not choices:
            raise ChatError("Unexpected chat response shape")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ChatError("Chat provider returned an empty answer")
        return content.strip()
