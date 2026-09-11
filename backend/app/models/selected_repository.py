"""Per-user selected GitHub repository (one at a time)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.index_job import IndexJob
    from app.models.repository_file import RepositoryFile
    from app.models.user import User


class SelectedRepository(Base, TimestampMixin):
    __tablename__ = "selected_repositories"
    __table_args__ = (UniqueConstraint("user_id", name="uq_selected_repositories_user_id"),)

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
    github_repo_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False)
    private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    html_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), nullable=False, default="main")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="selected_repository")
    index_jobs: Mapped[list[IndexJob]] = relationship(
        back_populates="selected_repository",
        cascade="all, delete-orphan",
    )
    files: Mapped[list[RepositoryFile]] = relationship(
        back_populates="selected_repository",
        cascade="all, delete-orphan",
    )
