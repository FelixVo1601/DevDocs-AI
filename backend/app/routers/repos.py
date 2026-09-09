"""GitHub repository listing for connected users."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, DbSession
from app.schemas.github import GitHubRepoListResponse
from app.services.github_api import list_user_repositories
from app.services.github_oauth import GitHubOAuthError
from app.services.github_tokens import get_github_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/repos", response_model=GitHubRepoListResponse)
def list_repos(current_user: CurrentUser, db: DbSession) -> GitHubRepoListResponse:
    """
    List repositories visible to the connected GitHub account
    (public and accessible private).
    """
    access_token = get_github_access_token(db, current_user.id)
    try:
        repos = list_user_repositories(access_token)
    except GitHubOAuthError as exc:
        logger.error("Failed to list repos for user_id=%s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    finally:
        access_token = ""

    return GitHubRepoListResponse(repos=repos, count=len(repos))
