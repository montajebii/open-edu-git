# OpenEdu Git – Phase 1 (Pamphlet Hub) Project Status

**Phase Goal:** Launch a website where teachers can upload, categorise, search, rate, and collaboratively improve handouts.
**Timeline:** Months 1–3
**Last Updated:** 2026-10-20

Status values: `Completed` = implemented **and** verified by tests/checks, `In Progress` = partially implemented, `Pending` = not started.

## What is verified

The following checks were executed on this date and pass:

| Check | Result |
| --- | --- |
| `pytest` (backend, SQLite) | 41 passed |
| `ruff check` + `ruff format --check` | clean |
| `tsc --noEmit` + `eslint` (frontend) | clean |
| `next build` (10 pages) | OK |
| `docker compose config` | OK (refuses to start without `SECRET_KEY`) |
| `init.sql` against a **real PostgreSQL** | applies cleanly; schema matches the SQLAlchemy models exactly; `search_vector` trigger fires; full HTTP flow (register → login → create → search → refresh → logout → revoked refresh rejected) |
| Live API flow over HTTP (uvicorn) | register/login/me/create/search pass |

Run `python scripts/validate_init_sql.py` (needs `pip install pgserver`) to repeat the PostgreSQL validation locally.

## Known gaps (honest list)

- **No Alembic migrations.** `backend/migrations/init.sql` is the schema source of truth; there is no versioned migration chain yet (see DECISIONS #21).
- **No Google OAuth** (planned for later, see DECISIONS #4).
- **No rate limiting, no E2E tests, no deployment.**
- **MinIO integration is code-complete but untested against a live MinIO** in this environment (no Docker daemon available); uploads use a mocked storage in tests.
- **The tsvector column exists in `init.sql` but the API search uses `ILIKE`**; Persian stemming is deferred (DECISIONS #6).
- **Backend tests run on SQLite**; CI provisions Postgres but the test fixtures override the DB URL. `scripts/validate_init_sql.py` covers that gap manually.

## Task table

| # | Task | Status | Notes |
| --- | ------ | ------ | ------------- |
| 1 | Set up project infrastructure (Docker Compose, GitHub repo, CI/CD) | Completed | Compose refuses to boot without `SECRET_KEY`; CI workflows exist |
| 2 | Design system architecture & API contracts | Completed | ARCHITECTURE.md |
| 3 | Set up FastAPI backend with project structure | Completed | boots; `/health`, `/docs` verified |
| 4 | Configure PostgreSQL + SQLAlchemy (+ Alembic) | In Progress | PostgreSQL validated via init.sql; **Alembic not set up** |
| 5 | Design database schema (Users, Pamphlets, Versions, Comments, Ratings) | Completed | init.sql matches models exactly |
| 6 | Implement authentication (JWT + refresh, httpOnly cookies; OAuth later) | In Progress | password auth + cookies + refresh **revocation on logout** done; email verification flow done; Google OAuth pending |
| 7 | Implement User model, profile | Completed | `/users/me` update restricted to the owner |
| 8 | Set up MinIO (S3-compatible) file storage integration | In Progress | lazy client, buckets ensured at start-up; not tested against live MinIO |
| 9 | Build Pamphlet CRUD APIs (upload, metadata, versioning) | Completed | multipart upload with size/type limits |
| 10 | Implement LaTeX storage pipeline & versioning | Pending | |
| 11 | Build LaTeX compiler Docker image & CI/CD pipeline | Pending | |
| 12 | Implement PostgreSQL full-text search | In Progress | `tsvector` + trigger in init.sql; API search uses escaped `ILIKE`; `pg_trgm` removed (unused) |
| 13 | Build Fork & Merge Request workflow | In Progress | backend endpoints + tests done; no UI |
| 14 | Implement Intellectual Property percentage calculation & display | Pending | |
| 15 | Implement Rating & Comment system | Completed | API + detail-page UI |
| 16 | Implement Teacher Credential system (metrics, expertise, rankings) | Pending | |
| 17 | Set up Next.js frontend with TypeScript, Tailwind, RTL | Completed | Next 16, RTL layout |
| 18 | Implement design token system (from BRAND.md) | In Progress | basic globals.css only |
| 19 | Build authentication UI (login, register, profile) | In Progress | login/register/verify-email done (cookie-based); profile page missing |
| 20 | Build Pamphlet upload UI with metadata forms | Completed | |
| 21 | Build in-browser handout viewer (PDF, Markdown, LaTeX) | Pending | |
| 22 | Build search UI with Persian full-text support | In Progress | grade/subject/chapter filters work |
| 23 | Build Pamphlet detail page (version history, IP%, ratings, comments) | In Progress | ratings/comments done; version history and IP% missing |
| 24 | Build Fork & Merge Request UI | Pending | |
| 25 | Build Teacher Profile & Credential dashboard | Pending | |
| 26 | Build LaTeX Editor page (Monaco + real-time PDF preview) | Pending | |
| 27 | Implement responsive RTL-first layout & accessibility | Pending | |
| 28 | Write backend unit & integration tests | In Progress | 41 tests pass; coverage target not measured |
| 29 | Write frontend unit tests (Jest) & E2E tests (Playwright) | Pending | |
| 30 | Security audit (auth, upload, XSS, SQLi, rate limiting) | In Progress | fixes applied: required `SECRET_KEY`, cookie flags, ownership checks, typed tokens, upload limits; **rate limiting missing** |
| 31 | Code review of all implementations | Pending | |
| 32 | Performance benchmarking | Pending | |
| 33 | Write API documentation (OpenAPI/Swagger) | In Progress | served at `/docs`; no written guide yet |
| 34 | Write user-facing documentation (Persian/English guides) | Pending | |
| 35 | Compliance audit (AGPLv3, CC BY-SA 4.0, data privacy) | Pending | |
| 36 | Set up monitoring (Sentry, logging) | In Progress | Sentry SDK wired, DSN optional; structured logging pending |
| 37 | Deploy to Iranian VPS (staging) | Pending | |
| 38 | Bootstrap content: founder uploads 5-10 initial handouts | Pending | |
| 39 | Community onboarding: invite 10-15 trusted teachers | Pending | |
| 40 | Growth hacking: launch announcement, social media, SEO | Pending | |
