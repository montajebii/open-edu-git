#!/bin/sh
# Backend container entrypoint: apply database migrations, then start the API.
#
# Migration policy:
#   - empty database        -> `alembic upgrade head` creates the full schema
#   - alembic-managed DB    -> `alembic upgrade head` applies pending revisions
#   - legacy DB (tables exist but no alembic_version) -> refuse to guess:
#     leave the data untouched, print instructions, and keep serving with the
#     existing schema (recreate the database, or `alembic stamp head` if you
#     know the schema already matches).
set -e

cd /app

POLICY="$(python - <<'PY'
import os
import sys

from sqlalchemy import create_engine, inspect

try:
    engine = create_engine(os.environ["DATABASE_URL"])
    names = set(inspect(engine).get_table_names())
except Exception as exc:
    print(f"entrypoint: could not inspect database: {exc}", file=sys.stderr)
    print("skip")
    raise SystemExit(0)

if not names:
    print("migrate")
elif "alembic_version" in names:
    print("upgrade")
else:
    print("legacy")
PY
)"

case "$POLICY" in
migrate)
    echo "entrypoint: empty database -> applying migrations"
    alembic upgrade head
    ;;
upgrade)
    echo "entrypoint: alembic-managed database -> applying pending migrations"
    alembic upgrade head
    ;;
legacy)
    cat >&2 <<'MSG'
entrypoint: database has tables but no alembic_version bookkeeping
(legacy pre-Alembic deployment). Refusing to migrate automatically to
avoid guessing wrong about its state. The app will start with the
existing schema.

Options:
  1. Recreate the database, then restart: migrations will build the
     current schema from scratch.
  2. If the schema already matches the ORM, run once:
       alembic stamp head
     and restart; future upgrades will then be applied normally.
MSG
    ;;
*)
    echo "entrypoint: WARNING: database state unknown; starting without migrating." >&2
    ;;
esac

exec "$@"
