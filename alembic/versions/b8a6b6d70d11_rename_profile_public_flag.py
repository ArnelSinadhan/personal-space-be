"""rename profile public flag

Revision ID: b8a6b6d70d11
Revises: 7f3d2bb3c0f1
Create Date: 2026-04-09 23:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8a6b6d70d11"
down_revision: str | None = "7f3d2bb3c0f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "profiles",
        "is_portfolio_public",
        new_column_name="is_public_profile_enabled",
    )


def downgrade() -> None:
    op.alter_column(
        "profiles",
        "is_public_profile_enabled",
        new_column_name="is_portfolio_public",
    )
