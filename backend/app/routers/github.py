"""GitHub OAuth connect routes (backend only for Day 11)."""

from __future__ import annotations

import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.crypto import encrypt_secret
from app.deps import CurrentUser, DbSession, get_current_user
from app.models import GitHubAccount, User
from app.schemas.github import GitHubConnectionResponse
from app.services.github_oauth import (
    GitHubOAuthError,
    build_authorize_url,
    create_oauth_state,
    exchange_code_for_token,
    fetch_github_user,
    parse_oauth_state,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/github", tags=["github-oauth"])


def _require_github_config() -> None:
    settings = get_settings()
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured (missing client id/secret)",
        )
    if not settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SECRET_KEY is required to store GitHub tokens securely",
        )


@router.get("/start")
def github_oauth_start(current_user: CurrentUser) -> RedirectResponse:
    """Begin GitHub OAuth for the signed-in user (browser navigation)."""
    _require_github_config()
    settings = get_settings()
    state = create_oauth_state(settings, str(current_user.id))
    url = build_authorize_url(settings, state)
    logger.info("Starting GitHub OAuth for user_id=%s", current_user.id)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/callback")
def github_oauth_callback(
    request: Request,
    db: DbSession,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Complete OAuth, store encrypted token, redirect to the frontend."""
    settings = get_settings()
    frontend = settings.frontend_url.rstrip("/")

    def redirect_with(query: str) -> RedirectResponse:
        return RedirectResponse(url=f"{frontend}/app?{query}", status_code=status.HTTP_302_FOUND)

    if error:
        logger.warning("GitHub OAuth cancelled or denied: error=%s", error)
        return redirect_with("github=denied")

    if not code or not state:
        return redirect_with("github=missing_params")

    try:
        _require_github_config()
        user_id = UUID(parse_oauth_state(settings, state))
    except HTTPException:
        return redirect_with("github=not_configured")
    except (GitHubOAuthError, ValueError) as exc:
        logger.warning("GitHub OAuth state rejected: %s", exc)
        return redirect_with("github=invalid_state")

    try:
        session_user = get_current_user(request, db)
        if session_user.id != user_id:
            logger.warning("GitHub OAuth state user mismatch")
            return redirect_with("github=user_mismatch")
    except HTTPException:
        logger.info("GitHub OAuth callback without session cookie; using state user_id")

    user = db.get(User, user_id)
    if user is None:
        return redirect_with("github=user_not_found")

    try:
        token_payload = exchange_code_for_token(settings, code)
        plaintext_token = token_payload["access_token"]
        profile = fetch_github_user(plaintext_token)
        encrypted = encrypt_secret(plaintext_token, settings.secret_key)
        # Clear plaintext as soon as we have ciphertext.
        plaintext_token = ""
        token_payload["access_token"] = ""
    except GitHubOAuthError as exc:
        logger.error("GitHub OAuth failed: %s", exc)
        return redirect_with("github=exchange_failed")

    existing = db.scalar(select(GitHubAccount).where(GitHubAccount.user_id == user_id))
    if existing is None:
        db.add(
            GitHubAccount(
                id=uuid4(),
                user_id=user_id,
                github_user_id=profile["id"],
                github_login=profile["login"],
                access_token_encrypted=encrypted,
                token_type=token_payload.get("token_type") or "bearer",
                scope=token_payload.get("scope"),
            )
        )
    else:
        existing.github_user_id = profile["id"]
        existing.github_login = profile["login"]
        existing.access_token_encrypted = encrypted
        existing.token_type = token_payload.get("token_type") or "bearer"
        existing.scope = token_payload.get("scope")

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.error("GitHub account uniqueness conflict for user_id=%s", user_id)
        return redirect_with("github=conflict")

    logger.info(
        "GitHub account linked user_id=%s github_login=%s",
        user_id,
        profile["login"],
    )
    return redirect_with("github=connected")


@router.get("/connection", response_model=GitHubConnectionResponse)
def github_connection(current_user: CurrentUser, db: DbSession) -> GitHubConnectionResponse:
    """Return connection metadata — never includes the access token."""
    account = db.scalar(select(GitHubAccount).where(GitHubAccount.user_id == current_user.id))
    if account is None:
        return GitHubConnectionResponse(connected=False)
    return GitHubConnectionResponse(
        connected=True,
        github_user_id=account.github_user_id,
        github_login=account.github_login,
        scope=account.scope,
    )
