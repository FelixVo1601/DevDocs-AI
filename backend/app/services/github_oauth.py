"""GitHub OAuth helpers. Never log access tokens or client secrets."""

from __future__ import annotations

import logging
import secrets
from typing import Any
from urllib.parse import urlencode

import httpx
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import Settings

logger = logging.getLogger(__name__)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


class GitHubOAuthError(Exception):
    """Raised when the GitHub OAuth exchange fails (safe message only)."""


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=settings.secret_key,
        salt="github-oauth-state",
    )


def create_oauth_state(settings: Settings, user_id: str) -> str:
    payload = {"uid": user_id, "nonce": secrets.token_urlsafe(16)}
    return _serializer(settings).dumps(payload)


def parse_oauth_state(settings: Settings, state: str, max_age_seconds: int = 600) -> str:
    try:
        payload = _serializer(settings).loads(state, max_age=max_age_seconds)
    except SignatureExpired as exc:
        raise GitHubOAuthError("OAuth state expired") from exc
    except BadSignature as exc:
        raise GitHubOAuthError("Invalid OAuth state") from exc

    user_id = payload.get("uid")
    if not user_id or not isinstance(user_id, str):
        raise GitHubOAuthError("Invalid OAuth state payload")
    return user_id


def build_authorize_url(settings: Settings, state: str) -> str:
    query = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": settings.github_oauth_scopes,
            "state": state,
            "allow_signup": "true",
        }
    )
    return f"{GITHUB_AUTHORIZE_URL}?{query}"


def exchange_code_for_token(settings: Settings, code: str) -> dict[str, Any]:
    """Exchange authorization code for an access token. Response must not be logged."""
    headers = {"Accept": "application/json"}
    data = {
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
        "code": code,
        "redirect_uri": settings.github_redirect_uri,
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(GITHUB_TOKEN_URL, data=data, headers=headers)
    except httpx.HTTPError as exc:
        logger.exception("GitHub token endpoint request failed")
        raise GitHubOAuthError("Could not reach GitHub token endpoint") from exc

    if response.status_code >= 400:
        logger.error("GitHub token endpoint returned HTTP %s", response.status_code)
        raise GitHubOAuthError("GitHub token exchange failed")

    payload = response.json()
    if "error" in payload:
        # GitHub may include error_description — safe to log error key only.
        logger.error("GitHub token exchange error=%s", payload.get("error"))
        raise GitHubOAuthError("GitHub denied the token exchange")

    access_token = payload.get("access_token")
    if not access_token or not isinstance(access_token, str):
        logger.error("GitHub token response missing access_token")
        raise GitHubOAuthError("GitHub token response incomplete")

    return {
        "access_token": access_token,
        "token_type": str(payload.get("token_type") or "bearer"),
        "scope": payload.get("scope"),
    }


def fetch_github_user(access_token: str) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "DevDocs-AI",
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(GITHUB_USER_URL, headers=headers)
    except httpx.HTTPError as exc:
        logger.exception("GitHub user endpoint request failed")
        raise GitHubOAuthError("Could not reach GitHub user endpoint") from exc

    if response.status_code >= 400:
        logger.error("GitHub user endpoint returned HTTP %s", response.status_code)
        raise GitHubOAuthError("Could not load GitHub profile")

    payload = response.json()
    github_id = payload.get("id")
    login = payload.get("login")
    if github_id is None or not login:
        logger.error("GitHub user payload missing id/login")
        raise GitHubOAuthError("GitHub profile incomplete")

    return {"id": int(github_id), "login": str(login)}
