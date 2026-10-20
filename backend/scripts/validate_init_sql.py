"""Validate migrations/init.sql against a real PostgreSQL.

This closes the gap that CI cannot: the tests run on SQLite, so nothing checks
that init.sql actually applies cleanly and matches the SQLAlchemy models. This
script starts an embedded PostgreSQL (``pip install pgserver``), then:

1. applies migrations/init.sql,
2. checks every table init.sql creates,
3. verifies the search_vector trigger fires on INSERT,
4. diffs init.sql's columns against the SQLAlchemy metadata (drift = exit 1),
5. boots the API against that database and runs the auth + pamphlet flow
   over real HTTP, including refresh-token revocation on logout.

Usage:
    pip install pgserver
    python scripts/validate_init_sql.py
"""

import os
import sys
import tempfile
import threading
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "init-sql-validation-key")
os.environ.setdefault("MINIO_ENDPOINT", "127.0.0.1:1")
os.environ.setdefault("MINIO_AUTO_CREATE_BUCKETS", "false")
os.environ.setdefault("PASSWORD_HASH_ROUNDS", "4")

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import httpx  # noqa: E402
import pgserver  # noqa: E402
import psycopg2  # noqa: E402
import uvicorn  # noqa: E402

EXPECTED_TABLES = {
    "users",
    "verification_tokens",
    "revoked_tokens",
    "pamphlets",
    "pamphlet_versions",
    "reviews",
    "pamphlet_forks",
    "merge_requests",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def main() -> None:
    workdir = tempfile.mkdtemp(prefix="pgvalidate-")
    server = pgserver.get_server(workdir)
    uri = server.get_uri()
    print(f"[pg] embedded PostgreSQL at {uri}")

    init_sql = (BACKEND_DIR / "migrations" / "init.sql").read_text()

    conn = psycopg2.connect(uri)
    conn.autocommit = True  # init.sql contains CREATE TYPE (needs autocommit)
    with conn.cursor() as cur:
        cur.execute(init_sql)
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
        tables = {row[0] for row in cur.fetchall()}
    print(f"[pg] init.sql applied; tables: {sorted(tables)}")
    missing = EXPECTED_TABLES - tables
    if missing:
        fail(f"tables missing from init.sql: {sorted(missing)}")

    # The search trigger must populate the vector on INSERT.
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name) "
            "VALUES ('trigger@example.com', 'x', 'Trigger')"
        )
        cur.execute("SELECT id FROM users WHERE email = 'trigger@example.com'")
        user_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO pamphlets (title, author_id, grade, subject, chapter) "
            "VALUES ('جزوۀ ریاضی', %s, 'یازدهم', 'ریاضی', 'مشتق')",
            (user_id,),
        )
        cur.execute("SELECT search_vector FROM pamphlets LIMIT 1")
        vector = cur.fetchone()[0]
        if not vector or "ریاضی" not in str(vector):
            fail(f"search_vector trigger did not fire: {vector!r}")
    print("[pg] search_vector trigger works on INSERT")

    # Diff init.sql against the SQLAlchemy models.
    os.environ["DATABASE_URL"] = uri

    import app.models  # noqa: F401,E402  (register metadata)
    from app.db.base import Base  # noqa: E402

    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' ORDER BY table_name, column_name"
        )
        pg_columns: dict[str, set[str]] = {}
        for table, column in cur.fetchall():
            pg_columns.setdefault(table, set()).add(column)

    drift = []
    model_tables = {t.name for t in Base.metadata.sorted_tables}
    for table in Base.metadata.sorted_tables:
        model_cols = {c.name for c in table.columns}
        actual = pg_columns.get(table.name)
        if actual is None:
            drift.append(f"{table.name}: missing from init.sql")
            continue
        # search_vector exists only in init.sql (maintained by the trigger).
        only_pg = actual - model_cols - {"search_vector"}
        only_model = model_cols - actual
        if only_pg:
            drift.append(f"{table.name}: in init.sql but not in the model: {sorted(only_pg)}")
        if only_model:
            drift.append(f"{table.name}: in the model but not in init.sql: {sorted(only_model)}")
    for table in sorted(set(pg_columns) - model_tables):
        drift.append(f"{table}: in init.sql but has no model")
    if drift:
        print("SCHEMA DRIFT DETECTED:")
        for line in drift:
            print(f"  - {line}")
        sys.exit(1)
    print("[pg] init.sql matches the SQLAlchemy models exactly")

    # Boot the API against Postgres and exercise the real flow.
    os.environ["DATABASE_URL"] = uri

    from app.main import app  # noqa: E402

    config = uvicorn.Config(app, host="127.0.0.1", port=8123, log_level="warning")
    httpd = uvicorn.Server(config)
    threading.Thread(target=httpd.run, daemon=True).start()
    while not httpd.started:
        pass

    checks: list[tuple[str, bool, str]] = []
    with httpx.Client(base_url="http://127.0.0.1:8123") as client:
        r = client.get("/health")
        checks.append(("health", r.status_code == 200, r.text))

        r = client.post(
            "/api/v1/auth/register",
            json={"email": "pg@example.com", "password": "secret123", "full_name": "PG User"},
        )
        checks.append(("register", r.status_code == 201, r.text))
        user_id = r.json().get("id") if r.status_code == 201 else None

        r = client.post(
            "/api/v1/auth/login",
            data={"username": "pg@example.com", "password": "secret123"},
        )
        checks.append(("login", r.status_code == 200, r.text))
        refresh_token = r.json().get("refresh_token", "")
        access_headers = {"Authorization": f"Bearer {r.json().get('access_token', '')}"}

        r = client.get("/api/v1/auth/me", headers=access_headers)
        checks.append(("me", r.status_code == 200 and r.json().get("id") == user_id, r.text))

        r = client.post(
            "/api/v1/pamphlets/",
            headers=access_headers,
            json={
                "title": "جزوۀ فیزیک",
                "grade": "دهم",
                "subject": "فیزیک",
                "chapter": "حرکت",
                "tags": ["فیزیک", "دهم"],
            },
        )
        checks.append(("create pamphlet", r.status_code == 201, r.text))
        pamphlet_id = r.json().get("id")

        r = client.get("/api/v1/pamphlets/?subject=فیزیک", headers=access_headers)
        found = r.status_code == 200 and any(p["id"] == pamphlet_id for p in r.json())
        checks.append(("search (ILIKE)", found, r.text[:200]))

        r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        checks.append(("refresh", r.status_code == 200, r.text))

        r = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        checks.append(("logout", r.status_code == 200, r.text))

        r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        checks.append(("refresh after logout is revoked", r.status_code == 401, r.text))

    failed = False
    for name, ok, detail in checks:
        print(f"[api] {'PASS' if ok else 'FAIL'}: {name}" + ("" if ok else f" -> {detail}"))
        failed = failed or not ok

    httpd.should_exit = True
    server.cleanup()
    if failed:
        sys.exit(1)
    print("init.sql validated against real PostgreSQL: all checks passed")


if __name__ == "__main__":
    main()
