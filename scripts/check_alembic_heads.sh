#!/usr/bin/env bash

set -euo pipefail

heads_output="$(alembic heads)"
head_count="$(printf '%s\n' "$heads_output" | sed '/^[[:space:]]*$/d' | wc -l | tr -d ' ')"

if [ "$head_count" -ne 1 ]; then
  echo "Expected exactly 1 Alembic head, found $head_count." >&2
  echo >&2
  echo "$heads_output" >&2
  echo >&2
  echo "Resolve multiple migration heads before merging or running alembic upgrade head." >&2
  exit 1
fi

echo "Alembic head check passed:"
echo "$heads_output"
