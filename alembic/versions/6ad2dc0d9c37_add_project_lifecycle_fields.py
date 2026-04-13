"""add project lifecycle fields

Revision ID: 6ad2dc0d9c37
Revises: 8c1d7f4b2e6a
Create Date: 2026-04-13 10:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6ad2dc0d9c37"
down_revision: str | None = "8c1d7f4b2e6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("lifecycle_status", sa.String(length=20), nullable=False, server_default="active"),
    )
    op.add_column("projects", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("projects", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("projects", sa.Column("outcome_summary", sa.Text(), nullable=True))
    op.create_index(op.f("ix_projects_lifecycle_status"), "projects", ["lifecycle_status"], unique=False)

    op.add_column(
        "personal_projects",
        sa.Column("lifecycle_status", sa.String(length=20), nullable=False, server_default="active"),
    )
    op.add_column("personal_projects", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("personal_projects", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("personal_projects", sa.Column("outcome_summary", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_personal_projects_lifecycle_status"),
        "personal_projects",
        ["lifecycle_status"],
        unique=False,
    )

    op.alter_column("projects", "lifecycle_status", server_default=None)
    op.alter_column("personal_projects", "lifecycle_status", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_personal_projects_lifecycle_status"), table_name="personal_projects")
    op.drop_column("personal_projects", "outcome_summary")
    op.drop_column("personal_projects", "archived_at")
    op.drop_column("personal_projects", "completed_at")
    op.drop_column("personal_projects", "lifecycle_status")

    op.drop_index(op.f("ix_projects_lifecycle_status"), table_name="projects")
    op.drop_column("projects", "outcome_summary")
    op.drop_column("projects", "archived_at")
    op.drop_column("projects", "completed_at")
    op.drop_column("projects", "lifecycle_status")
