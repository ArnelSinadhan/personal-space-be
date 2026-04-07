"""add indexes for work experience project structure

Revision ID: 91cfcf96f468
Revises: a3d006efa72e
Create Date: 2026-04-07 08:51:46.403774
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "91cfcf96f468"
down_revision: Union[str, None] = "a3d006efa72e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_education_entries_profile_id"),
        "education_entries",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_social_links_profile_id"),
        "social_links",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_work_experiences_profile_id"),
        "work_experiences",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        "ix_work_experiences_profile_current",
        "work_experiences",
        ["profile_id", "is_current"],
        unique=False,
    )

    op.add_column(
        "projects",
        sa.Column("work_experience_id", sa.UUID(), nullable=True),
    )

    op.execute(
        """
        UPDATE projects p
        SET work_experience_id = we.id
        FROM companies c
        JOIN profiles pr ON pr.user_id = c.user_id
        JOIN work_experiences we
          ON we.profile_id = pr.id
         AND we.company = c.name
        WHERE p.company_id = c.id
          AND p.work_experience_id IS NULL
        """
    )

    op.execute(
        """
        INSERT INTO work_experiences (
            id,
            profile_id,
            title,
            company,
            start_date,
            end_date,
            is_current,
            image_url,
            sort_order,
            created_at,
            updated_at
        )
        SELECT
            gen_random_uuid(),
            pr.id,
            COALESCE(c.role, ''),
            c.name,
            COALESCE(c.start_date, ''),
            c.end_date,
            c.is_current,
            c.logo_url,
            c.sort_order,
            now(),
            now()
        FROM companies c
        JOIN profiles pr ON pr.user_id = c.user_id
        LEFT JOIN work_experiences we
          ON we.profile_id = pr.id
         AND we.company = c.name
        WHERE we.id IS NULL
        """
    )

    op.execute(
        """
        UPDATE projects p
        SET work_experience_id = we.id
        FROM companies c
        JOIN profiles pr ON pr.user_id = c.user_id
        JOIN work_experiences we
          ON we.profile_id = pr.id
         AND we.company = c.name
        WHERE p.company_id = c.id
          AND p.work_experience_id IS NULL
        """
    )

    op.alter_column("projects", "work_experience_id", nullable=False)

    op.create_index(
        op.f("ix_projects_work_experience_id"),
        "projects",
        ["work_experience_id"],
        unique=False,
    )

    op.drop_constraint(
        op.f("projects_company_id_fkey"),
        "projects",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "projects_work_experience_id_fkey",
        "projects",
        "work_experiences",
        ["work_experience_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_index(op.f("ix_projects_company_id"), table_name="projects")
    op.drop_column("projects", "company_id")

    op.drop_index(op.f("ix_companies_user_id"), table_name="companies")
    op.drop_table("companies")


def downgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("user_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(length=255), autoincrement=False, nullable=False),
        sa.Column("logo_url", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("role", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column(
            "start_date", sa.VARCHAR(length=100), autoincrement=False, nullable=True
        ),
        sa.Column(
            "end_date", sa.VARCHAR(length=100), autoincrement=False, nullable=True
        ),
        sa.Column("is_current", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("sort_order", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("companies_user_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("companies_pkey")),
    )
    op.create_index(
        op.f("ix_companies_user_id"), "companies", ["user_id"], unique=False
    )

    op.add_column(
        "projects",
        sa.Column("company_id", sa.UUID(), autoincrement=False, nullable=True),
    )

    op.drop_constraint(
        "projects_work_experience_id_fkey", "projects", type_="foreignkey"
    )
    op.execute(
        """
        UPDATE projects
        SET company_id = NULL
        """
    )
    op.create_index(
        op.f("ix_projects_company_id"), "projects", ["company_id"], unique=False
    )
    op.create_foreign_key(
        op.f("projects_company_id_fkey"),
        "projects",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_index(op.f("ix_projects_work_experience_id"), table_name="projects")
    op.drop_column("projects", "work_experience_id")

    op.drop_index("ix_work_experiences_profile_current", table_name="work_experiences")
    op.drop_index(op.f("ix_work_experiences_profile_id"), table_name="work_experiences")
    op.drop_index(op.f("ix_social_links_profile_id"), table_name="social_links")
    op.drop_index(
        op.f("ix_education_entries_profile_id"), table_name="education_entries"
    )
