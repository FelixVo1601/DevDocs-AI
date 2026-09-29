"""Grounded question answering for the selected repository."""

from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUser, DbSession
from app.schemas.ask import AskRequest, AskResponse
from app.services.ask import ask_question

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> AskResponse:
    """
    Retrieve similar chunks, prompt an LLM with that context, and return
    the answer plus citation metadata (file path and chunk id).
    """
    result = ask_question(db, current_user.id, payload.question, k=payload.k)
    return AskResponse.model_validate(result)
