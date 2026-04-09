"""add project urls and portfolio views

Revision ID: d1b8e4c9f2a1
Revises: c73c0a6b9f5f
Create Date: 2026-04-09 20:35:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d1b8e4c9f2a1"
down_revision: str | None = "c73c0a6b9f5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("github_url", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("live_url", sa.Text(), nullable=True))

    op.create_table(
        "portfolio_views",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_portfolio_views_user_id"),
        "portfolio_views",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_portfolio_views_user_id"), table_name="portfolio_views")
    op.drop_table("portfolio_views")
    op.drop_column("projects", "live_url")
    op.drop_column("projects", "github_url")
