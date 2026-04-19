"""refactor portfolio views to visitors

Revision ID: c6f4d7b8a2d1
Revises: 3e7f2a1b4c8d
Create Date: 2026-04-19 16:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c6f4d7b8a2d1"
down_revision: str | None = "3e7f2a1b4c8d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.rename_table("portfolio_views", "portfolio_visitors")
    op.drop_index(op.f("ix_portfolio_views_user_id"), table_name="portfolio_visitors")
    op.alter_column(
        "portfolio_visitors",
        "path",
        new_column_name="last_path",
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )
    op.add_column("portfolio_visitors", sa.Column("visitor_id", sa.String(length=128), nullable=True))
    op.add_column(
        "portfolio_visitors",
        sa.Column(
            "first_visited_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.add_column(
        "portfolio_visitors",
        sa.Column(
            "last_visited_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.add_column(
        "portfolio_visitors",
        sa.Column("visit_count", sa.Integer(), server_default="1", nullable=True),
    )
    op.add_column("portfolio_visitors", sa.Column("country_code", sa.String(length=16), nullable=True))
    op.add_column("portfolio_visitors", sa.Column("region", sa.String(length=120), nullable=True))
    op.add_column("portfolio_visitors", sa.Column("city", sa.String(length=120), nullable=True))

    op.execute(
        """
        UPDATE portfolio_visitors
        SET visitor_id = id::text,
            first_visited_at = created_at,
            last_visited_at = COALESCE(updated_at, created_at),
            visit_count = 1
        """
    )

    op.alter_column("portfolio_visitors", "visitor_id", nullable=False)
    op.alter_column("portfolio_visitors", "first_visited_at", nullable=False)
    op.alter_column("portfolio_visitors", "last_visited_at", nullable=False)
    op.alter_column("portfolio_visitors", "visit_count", nullable=False)

    op.create_index(
        op.f("ix_portfolio_visitors_user_id"),
        "portfolio_visitors",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_portfolio_visitors_user_last_visited_at",
        "portfolio_visitors",
        ["user_id", "last_visited_at"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_portfolio_visitors_user_visitor",
        "portfolio_visitors",
        ["user_id", "visitor_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_portfolio_visitors_user_visitor",
        "portfolio_visitors",
        type_="unique",
    )
    op.drop_index("ix_portfolio_visitors_user_last_visited_at", table_name="portfolio_visitors")
    op.drop_index(op.f("ix_portfolio_visitors_user_id"), table_name="portfolio_visitors")
    op.drop_column("portfolio_visitors", "city")
    op.drop_column("portfolio_visitors", "region")
    op.drop_column("portfolio_visitors", "country_code")
    op.drop_column("portfolio_visitors", "visit_count")
    op.drop_column("portfolio_visitors", "last_visited_at")
    op.drop_column("portfolio_visitors", "first_visited_at")
    op.drop_column("portfolio_visitors", "visitor_id")
    op.alter_column(
        "portfolio_visitors",
        "last_path",
        new_column_name="path",
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )
    op.rename_table("portfolio_visitors", "portfolio_views")
    op.create_index(
        op.f("ix_portfolio_views_user_id"),
        "portfolio_views",
        ["user_id"],
        unique=False,
    )
