"""Semantic search over embedded chunks for the selected repository."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CodeChunk, RepositoryFile, SelectedRepository
from app.services.embeddings_client import (
    EmbeddingsClient,
    EmbeddingsError,
    prepare_embedding_text,
)

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
MAX_TOP_K = 20


def retrieve_similar_chunks(
    db: Session,
    user_id: UUID,
    question: str,
    *,
    k: int = DEFAULT_TOP_K,
    client: EmbeddingsClient | None = None,
) -> dict:
    """
    Embed ``question`` and return the ``k`` nearest chunks for the selected repo.

    Similarity is cosine distance (pgvector ``<=>``). Only chunks that already
    have embeddings are considered.
    """
    text = prepare_embedding_text(question)
    if text is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is empty.",
        )
    if k < 1 or k > MAX_TOP_K:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"k must be between 1 and {MAX_TOP_K}.",
        )

    selected = db.scalar(
        select(SelectedRepository).where(SelectedRepository.user_id == user_id)
    )
    if selected is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No repository selected. Select a repository first.",
        )

    embedded_count = db.scalar(
        select(CodeChunk.id)
        .join(RepositoryFile, CodeChunk.file_id == RepositoryFile.id)
        .where(
            RepositoryFile.selected_repository_id == selected.id,
            CodeChunk.embedding.is_not(None),
        )
        .limit(1)
    )
    if embedded_count is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No embeddings for the selected repository. Index it first.",
        )

    try:
        embeddings_client = client or EmbeddingsClient()
        vector = embeddings_client.embed_texts([text])[0]
    except EmbeddingsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST
            if "OPENAI_API_KEY" in str(exc)
            else status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    distance = CodeChunk.embedding.cosine_distance(vector)
    rows = db.execute(
        select(RepositoryFile.path, CodeChunk, distance.label("distance"))
        .join(RepositoryFile, CodeChunk.file_id == RepositoryFile.id)
        .where(
            RepositoryFile.selected_repository_id == selected.id,
            CodeChunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(k)
    ).all()

    hits = [
        {
            "path": path,
            "chunk_index": chunk.chunk_index,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "content": chunk.content,
            "distance": float(dist),
        }
        for path, chunk, dist in rows
    ]

    logger.info(
        "Retrieved chunks user_id=%s full_name=%s k=%s hits=%s paths=%s",
        user_id,
        selected.full_name,
        k,
        len(hits),
        [hit["path"] for hit in hits],
    )
    return {
        "full_name": selected.full_name,
        "question": text,
        "k": k,
        "hits": hits,
    }
