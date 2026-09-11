"""Indexing job status for a selected repository."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.selected_repository import SelectedRepository


class IndexJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class IndexJob(Base, TimestampMixin):
    """Tracks one ingestion/index run for a selected repository."""

    __tablename__ = "index_jobs"

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
    status: Mapped[IndexJobStatus] = mapped_column(
        Enum(
            IndexJobStatus,
            name="index_job_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=IndexJobStatus.PENDING,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Optional commit SHA being indexed (filled by ingestion later).
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)

    selected_repository: Mapped[SelectedRepository] = relationship(
        back_populates="index_jobs"
    )
