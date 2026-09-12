"""Authenticated GitHub REST helpers. Never log access tokens."""

from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

from app.services.github_oauth import GitHubOAuthError

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_REPOS_URL = f"{GITHUB_API}/user/repos"
MAX_PAGES = 10


def _auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "DevDocs-AI",
    }


def _raise_for_github_status(response: httpx.Response, action: str) -> None:
    if response.status_code == 401:
        raise GitHubOAuthError("GitHub token is invalid or expired")
    if response.status_code == 403:
        raise GitHubOAuthError(f"GitHub denied access while trying to {action}")
    if response.status_code == 404:
        raise GitHubOAuthError(f"GitHub resource not found while trying to {action}")
    if response.status_code >= 400:
        logger.error("GitHub %s returned HTTP %s", action, response.status_code)
        raise GitHubOAuthError(f"Could not {action}")


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
    url = f"{GITHUB_API}/repositories/{github_repo_id}"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=_auth_headers(access_token))
    except httpx.HTTPError as exc:
        logger.exception("GitHub repository request failed")
        raise GitHubOAuthError("Could not reach GitHub repository endpoint") from exc

    if response.status_code == 404:
        raise GitHubOAuthError("Repository not found or not accessible")
    _raise_for_github_status(response, "load GitHub repository")

    payload = response.json()
    if not isinstance(payload, dict) or "id" not in payload:
        raise GitHubOAuthError("Unexpected GitHub repository response")
    return _normalize_repo(payload)


def get_branch_commit_sha(access_token: str, full_name: str, ref: str) -> str:
    """Resolve a branch/tag/ref to a commit SHA."""
    url = f"{GITHUB_API}/repos/{full_name}/commits/{ref}"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                url,
                headers=_auth_headers(access_token),
                params={"per_page": 1},
            )
    except httpx.HTTPError as exc:
        logger.exception("GitHub commit resolve failed for %s@%s", full_name, ref)
        raise GitHubOAuthError("Could not reach GitHub commits endpoint") from exc

    _raise_for_github_status(response, f"resolve commit for {full_name}@{ref}")
    payload = response.json()
    sha = payload.get("sha") if isinstance(payload, dict) else None
    if not isinstance(sha, str) or not sha:
        raise GitHubOAuthError("Unexpected GitHub commit response")
    return sha


def get_repository_tree(
    access_token: str, full_name: str, ref: str, *, recursive: bool = True
) -> dict[str, Any]:
    """
    List files via the Git Trees API.

    ``ref`` may be a branch name or commit/tree SHA.
    Returns ``{sha, truncated, tree: [{path, type, sha, size}, ...]}``.
    """
    url = f"{GITHUB_API}/repos/{full_name}/git/trees/{ref}"
    params = {"recursive": "1"} if recursive else None
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(
                url, headers=_auth_headers(access_token), params=params
            )
    except httpx.HTTPError as exc:
        logger.exception("GitHub tree request failed for %s@%s", full_name, ref)
        raise GitHubOAuthError("Could not reach GitHub trees endpoint") from exc

    _raise_for_github_status(response, f"list tree for {full_name}@{ref}")
    payload = response.json()
    if not isinstance(payload, dict) or "tree" not in payload:
        raise GitHubOAuthError("Unexpected GitHub tree response")

    tree_items: list[dict[str, Any]] = []
    for item in payload.get("tree") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "blob":
            continue
        path = item.get("path")
        sha = item.get("sha")
        if not isinstance(path, str) or not isinstance(sha, str):
            continue
        size = item.get("size")
        tree_items.append(
            {
                "path": path,
                "type": "blob",
                "sha": sha,
                "size": int(size) if isinstance(size, int) else None,
            }
        )

    return {
        "sha": str(payload.get("sha") or ""),
        "truncated": bool(payload.get("truncated", False)),
        "tree": tree_items,
    }


class NonTextBlobError(Exception):
    """Blob is not usable text (binary / bad encoding). Caller may skip."""


def get_blob_text(access_token: str, full_name: str, blob_sha: str) -> str:
    """Fetch a git blob and decode UTF-8 text (base64 from GitHub)."""
    url = f"{GITHUB_API}/repos/{full_name}/git/blobs/{blob_sha}"
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(url, headers=_auth_headers(access_token))
    except httpx.HTTPError as exc:
        logger.exception("GitHub blob request failed for %s sha=%s", full_name, blob_sha[:12])
        raise GitHubOAuthError("Could not reach GitHub blobs endpoint") from exc

    _raise_for_github_status(response, f"fetch blob {blob_sha[:12]}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise GitHubOAuthError("Unexpected GitHub blob response")

    encoding = payload.get("encoding")
    content = payload.get("content")
    if encoding != "base64" or not isinstance(content, str):
        raise NonTextBlobError("Unsupported GitHub blob encoding")

    try:
        raw = base64.b64decode(content, validate=False)
    except Exception as exc:  # noqa: BLE001 — treat as skippable
        raise NonTextBlobError("Could not decode GitHub blob content") from exc

    if b"\x00" in raw:
        raise NonTextBlobError("Blob appears binary")

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


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
