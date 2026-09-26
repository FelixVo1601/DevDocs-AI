"""Orchestrate sync index jobs: fetch → chunk → embed → ready/failed."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    CodeChunk,
    IndexJob,
    IndexJobStatus,
    RepositoryFile,
    SelectedRepository,
)
from app.services.embed_repo import embed_selected_repository_chunks
from app.services.embeddings_client import EmbeddingsClient
from app.services.fetch_repo import fetch_and_store_contents
from app.services.github_oauth import GitHubOAuthError
from app.services.github_tokens import get_github_access_token

logger = logging.getLogger(__name__)


def _selected_or_400(db: Session, user_id: UUID) -> SelectedRepository:
    selected = db.scalar(
        select(SelectedRepository).where(SelectedRepository.user_id == user_id)
    )
    if selected is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No repository selected. Select a repository first.",
        )
    return selected


def _counts_for_repo(db: Session, selected_id: UUID) -> dict[str, int]:
    file_count = db.scalar(
        select(func.count())
        .select_from(RepositoryFile)
        .where(RepositoryFile.selected_repository_id == selected_id)
    )
    chunk_count = db.scalar(
        select(func.count())
        .select_from(CodeChunk)
        .join(RepositoryFile, CodeChunk.file_id == RepositoryFile.id)
        .where(RepositoryFile.selected_repository_id == selected_id)
    )
    embedded_count = db.scalar(
        select(func.count())
        .select_from(CodeChunk)
        .join(RepositoryFile, CodeChunk.file_id == RepositoryFile.id)
        .where(
            RepositoryFile.selected_repository_id == selected_id,
            CodeChunk.embedding.is_not(None),
        )
    )
    return {
        "file_count": int(file_count or 0),
        "chunk_count": int(chunk_count or 0),
        "embedded_count": int(embedded_count or 0),
    }


def _job_payload(
    job: IndexJob | None,
    selected: SelectedRepository | None,
    counts: dict[str, int] | None = None,
) -> dict:
    counts = counts or {"file_count": 0, "chunk_count": 0, "embedded_count": 0}
    if selected is None:
        return {
            "selected": None,
            "job": None,
            **counts,
        }
    if job is None:
        return {
            "selected": {
                "full_name": selected.full_name,
                "default_branch": selected.default_branch,
            },
            "job": None,
            **counts,
        }
    return {
        "selected": {
            "full_name": selected.full_name,
            "default_branch": selected.default_branch,
        },
        "job": {
            "id": str(job.id),
            "status": job.status.value,
            "error_message": job.error_message,
            "commit_sha": job.commit_sha,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        },
        **counts,
    }


def get_index_status(db: Session, user_id: UUID) -> dict:
    """Latest index job + snapshot counts for the selected repository."""
    selected = db.scalar(
        select(SelectedRepository).where(SelectedRepository.user_id == user_id)
    )
    if selected is None:
        return _job_payload(None, None)

    job = db.scalar(
        select(IndexJob)
        .where(IndexJob.selected_repository_id == selected.id)
        .order_by(IndexJob.created_at.desc())
        .limit(1)
    )
    return _job_payload(job, selected, _counts_for_repo(db, selected.id))


def index_selected_repository(
    db: Session,
    user_id: UUID,
    *,
    embeddings_client: EmbeddingsClient | None = None,
) -> dict:
    """
    Synchronous MVP index: pending → running → fetch/chunk → embed → ready|failed.
    """
    selected = _selected_or_400(db, user_id)

    job = IndexJob(
        id=uuid4(),
        selected_repository_id=selected.id,
        status=IndexJobStatus.PENDING,
    )
    db.add(job)
    db.flush()

    job.status = IndexJobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)
    job.error_message = None
    db.flush()

    access_token = ""
    try:
        access_token = get_github_access_token(db, user_id)
        fetch_result = fetch_and_store_contents(db, selected, access_token)
        job.commit_sha = fetch_result["commit_sha"]
        db.flush()

        if fetch_result["file_count"] == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No indexable files found in the selected repository.",
            )

        embed_result = embed_selected_repository_chunks(
            db,
            user_id,
            force=True,
            client=embeddings_client,
            commit=False,
        )

        job.status = IndexJobStatus.READY
        job.finished_at = datetime.now(timezone.utc)
        job.error_message = None
        db.commit()
        db.refresh(job)

        counts = _counts_for_repo(db, selected.id)
        logger.info(
            "Index ready user_id=%s full_name=%s files=%s chunks=%s embedded=%s",
            user_id,
            selected.full_name,
            counts["file_count"],
            counts["chunk_count"],
            embed_result["embedded"],
        )
        payload = _job_payload(job, selected, counts)
        payload["embedded"] = embed_result["embedded"]
        payload["skipped_empty"] = embed_result["skipped_empty"]
        payload["truncated"] = embed_result["truncated"]
        return payload
    except HTTPException as exc:
        job.status = IndexJobStatus.FAILED
        job.finished_at = datetime.now(timezone.utc)
        job.error_message = str(exc.detail)
        db.commit()
        raise
    except GitHubOAuthError as exc:
        logger.error(
            "Index failed user_id=%s full_name=%s: %s",
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
            "Unexpected index failure user_id=%s full_name=%s",
            user_id,
            selected.full_name,
        )
        job.status = IndexJobStatus.FAILED
        job.finished_at = datetime.now(timezone.utc)
        job.error_message = "Unexpected error while indexing repository"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while indexing repository",
        ) from exc
    finally:
        access_token = ""
