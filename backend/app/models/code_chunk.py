"""Text chunks produced from repository files (with optional pgvector embeddings)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.embedding_config import EMBEDDING_DIMENSIONS
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.repository_file import RepositoryFile


class CodeChunk(Base, TimestampMixin):
    """
    Retrieval unit for RAG.

    ``embedding`` is nullable until an embedding job fills it (Day 20+).
    """

    __tablename__ = "code_chunks"
    __table_args__ = (
        UniqueConstraint(
            "file_id",
            "chunk_index",
            name="uq_code_chunks_file_chunk_index",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS),
        nullable=True,
    )

    file: Mapped[RepositoryFile] = relationship(back_populates="chunks")
