"""merge work experience description and certifications heads

Revision ID: 8c1d7f4b2e6a
Revises: 0f6e4a1c2b9d, 4b8f1d2c9a7e
Create Date: 2026-04-11 17:05:00.000000
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "8c1d7f4b2e6a"
down_revision: tuple[str, str] = ("0f6e4a1c2b9d", "4b8f1d2c9a7e")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
