"""add project image url

Revision ID: c73c0a6b9f5f
Revises: 91cfcf96f468
Create Date: 2026-04-08 18:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c73c0a6b9f5f"
down_revision: Union[str, None] = "91cfcf96f468"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("image_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "image_url")
