"""add upwork projects

Revision ID: 3e7f2a1b4c8d
Revises: 6ad2dc0d9c37
Branch Labels: None
Depends On: None

Create Date: 2026-04-15 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "3e7f2a1b4c8d"
down_revision: str | None = "6ad2dc0d9c37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "upwork_projects",
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("github_url", sa.Text(), nullable=True),
        sa.Column("live_url", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "lifecycle_status",
            sa.String(length=20),
            nullable=False,
            server_default="active",
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome_summary", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_upwork_projects_profile_id"),
        "upwork_projects",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_upwork_projects_lifecycle_status"),
        "upwork_projects",
        ["lifecycle_status"],
        unique=False,
    )

    op.create_table(
        "upwork_project_tech_stacks",
        sa.Column(
            "upwork_project_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["upwork_project_id"], ["upwork_projects.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("upwork_project_id", "skill_id"),
    )


def downgrade() -> None:
    op.drop_table("upwork_project_tech_stacks")
    op.drop_index(
        op.f("ix_upwork_projects_lifecycle_status"), table_name="upwork_projects"
    )
    op.drop_index(
        op.f("ix_upwork_projects_profile_id"), table_name="upwork_projects"
    )
    op.drop_table("upwork_projects")
