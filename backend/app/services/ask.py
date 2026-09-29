"""Grounded answers: retrieve chunks, prompt an LLM, return citations."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.chat_client import ChatClient, ChatError
from app.services.embeddings_client import EmbeddingsClient
from app.services.retrieve import DEFAULT_TOP_K, retrieve_similar_chunks

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You answer questions about a software repository using only the retrieved "
    "code excerpts. If the excerpts do not contain the answer, say you cannot "
    "tell from the indexed code. Mention citation numbers like [1] when you "
    "use an excerpt. Do not invent files or behavior that is not in the excerpts."
)


def _format_context(hits: list[dict]) -> str:
    blocks: list[str] = []
    for index, hit in enumerate(hits, start=1):
        start = hit.get("start_line")
        end = hit.get("end_line")
        span = f":{start}-{end}" if start and end else ""
        blocks.append(
            f"[{index}] {hit['path']}{span} (chunk {hit['chunk_id']})\n{hit['content']}"
        )
    return "\n\n".join(blocks)


def ask_question(
    db: Session,
    user_id: UUID,
    question: str,
    *,
    k: int = DEFAULT_TOP_K,
    embeddings_client: EmbeddingsClient | None = None,
    chat_client: ChatClient | None = None,
) -> dict:
    """Retrieve top-k chunks, prompt the chat model, and attach citation metadata."""
    retrieved = retrieve_similar_chunks(
        db,
        user_id,
        question,
        k=k,
        client=embeddings_client,
    )
    hits = retrieved["hits"]
    if not hits:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No chunks matched the question. Index the repository first.",
        )

    try:
        client = chat_client or ChatClient()
    except ChatError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Repository: {retrieved['full_name']}\n\n"
                f"Excerpts:\n{_format_context(hits)}\n\n"
                f"Question: {retrieved['question']}"
            ),
        },
    ]
    try:
        answer = client.complete(messages)
    except ChatError as exc:
        logger.error("Ask failed user_id=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    citations = [
        {
            "chunk_id": hit["chunk_id"],
            "path": hit["path"],
            "chunk_index": hit["chunk_index"],
            "start_line": hit["start_line"],
            "end_line": hit["end_line"],
            "distance": hit["distance"],
        }
        for hit in hits
    ]
    logger.info(
        "Answered question user_id=%s full_name=%s citations=%s",
        user_id,
        retrieved["full_name"],
        [item["path"] for item in citations],
    )
    return {
        "full_name": retrieved["full_name"],
        "question": retrieved["question"],
        "answer": answer,
        "model": client.model,
        "citations": citations,
    }
