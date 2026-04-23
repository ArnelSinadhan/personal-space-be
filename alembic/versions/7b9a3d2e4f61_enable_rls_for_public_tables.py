"""enable rls for public tables

Revision ID: 7b9a3d2e4f61
Revises: e5a1c3d9b742
Create Date: 2026-04-23 17:40:00.000000
"""

from collections.abc import Sequence

from alembic import op
from app.migration_security import (
    lock_down_public_schema_defaults,
    lock_down_public_tables,
)

# revision identifiers, used by Alembic.
revision: str = "7b9a3d2e4f61"
down_revision: str | None = "e5a1c3d9b742"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PUBLIC_APP_TABLES = (
    "users",
    "profiles",
    "skills",
    "profile_skills",
    "work_experiences",
    "education_entries",
    "certification_entries",
    "social_links",
    "projects",
    "project_tech_stacks",
    "project_testimonials",
    "project_testimonial_submission_logs",
    "personal_projects",
    "personal_project_tech_stacks",
    "upwork_projects",
    "todos",
    "notes",
    "resumes",
    "resume_experiences",
    "resume_educations",
    "resume_projects",
    "resume_links",
    "vault_pins",
    "vault_categories",
    "vault_entries",
    "portfolio_visitors",
)


def upgrade() -> None:
    lock_down_public_tables(PUBLIC_APP_TABLES)
    lock_down_public_schema_defaults()


def downgrade() -> None:
    for table_name in PUBLIC_APP_TABLES:
        op.execute(f'ALTER TABLE public."{table_name}" DISABLE ROW LEVEL SECURITY')
