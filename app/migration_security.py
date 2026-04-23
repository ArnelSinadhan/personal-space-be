"""Security helpers for Supabase-backed Alembic migrations."""

from __future__ import annotations

import re
from collections.abc import Iterable

from alembic import op

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _quote_identifier(identifier: str) -> str:
    if not _IDENTIFIER_RE.fullmatch(identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier!r}")
    return f'"{identifier}"'


def lock_down_public_table(table_name: str, *, schema: str = "public") -> None:
    """Enable RLS and explicitly deny direct Supabase client role access."""

    qualified_table = f"{_quote_identifier(schema)}.{_quote_identifier(table_name)}"
    op.execute(f"ALTER TABLE {qualified_table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"REVOKE ALL ON TABLE {qualified_table} FROM anon")
    op.execute(f"REVOKE ALL ON TABLE {qualified_table} FROM authenticated")
    create_deny_direct_client_policy(table_name, schema=schema)


def create_deny_direct_client_policy(table_name: str, *, schema: str = "public") -> None:
    """Create a deny-all policy so Supabase linter sees intentional RLS."""

    qualified_table = f"{_quote_identifier(schema)}.{_quote_identifier(table_name)}"
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_policies
                WHERE schemaname = '{schema}'
                  AND tablename = '{table_name}'
                  AND policyname = 'deny_direct_client_access'
            ) THEN
                CREATE POLICY deny_direct_client_access
                ON {qualified_table}
                AS RESTRICTIVE
                FOR ALL
                TO anon, authenticated
                USING (false)
                WITH CHECK (false);
            END IF;
        END
        $$;
        """
    )


def lock_down_public_tables(table_names: Iterable[str], *, schema: str = "public") -> None:
    for table_name in table_names:
        lock_down_public_table(table_name, schema=schema)


def create_deny_direct_client_policies(
    table_names: Iterable[str], *, schema: str = "public"
) -> None:
    for table_name in table_names:
        create_deny_direct_client_policy(table_name, schema=schema)


def lock_down_public_schema_defaults(*, schema: str = "public") -> None:
    """Prevent future public tables/sequences from granting direct client access."""

    quoted_schema = _quote_identifier(schema)
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {quoted_schema} "
        "REVOKE ALL ON TABLES FROM anon"
    )
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {quoted_schema} "
        "REVOKE ALL ON TABLES FROM authenticated"
    )
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {quoted_schema} "
        "REVOKE ALL ON SEQUENCES FROM anon"
    )
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {quoted_schema} "
        "REVOKE ALL ON SEQUENCES FROM authenticated"
    )
