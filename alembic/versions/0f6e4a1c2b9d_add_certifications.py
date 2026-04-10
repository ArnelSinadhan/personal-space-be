"""add certifications

Revision ID: 0f6e4a1c2b9d
Revises: f2c9a7d4e1b3
Create Date: 2026-04-10 11:20:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0f6e4a1c2b9d"
down_revision: Union[str, None] = "f2c9a7d4e1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "certification_entries",
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("issuer", sa.String(length=255), nullable=False),
        sa.Column("issued_at", sa.String(length=100), nullable=False),
        sa.Column("expires_at", sa.String(length=100), nullable=True),
        sa.Column("credential_id", sa.String(length=255), nullable=True),
        sa.Column("credential_url", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_certification_entries_profile_id",
        "certification_entries",
        ["profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_certification_entries_profile_id", table_name="certification_entries")
    op.drop_table("certification_entries")
