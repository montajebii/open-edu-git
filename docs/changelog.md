# Changelog

## [Unreleased]
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