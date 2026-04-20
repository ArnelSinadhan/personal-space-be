#!/usr/bin/env sh
set -eu

if [ "${RUN_MIGRATIONS_ON_STARTUP:-1}" = "1" ]; then
  echo "Checking Alembic migration heads..."
  ./scripts/check_alembic_heads.sh

  echo "Running database migrations..."
  alembic upgrade head
fi

echo "Starting API..."
exec "$@"
