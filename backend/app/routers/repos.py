"""GitHub repository listing and selection for connected users."""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models import SelectedRepository
from app.schemas.github import (
    FetchRepositoryContentsResponse,
    GitHubRepoListResponse,
    SelectedRepositoryEnvelope,
    SelectedRepositoryResponse,
    SelectRepositoryRequest,
)
from app.services.fetch_repo import fetch_selected_repository_contents
from app.services.github_api import get_repository_by_id, list_user_repositories
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


@router.get("/selected-repo", response_model=SelectedRepositoryEnvelope)
def get_selected_repo(
    current_user: CurrentUser, db: DbSession
) -> SelectedRepositoryEnvelope:
    row = db.scalar(
        select(SelectedRepository).where(SelectedRepository.user_id == current_user.id)
    )
    if row is None:
        return SelectedRepositoryEnvelope(selected=None)
    return SelectedRepositoryEnvelope(
        selected=SelectedRepositoryResponse.model_validate(row)
    )


@router.put("/selected-repo", response_model=SelectedRepositoryEnvelope)
def select_repo(
    payload: SelectRepositoryRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> SelectedRepositoryEnvelope:
    """Persist one selected repository per user (verified via GitHub API)."""
    access_token = get_github_access_token(db, current_user.id)
    try:
        repo = get_repository_by_id(access_token, payload.github_repo_id)
    except GitHubOAuthError as exc:
        logger.error(
            "Failed to verify repo %s for user_id=%s: %s",
            payload.github_repo_id,
            current_user.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    finally:
        access_token = ""

    row = db.scalar(
        select(SelectedRepository).where(SelectedRepository.user_id == current_user.id)
    )
    if row is None:
        row = SelectedRepository(id=uuid4(), user_id=current_user.id)
        db.add(row)

    row.github_repo_id = repo["id"]
    row.name = repo["name"]
    row.full_name = repo["full_name"]
    row.private = repo["private"]
    row.html_url = repo["html_url"]
    row.default_branch = repo["default_branch"]
    row.description = repo.get("description")
    db.commit()
    db.refresh(row)

    logger.info(
        "Selected repo user_id=%s full_name=%s",
        current_user.id,
        row.full_name,
    )
    return SelectedRepositoryEnvelope(
        selected=SelectedRepositoryResponse.model_validate(row)
    )


@router.post(
    "/selected-repo/fetch",
    response_model=FetchRepositoryContentsResponse,
)
def fetch_selected_repo_contents(
    current_user: CurrentUser, db: DbSession
) -> FetchRepositoryContentsResponse:
    """
    Fetch filtered file list + content for the selected repository.

    Uses GitHub Trees + Blobs APIs (no clone). Stores ``repository_files`` and
    full-file ``code_chunks`` (chunk_index=0) for later processing.
    """
    result = fetch_selected_repository_contents(db, current_user.id)
    return FetchRepositoryContentsResponse.model_validate(result)
