"""migrate projects from companies to work experiences

Revision ID: a3d006efa72e
Revises: 94fca1a390c3
Create Date: 2026-04-07 08:44:19.417755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3d006efa72e'
down_revision: Union[str, None] = '94fca1a390c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
