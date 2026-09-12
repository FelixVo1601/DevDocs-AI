"""Fetch selected-repository file list + content from GitHub and persist."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    CodeChunk,
    IndexJob,
    IndexJobStatus,
    RepositoryFile,
    SelectedRepository,
)
from app.services.github_api import (
    NonTextBlobError,
    get_blob_text,
    get_branch_commit_sha,
    get_repository_tree,
)
from app.services.github_oauth import GitHubOAuthError
from app.services.github_tokens import get_github_access_token
from app.services.repo_filters import (
    MAX_FILES_PER_FETCH,
    guess_language,
    should_include_path,
)

logger = logging.getLogger(__name__)


def fetch_selected_repository_contents(db: Session, user_id: UUID) -> dict:
    """
    Pull filtered source/docs from the user's selected repo.

    Creates an ``index_jobs`` row, replaces ``repository_files`` (+ content as
    a single ``code_chunks`` row per file for later processing), and returns a
    summary including file paths and content.
    """
    selected = db.scalar(
        select(SelectedRepository).where(SelectedRepository.user_id == user_id)
    )
    if selected is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No repository selected. Select a repository first.",
        )

    job = IndexJob(
        id=uuid4(),
        selected_repository_id=selected.id,
        status=IndexJobStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.flush()

    access_token = get_github_access_token(db, user_id)
    files_out: list[dict] = []
    try:
        commit_sha = get_branch_commit_sha(
            access_token, selected.full_name, selected.default_branch
        )
        job.commit_sha = commit_sha

        tree = get_repository_tree(
            access_token, selected.full_name, commit_sha, recursive=True
        )
        if tree.get("truncated"):
            raise GitHubOAuthError(
                "Repository tree is truncated; choose a smaller repo for MVP fetch"
            )

        candidates = [
            item
            for item in tree["tree"]
            if should_include_path(item["path"], item.get("size"))
        ]
        candidates.sort(key=lambda item: item["path"])
        skipped_over_cap = max(0, len(candidates) - MAX_FILES_PER_FETCH)
        candidates = candidates[:MAX_FILES_PER_FETCH]

        # Replace previous file snapshot for this selection.
        db.execute(
            delete(RepositoryFile).where(
                RepositoryFile.selected_repository_id == selected.id
            )
        )
        db.flush()

        for item in candidates:
            path = item["path"]
            blob_sha = item["sha"]
            try:
                content = get_blob_text(access_token, selected.full_name, blob_sha)
            except NonTextBlobError as exc:
                logger.warning(
                    "Skipping non-text %s path=%s: %s",
                    selected.full_name,
                    path,
                    exc,
                )
                continue

            line_count = len(content.splitlines()) if content else 0

            file_row = RepositoryFile(
                id=uuid4(),
                selected_repository_id=selected.id,
                path=path,
                content_sha=blob_sha,
                language=guess_language(path),
                size_bytes=item.get("size") if item.get("size") is not None else len(
                    content.encode("utf-8")
                ),
                line_count=line_count,
            )
            db.add(file_row)
            db.flush()

            db.add(
                CodeChunk(
                    id=uuid4(),
                    file_id=file_row.id,
                    chunk_index=0,
                    start_line=1 if line_count else None,
                    end_line=line_count if line_count else None,
                    content=content,
                    token_count=None,
                )
            )

            files_out.append(
                {
                    "path": path,
                    "content_sha": blob_sha,
                    "language": file_row.language,
                    "size_bytes": file_row.size_bytes,
                    "line_count": file_row.line_count,
                    "content": content,
                }
            )

        job.status = IndexJobStatus.SUCCEEDED
        job.finished_at = datetime.now(timezone.utc)
        job.error_message = None
        db.commit()
        db.refresh(job)

        logger.info(
            "Fetched repo contents user_id=%s full_name=%s files=%s skipped_cap=%s",
            user_id,
            selected.full_name,
            len(files_out),
            skipped_over_cap,
        )
        return {
            "job_id": str(job.id),
            "status": job.status.value,
            "full_name": selected.full_name,
            "ref": selected.default_branch,
            "commit_sha": commit_sha,
            "file_count": len(files_out),
            "skipped_over_cap": skipped_over_cap,
            "files": files_out,
        }
    except GitHubOAuthError as exc:
        logger.error(
            "Fetch failed user_id=%s full_name=%s: %s",
            user_id,
            selected.full_name,
            exc,
        )
        job.status = IndexJobStatus.FAILED
        job.finished_at = datetime.now(timezone.utc)
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Unexpected fetch failure user_id=%s full_name=%s",
            user_id,
            selected.full_name,
        )
        job.status = IndexJobStatus.FAILED
        job.finished_at = datetime.now(timezone.utc)
        job.error_message = "Unexpected error while fetching repository contents"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while fetching repository contents",
        ) from exc
    finally:
        access_token = ""
