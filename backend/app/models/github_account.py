"""GitHub account link for a DevDocs user."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class GitHubAccount(Base, TimestampMixin):
    """Stores encrypted GitHub OAuth token metadata linked to a local user."""

    __tablename__ = "github_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_github_accounts_user_id"),
        UniqueConstraint("github_user_id", name="uq_github_accounts_github_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    github_login: Mapped[str] = mapped_column(String(255), nullable=False)
    # Fernet ciphertext — never log or return this field from the API.
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    token_type: Mapped[str] = mapped_column(String(64), nullable=False, default="bearer")
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="github_account")
