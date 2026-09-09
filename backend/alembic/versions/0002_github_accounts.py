"""create github_accounts table

Revision ID: 0002_github_accounts
Revises: 0001_users_sessions
Create Date: 2026-09-09 01:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_github_accounts"
down_revision: str | None = "0001_users_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "github_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_user_id", sa.BigInteger(), nullable=False),
        sa.Column("github_login", sa.String(length=255), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("token_type", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_github_accounts_user_id"),
        sa.UniqueConstraint("github_user_id", name="uq_github_accounts_github_user_id"),
    )
    op.create_index(op.f("ix_github_accounts_user_id"), "github_accounts", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_github_accounts_github_user_id"),
        "github_accounts",
        ["github_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_github_accounts_github_user_id"), table_name="github_accounts")
    op.drop_index(op.f("ix_github_accounts_user_id"), table_name="github_accounts")
    op.drop_table("github_accounts")
