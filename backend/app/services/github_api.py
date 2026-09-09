"""Authenticated GitHub REST helpers. Never log access tokens."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.services.github_oauth import GitHubOAuthError

logger = logging.getLogger(__name__)

GITHUB_REPOS_URL = "https://api.github.com/user/repos"
MAX_PAGES = 10


def _auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "DevDocs-AI",
    }


def list_user_repositories(access_token: str) -> list[dict[str, Any]]:
    """
    List repositories visible to the token (owned, collaborator, org member).
    Includes public and accessible private repos.
    """
    repos: list[dict[str, Any]] = []
    try:
        with httpx.Client(timeout=30.0) as client:
            for page in range(1, MAX_PAGES + 1):
                response = client.get(
                    GITHUB_REPOS_URL,
                    headers=_auth_headers(access_token),
                    params={
                        "per_page": 100,
                        "page": page,
                        "sort": "updated",
                        "direction": "desc",
                        "affiliation": "owner,collaborator,organization_member",
                    },
                )
                if response.status_code == 401:
                    logger.error("GitHub repos request unauthorized")
                    raise GitHubOAuthError("GitHub token is invalid or expired")
                if response.status_code == 403:
                    logger.error("GitHub repos request forbidden (rate limit or scope)")
                    raise GitHubOAuthError("GitHub denied repository access")
                if response.status_code >= 400:
                    logger.error("GitHub repos endpoint returned HTTP %s", response.status_code)
                    raise GitHubOAuthError("Could not list GitHub repositories")

                batch = response.json()
                if not isinstance(batch, list):
                    logger.error("GitHub repos response was not a list")
                    raise GitHubOAuthError("Unexpected GitHub repositories response")
                if not batch:
                    break

                for item in batch:
                    repos.append(_normalize_repo(item))

                if len(batch) < 100:
                    break
    except httpx.HTTPError as exc:
        logger.exception("GitHub repos request failed")
        raise GitHubOAuthError("Could not reach GitHub repositories endpoint") from exc

    logger.info("Listed %s GitHub repositories for connected user", len(repos))
    return repos


def get_repository_by_id(access_token: str, github_repo_id: int) -> dict[str, Any]:
    """Fetch a single repository the token can access (verifies selection)."""
    url = f"https://api.github.com/repositories/{github_repo_id}"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=_auth_headers(access_token))
    except httpx.HTTPError as exc:
        logger.exception("GitHub repository request failed")
        raise GitHubOAuthError("Could not reach GitHub repository endpoint") from exc

    if response.status_code == 404:
        raise GitHubOAuthError("Repository not found or not accessible")
    if response.status_code == 401:
        raise GitHubOAuthError("GitHub token is invalid or expired")
    if response.status_code >= 400:
        logger.error("GitHub repository endpoint returned HTTP %s", response.status_code)
        raise GitHubOAuthError("Could not load GitHub repository")

    payload = response.json()
    if not isinstance(payload, dict) or "id" not in payload:
        raise GitHubOAuthError("Unexpected GitHub repository response")
    return _normalize_repo(payload)


def _normalize_repo(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(item["id"]),
        "name": str(item["name"]),
        "full_name": str(item["full_name"]),
        "private": bool(item.get("private", False)),
        "html_url": str(item.get("html_url") or ""),
        "description": item.get("description"),
        "default_branch": str(item.get("default_branch") or "main"),
        "language": item.get("language"),
        "updated_at": item.get("updated_at"),
    }
