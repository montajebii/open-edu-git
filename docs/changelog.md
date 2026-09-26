# Changelog

## [Unreleased]
### Changed
- **Backend**: the backend container now applies Alembic migrations on startup (`entrypoint.sh`): empty databases are migrated to head automatically, managed databases get pending revisions, and legacy pre-Alembic databases are left untouched with instructions (recreate, or `alembic stamp head`). The stale `backend/migrations/init.sql` bootstrap — integer PKs, missing `forks`/`merge_requests` — is removed; the schema comes exclusively from Alembic now.

### Fixed
- **Backend**: Alembic migrations could never run on a fresh database — the search_vector revision assumed base tables that nothing ever created. A proper baseline revision (`470ddd355943`) now creates all six tables with PostgreSQL-native types (`UUID`, `TSVECTOR`, native enum, GIN index on `search_vector`), the search revision installs only the Persian full-text trigger, and the IP%/credential revision is idempotent. Downgrade path verified.
- **Backend**: the full-text trigger referenced a non-existent `persian` text-search configuration (PostgreSQL ships none) and used `array_to_string` on a JSON column — every pamphlet insert would have failed on a real database. The baseline now creates a `persian` configuration (copied from `simple`) and the trigger indexes `tags::text`; ORM inserts and `plainto_tsquery('persian', …)` search verified end-to-end.
- **Backend**: `alembic/env.py` resolved the database URL from a stale hardcoded value; it now honors `DATABASE_URL` > app settings > `alembic.ini`. The `Settings.DATABASE_URL` default no longer contains literal `${POSTGRES_USER:-…}` shell text.
- **Backend**: `pamphlets.search_vector` is now a cross-dialect `TSVector` type (native `TSVECTOR` on PostgreSQL, `TEXT` on SQLite for the test suite) with the GIN index declared on the model; an autogenerate consistency probe confirms migrations match the ORM exactly.

### Added
- **CI**: `E2E Smoke` workflow builds both Docker images and runs `scripts/e2e_smoke.sh` against real PostgreSQL + MinIO service containers: register → login → create pamphlet → upload version → negative auth/validation checks → uploaded object verified byte-for-byte in MinIO via sha256.

### Fixed
- **Frontend**: Docker image now builds — `npm ci --only=production` omitted the devDependencies `next build` needs, the runner copied a non-existent `next.config.js`, and standalone output was referenced without `output: "standalone"` in `next.config.ts`.

### Security
- **Backend**: `PUT /api/v1/users/{id}` requires authentication and only allows the account owner to update their profile (was fully unauthenticated — IDOR). The unauthenticated `POST /api/v1/users/` duplicate registration route is removed; registration happens via `POST /api/v1/auth/register`. The dead `password` field is dropped from the profile-update schema (it was silently ignored by the service layer).

### Fixed
- **Backend**: `PamphletVersion` upload pipeline (`POST /pamphlets/{id}/versions`) was broken three ways and could never succeed: non-existent `Minio.upload_fileobj` SDK call, JSON-body field mixed into a multipart endpoint (always 422), and use of the non-existent `UploadFile.size`. Metadata now arrives as form fields; uploads are validated (allowed extensions, non-empty, 50 MB cap), stored via `put_object` with a real length, and the stored object is removed if the DB write fails.
- **Backend**: models now use SQLAlchemy 2.0 cross-dialect `Uuid` instead of the PostgreSQL-dialect type, so the SQLite-based test suite can create tables (7 tests went from collection errors to passing).

### Changed
- **Tooling**: `.gitignore` covers venvs, test DBs, tool caches, egg-info and agent-local artifacts.

## [0.2.0] - 2026-07-05
### Added
- **Backend**: Pamphlet CRUD API (`/api/v1/pamphlets/`) 
- **Backend**: Review system API (`/api/v1/reviews/`)
- **Backend**: PostgreSQL full-text search for pamphlets
- **Frontend**: Pamphlet upload page (`/pamphlets/upload`)
- **Frontend**: Pamphlet list/search page (`/pamphlets`)
- **Frontend**: Pamphlet detail page (`/pamphlets/{id}`)
- **Frontend**: Review form + display on detail page
- **Docs**: `changelog.md` and `decisions.md`
- **Version**: `VERSION` file (0.2.0)