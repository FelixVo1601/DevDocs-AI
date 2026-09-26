"""Embed stored code chunks for the user's selected repository."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.embedding_config import EMBEDDING_BATCH_SIZE
from app.models import CodeChunk, RepositoryFile, SelectedRepository
from app.services.embeddings_client import (
    EmbeddingsClient,
    EmbeddingsError,
    prepare_embedding_text,
)

logger = logging.getLogger(__name__)


def embed_selected_repository_chunks(
    db: Session,
    user_id: UUID,
    *,
    force: bool = False,
    client: EmbeddingsClient | None = None,
    commit: bool = True,
) -> dict:
    """
    Write embeddings into ``code_chunks.embedding`` for the selected repo.

    Skips empty/whitespace chunks. Truncates oversized text. By default only
    fills rows where ``embedding`` is NULL unless ``force`` is True.

    When ``commit`` is False, changes are flushed only — the caller owns the
    transaction (used by the full index orchestrator).
    """
    selected = db.scalar(
        select(SelectedRepository).where(SelectedRepository.user_id == user_id)
    )
    if selected is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No repository selected. Select a repository first.",
        )

    files = db.scalars(
        select(RepositoryFile)
        .where(RepositoryFile.selected_repository_id == selected.id)
        .options(selectinload(RepositoryFile.chunks))
        .order_by(RepositoryFile.path)
    ).all()

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files fetched for the selected repository. Run fetch first.",
        )

    try:
        embeddings_client = client or EmbeddingsClient()
    except EmbeddingsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    skipped_empty = 0
    skipped_existing = 0
    truncated = 0
    prepared: list[tuple[CodeChunk, str]] = []

    for file_row in files:
        for chunk in sorted(file_row.chunks, key=lambda c: c.chunk_index):
            if chunk.embedding is not None and not force:
                skipped_existing += 1
                continue
            text = prepare_embedding_text(chunk.content)
            if text is None:
                skipped_empty += 1
                continue
            if len(chunk.content.strip()) > len(text):
                truncated += 1
            prepared.append((chunk, text))

    embedded = 0
    try:
        for start in range(0, len(prepared), EMBEDDING_BATCH_SIZE):
            batch = prepared[start : start + EMBEDDING_BATCH_SIZE]
            texts = [text for _, text in batch]
            vectors = embeddings_client.embed_texts(texts)
            for (chunk, _), vector in zip(batch, vectors, strict=True):
                chunk.embedding = vector
                embedded += 1
        if commit:
            db.commit()
        else:
            db.flush()
    except EmbeddingsError as exc:
        if commit:
            db.rollback()
        logger.error(
            "Embed failed user_id=%s full_name=%s: %s",
            user_id,
            selected.full_name,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        if commit:
            db.rollback()
        logger.exception(
            "Unexpected embed failure user_id=%s full_name=%s",
            user_id,
            selected.full_name,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while generating embeddings",
        ) from exc

    logger.info(
        "Embedded chunks user_id=%s full_name=%s embedded=%s skipped_empty=%s "
        "skipped_existing=%s truncated=%s",
        user_id,
        selected.full_name,
        embedded,
        skipped_empty,
        skipped_existing,
        truncated,
    )
    return {
        "full_name": selected.full_name,
        "model": embeddings_client.model,
        "embedded": embedded,
        "skipped_empty": skipped_empty,
        "skipped_existing": skipped_existing,
        "truncated": truncated,
        "force": force,
    }
