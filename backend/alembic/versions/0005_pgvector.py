"""create pgvector extension and code_chunks.embedding column

Revision ID: 0005_pgvector
Revises: 0004_indexing_schema
Create Date: 2026-09-19 22:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.embedding_config import EMBEDDING_DIMENSIONS

revision: str = "0005_pgvector"
down_revision: str | None = "0004_indexing_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        sa.text(
            f"ALTER TABLE code_chunks "
            f"ADD COLUMN embedding vector({EMBEDDING_DIMENSIONS})"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE code_chunks DROP COLUMN IF EXISTS embedding"))
    # Leave the extension installed; other objects may depend on it.