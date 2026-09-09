"""Helpers to load a connected user's GitHub credentials. Never log tokens."""

from __future__ import annotations

from uuid import UUID

from cryptography.fernet import InvalidToken
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.crypto import decrypt_secret
from app.models import GitHubAccount


def get_connected_github_account(db: Session, user_id: UUID) -> GitHubAccount:
    account = db.scalar(select(GitHubAccount).where(GitHubAccount.user_id == user_id))
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub is not connected. Connect GitHub first.",
        )
    return account


def get_github_access_token(db: Session, user_id: UUID) -> str:
    settings = get_settings()
    account = get_connected_github_account(db, user_id)
    try:
        return decrypt_secret(account.access_token_encrypted, settings.secret_key)
    except InvalidToken as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored GitHub token could not be decrypted. Reconnect GitHub.",
        ) from exc
