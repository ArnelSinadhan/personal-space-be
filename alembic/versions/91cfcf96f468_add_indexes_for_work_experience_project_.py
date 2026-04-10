"""add indexes for work experience project structure

Revision ID: 91cfcf96f468
Revises: a3d006efa72e
Create Date: 2026-04-07 08:51:46.403774
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

revision: str = "91cfcf96f468"
down_revision: Union[str, None] = "a3d006efa72e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_indexes = {
        index["name"] for index in inspector.get_indexes("education_entries")
    }
    if op.f("ix_education_entries_profile_id") not in existing_indexes:
        op.create_index(
            op.f("ix_education_entries_profile_id"),
            "education_entries",
            ["profile_id"],
            unique=False,
        )

    existing_indexes = {
        index["name"] for index in inspector.get_indexes("social_links")
    }
    if op.f("ix_social_links_profile_id") not in existing_indexes:
        op.create_index(
            op.f("ix_social_links_profile_id"),
            "social_links",
            ["profile_id"],
            unique=False,
        )

    existing_indexes = {
        index["name"] for index in inspector.get_indexes("work_experiences")
    }
    if op.f("ix_work_experiences_profile_id") not in existing_indexes:
        op.create_index(
            op.f("ix_work_experiences_profile_id"),
            "work_experiences",
            ["profile_id"],
            unique=False,
        )
    if "ix_work_experiences_profile_current" not in existing_indexes:
        op.create_index(
            "ix_work_experiences_profile_current",
            "work_experiences",
            ["profile_id", "is_current"],
            unique=False,
        )

    project_columns = {
        column["name"] for column in inspector.get_columns("projects")
    }
    has_work_experience_id = "work_experience_id" in project_columns
    has_company_id = "company_id" in project_columns
    has_companies_table = "companies" in inspector.get_table_names()

    existing_project_indexes = {
        index["name"] for index in inspector.get_indexes("projects")
    }

    if not has_work_experience_id:
        op.add_column(
            "projects",
            sa.Column("work_experience_id", sa.UUID(), nullable=True),
        )
        has_work_experience_id = True

    if has_company_id and has_companies_table:
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

        if op.f("ix_projects_work_experience_id") not in existing_project_indexes:
            op.create_index(
                op.f("ix_projects_work_experience_id"),
                "projects",
                ["work_experience_id"],
                unique=False,
            )

        foreign_keys = {
            fk["name"] for fk in inspector.get_foreign_keys("projects") if fk.get("name")
        }
        if op.f("projects_company_id_fkey") in foreign_keys:
            op.drop_constraint(
                op.f("projects_company_id_fkey"),
                "projects",
                type_="foreignkey",
            )
        if "projects_work_experience_id_fkey" not in foreign_keys:
            op.create_foreign_key(
                "projects_work_experience_id_fkey",
                "projects",
                "work_experiences",
                ["work_experience_id"],
                ["id"],
                ondelete="CASCADE",
            )

        if op.f("ix_projects_company_id") in existing_project_indexes:
            op.drop_index(op.f("ix_projects_company_id"), table_name="projects")
        op.drop_column("projects", "company_id")

        company_indexes = {
            index["name"] for index in inspector.get_indexes("companies")
        }
        if op.f("ix_companies_user_id") in company_indexes:
            op.drop_index(op.f("ix_companies_user_id"), table_name="companies")
        op.drop_table("companies")
    elif (
        has_work_experience_id
        and op.f("ix_projects_work_experience_id") not in existing_project_indexes
    ):
        op.create_index(
            op.f("ix_projects_work_experience_id"),
            "projects",
            ["work_experience_id"],
            unique=False,
        )


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
