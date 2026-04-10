"""add project testimonials

Revision ID: e3b1c4a9f8d2
Revises: b8a6b6d70d11
Create Date: 2026-04-10 11:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e3b1c4a9f8d2"
down_revision: str | None = "b8a6b6d70d11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_testimonials",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index(
        op.f("ix_project_testimonials_project_id"),
        "project_testimonials",
        ["project_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_project_testimonials_status"),
        "project_testimonials",
        ["status"],
        unique=False,
    )

    op.create_table(
        "project_testimonial_submission_logs",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ip_address", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_project_testimonial_submission_logs_project_id"),
        "project_testimonial_submission_logs",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_testimonial_submission_logs_ip_address"),
        "project_testimonial_submission_logs",
        ["ip_address"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_project_testimonial_submission_logs_ip_address"),
        table_name="project_testimonial_submission_logs",
    )
    op.drop_index(
        op.f("ix_project_testimonial_submission_logs_project_id"),
        table_name="project_testimonial_submission_logs",
    )
    op.drop_table("project_testimonial_submission_logs")

    op.drop_index(op.f("ix_project_testimonials_status"), table_name="project_testimonials")
    op.drop_index(
        op.f("ix_project_testimonials_project_id"), table_name="project_testimonials"
    )
    op.drop_table("project_testimonials")
