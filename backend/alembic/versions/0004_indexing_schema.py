"""create index_jobs, repository_files, and code_chunks tables

Revision ID: 0004_indexing_schema
Revises: 0003_selected_repositories
Create Date: 2026-09-10 20:55:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_indexing_schema"
down_revision: str | None = "0003_selected_repositories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# create_type=False: we create/drop the PG enum explicitly so create_table
# does not attempt a second CREATE TYPE.
index_job_status = postgresql.ENUM(
    "pending",
    "running",
    "succeeded",
    "failed",
    name="index_job_status",
    create_type=False,
)


def upgrade() -> None:
    index_job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "index_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("selected_repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            index_job_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["selected_repository_id"],
            ["selected_repositories.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_index_jobs_selected_repository_id"),
        "index_jobs",
        ["selected_repository_id"],
        unique=False,
    )
    op.create_index(op.f("ix_index_jobs_status"), "index_jobs", ["status"], unique=False)

    op.create_table(
        "repository_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("selected_repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("content_sha", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("line_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["selected_repository_id"],
            ["selected_repositories.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "selected_repository_id",
            "path",
            name="uq_repository_files_repo_path",
        ),
    )
    op.create_index(
        op.f("ix_repository_files_selected_repository_id"),
        "repository_files",
        ["selected_repository_id"],
        unique=False,
    )

    op.create_table(
        "code_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["file_id"], ["repository_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "file_id",
            "chunk_index",
            name="uq_code_chunks_file_chunk_index",
        ),
    )
    op.create_index(op.f("ix_code_chunks_file_id"), "code_chunks", ["file_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_code_chunks_file_id"), table_name="code_chunks")
    op.drop_table("code_chunks")
    op.drop_index(
        op.f("ix_repository_files_selected_repository_id"),
        table_name="repository_files",
    )
    op.drop_table("repository_files")
    op.drop_index(op.f("ix_index_jobs_status"), table_name="index_jobs")
    op.drop_index(op.f("ix_index_jobs_selected_repository_id"), table_name="index_jobs")
    op.drop_table("index_jobs")
    index_job_status.drop(op.get_bind(), checkfirst=True)
