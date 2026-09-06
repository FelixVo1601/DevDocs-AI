"""FastAPI dependencies."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Session as AuthSession
from app.models import User
from app.security import hash_session_token

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, db: DbSession) -> User:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token_hash = hash_session_token(token)
    now = datetime.now(UTC)
    stmt = (
        select(AuthSession)
        .where(AuthSession.token_hash == token_hash)
        .where(AuthSession.revoked_at.is_(None))
        .where(AuthSession.expires_at > now)
    )
    auth_session = db.scalar(stmt)
    if auth_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    user = db.get(User, auth_session.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session user",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
