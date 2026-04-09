"""add profile public slug

Revision ID: 7f3d2bb3c0f1
Revises: d1b8e4c9f2a1
Create Date: 2026-04-09 22:10:00.000000
"""

from collections.abc import Sequence
import re

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f3d2bb3c0f1"
down_revision: str | None = "d1b8e4c9f2a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _slugify_email_local_part(email: str | None) -> str:
    local_part = (email or "").split("@", 1)[0].strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", local_part).strip("-")
    return slug or "user"


def upgrade() -> None:
    op.add_column("profiles", sa.Column("public_slug", sa.String(length=100), nullable=True))
    op.add_column("profiles", sa.Column("is_portfolio_public", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_profiles_public_slug", "profiles", ["public_slug"], unique=True)

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT profiles.id, COALESCE(profiles.email, users.email) AS email
            FROM profiles
            JOIN users ON users.id = profiles.user_id
            ORDER BY profiles.created_at, profiles.id
            """
        )
    ).mappings().all()

    used_slugs: set[str] = set()
    for row in rows:
        base_slug = _slugify_email_local_part(row["email"])
        candidate = base_slug
        suffix = 2
        while candidate in used_slugs:
            candidate = f"{base_slug}-{suffix}"
            suffix += 1
        used_slugs.add(candidate)
        bind.execute(
            sa.text("UPDATE profiles SET public_slug = :slug WHERE id = :id"),
            {"slug": candidate, "id": row["id"]},
        )

    op.alter_column("profiles", "is_portfolio_public", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_profiles_public_slug", table_name="profiles")
    op.drop_column("profiles", "is_portfolio_public")
    op.drop_column("profiles", "public_slug")
