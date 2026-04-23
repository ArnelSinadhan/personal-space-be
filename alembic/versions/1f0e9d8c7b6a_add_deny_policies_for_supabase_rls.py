"""add deny policies for supabase rls

Revision ID: 1f0e9d8c7b6a
Revises: 7b9a3d2e4f61
Create Date: 2026-04-23 18:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
from app.migration_security import lock_down_public_tables

# revision identifiers, used by Alembic.
revision: str = "1f0e9d8c7b6a"
down_revision: str | None = "7b9a3d2e4f61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PUBLIC_TABLES = (
    "alembic_version",
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
    "upwork_project_tech_stacks",
    "todos",
    "notes",
    "resumes",
    "resume_skills",
    "resume_experiences",
    "resume_educations",
    "resume_projects",
    "resume_project_tech_stacks",
    "resume_links",
    "vault_pins",
    "vault_categories",
    "vault_entries",
    "portfolio_visitors",
)


def upgrade() -> None:
    lock_down_public_tables(PUBLIC_TABLES)


def downgrade() -> None:
    for table_name in PUBLIC_TABLES:
        op.execute(f'DROP POLICY IF EXISTS deny_direct_client_access ON public."{table_name}"')
