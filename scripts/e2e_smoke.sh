#!/usr/bin/env bash
#
# End-to-end smoke test for OpenEdu Git.
#
# Exercises the core happy path against a real backend + PostgreSQL + MinIO:
#   register -> login -> create pamphlet -> upload version (file stored in MinIO)
# plus the negative auth/validation checks, and verifies the uploaded object
# in MinIO byte-for-byte (sha256) — the "download" leg, since the storage
# download endpoint is tracked separately (C5).
#
# Required environment:
#   API_URL    Base URL of the running API incl. prefix, e.g. http://localhost:8000/api/v1
#   MC_EXEC    Command prefix that runs `mc` with the given args, e.g.
#              "docker exec mc-helper" (the container must be able to reach MinIO)
#
# Optional environment:
#   MC_ENDPOINT          MinIO S3 endpoint as seen by the mc context (default http://localhost:9000)
#   MINIO_ACCESS_KEY     (default minioadmin)
#   MINIO_SECRET_KEY     (default minioadmin)
#   SMOKE_BUCKET         Pamphlets bucket (default pamphlets)
#   SMOKE_RUN_ID         Unique id for this run (default: unix timestamp)
#
# Exit code 0 = smoke passed, non-zero = failure.

set -euo pipefail

: "${API_URL:?API_URL is required (e.g. http://localhost:8000/api/v1)}"
: "${MC_EXEC:?MC_EXEC is required (e.g. \"docker exec mc-helper\")}"

MC_ENDPOINT="${MC_ENDPOINT:-http://localhost:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-minioadmin}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-minioadmin}"
SMOKE_BUCKET="${SMOKE_BUCKET:-pamphlets}"
SMOKE_RUN_ID="${SMOKE_RUN_ID:-$(date +%s)}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

step()  { echo "==> $*"; }
fail()  { echo "FAIL: $*" >&2; exit 1; }
expect_code() { # expect_code <expected> <actual> <label> <body_file>
    if [ "$2" != "$1" ]; then
        fail "$3: expected HTTP $1, got $2 (body: $(cat "$4" 2>/dev/null || echo '<none>'))"
    fi
    echo "    $3 -> $2"
}

json_field() { # json_field <file> <field>
    python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$1" "$2"
}

EMAIL="smoke-${SMOKE_RUN_ID}-$(head -c 4 /dev/urandom | od -An -tx1 | tr -d ' \n')@example.com"
PASSWORD="smoke-pw-${SMOKE_RUN_ID}"
BODY="$TMP_DIR/body.json"

step "Registering user $EMAIL"
CODE="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$API_URL/auth/register" \
    -H 'Content-Type: application/json' \
    -d '{"email":"'"$EMAIL"'","password":"'"$PASSWORD"'","full_name":"Smoke Tester"}')"
expect_code 201 "$CODE" "register" "$BODY"
USER_ID="$(json_field "$BODY" id)"

step "Logging in"
CODE="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$API_URL/auth/login" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=$EMAIL" \
    --data-urlencode "password=$PASSWORD")"
expect_code 200 "$CODE" "login" "$BODY"
TOKEN="$(json_field "$BODY" access_token)"
[ -n "$TOKEN" ] || fail "login returned an empty access token"
AUTH="Authorization: Bearer $TOKEN"

step "Creating pamphlet"
CODE="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$API_URL/pamphlets/" \
    -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"title":"Smoke pamphlet '"$SMOKE_RUN_ID"'","grade":"12","subject":"smoke","chapter":"1","is_public":true,"tags":["smoke"]}')"
expect_code 200 "$CODE" "create pamphlet" "$BODY"
PAMPHLET_ID="$(json_field "$BODY" id)"

step "Reading pamphlet back"
CODE="$(curl -sS -o "$BODY" -w '%{http_code}' "$API_URL/pamphlets/$PAMPHLET_ID")"
expect_code 200 "$CODE" "get pamphlet" "$BODY"
[ "$(json_field "$BODY" id)" = "$PAMPHLET_ID" ] || fail "pamphlet id mismatch on read-back"

step "Uploading version 1 (markdown payload)"
printf 'OpenEdu smoke payload\nrun: %s\npamphlet: %s\n' "$SMOKE_RUN_ID" "$PAMPHLET_ID" > "$TMP_DIR/payload.md"
# Pad the file so size/content are non-trivial
head -c 1024 /dev/urandom >> "$TMP_DIR/payload.md"
LOCAL_SIZE="$(wc -c < "$TMP_DIR/payload.md" | tr -d ' ')"
LOCAL_SHA="$(sha256sum "$TMP_DIR/payload.md" | cut -d' ' -f1)"

CODE="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$API_URL/pamphlets/$PAMPHLET_ID/versions" \
    -H "$AUTH" \
    -F "version_number=1" \
    -F "notes=smoke upload $SMOKE_RUN_ID" \
    -F "file=@$TMP_DIR/payload.md;type=text/markdown")"
expect_code 200 "$CODE" "upload version" "$BODY"
FILE_PATH="$(json_field "$BODY" file_path)"
UPLOADED_SIZE="$(json_field "$BODY" file_size)"
[ -n "$FILE_PATH" ] || fail "upload response missing file_path"
[ "$UPLOADED_SIZE" = "$LOCAL_SIZE" ] || fail "file_size mismatch: api=$UPLOADED_SIZE local=$LOCAL_SIZE"

step "Verifying negative checks"
# No token -> 401
CODE="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$API_URL/pamphlets/$PAMPHLET_ID/versions" \
    -F "version_number=2" -F "file=@$TMP_DIR/payload.md;type=text/markdown")"
expect_code 401 "$CODE" "upload without token" "$BODY"

# version_number=0 -> 422
CODE="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$API_URL/pamphlets/$PAMPHLET_ID/versions" \
    -H "$AUTH" -F "version_number=0" -F "file=@$TMP_DIR/payload.md;type=text/markdown")"
expect_code 422 "$CODE" "version_number=0" "$BODY"

# Disallowed extension -> 400
cp "$TMP_DIR/payload.md" "$TMP_DIR/payload.exe"
CODE="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$API_URL/pamphlets/$PAMPHLET_ID/versions" \
    -H "$AUTH" -F "version_number=2" -F "file=@$TMP_DIR/payload.exe;type=application/octet-stream")"
expect_code 400 "$CODE" "disallowed extension" "$BODY"

step "Verifying object in MinIO (download leg via mc)"
mc() { # shellcheck disable=SC2086  — MC_EXEC is intentionally word-split
    $MC_EXEC "$@"
}

# Retry alias setup in case MinIO is still starting
ALIAS_OK=0
for _ in $(seq 1 15); do
    if mc alias set smokecheck "$MC_ENDPOINT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" >/dev/null 2>&1; then
        ALIAS_OK=1
        break
    fi
    sleep 2
done
[ "$ALIAS_OK" = 1 ] || fail "could not reach MinIO at $MC_ENDPOINT via mc"

REMOTE_SHA="$(mc cat "smokecheck/$SMOKE_BUCKET/$FILE_PATH" | sha256sum | cut -d' ' -f1)"
[ "$REMOTE_SHA" = "$LOCAL_SHA" ] || fail "object sha256 mismatch: minio=$REMOTE_SHA local=$LOCAL_SHA"

step "E2E smoke PASSED (user=$USER_ID pamphlet=$PAMPHLET_ID object=$FILE_PATH sha256=${REMOTE_SHA:0:12}...)"
