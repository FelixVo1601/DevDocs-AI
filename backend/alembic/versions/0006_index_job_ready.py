"""rename index_job_status succeeded → ready

Revision ID: 0006_index_job_ready
Revises: 0005_pgvector
Create Date: 2026-09-26 17:50:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006_index_job_ready"
down_revision: str | None = "0005_pgvector"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # PostgreSQL 10+: rename enum label in place (keeps existing rows valid).
    op.execute("ALTER TYPE index_job_status RENAME VALUE 'succeeded' TO 'ready'")


def downgrade() -> None:
    op.execute("ALTER TYPE index_job_status RENAME VALUE 'ready' TO 'succeeded'")
