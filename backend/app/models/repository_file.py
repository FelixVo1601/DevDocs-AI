"""Source files discovered during repository ingestion."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.code_chunk import CodeChunk
    from app.models.selected_repository import SelectedRepository


class RepositoryFile(Base, TimestampMixin):
    """One indexed source/doc file belonging to a selected repository."""

    __tablename__ = "repository_files"
    __table_args__ = (
        UniqueConstraint(
            "selected_repository_id",
            "path",
            name="uq_repository_files_repo_path",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    selected_repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("selected_repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    # Git blob SHA when available.
    content_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Optional denormalized line count after processing.
    line_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    selected_repository: Mapped[SelectedRepository] = relationship(
        back_populates="files"
    )
    chunks: Mapped[list[CodeChunk]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
    )
