"""add description to work experiences

Revision ID: 4b8f1d2c9a7e
Revises: e3b1c4a9f8d2
Create Date: 2026-04-11 11:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4b8f1d2c9a7e"
down_revision: str | None = "e3b1c4a9f8d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "work_experiences",
        sa.Column("description", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("work_experiences", "description")
