# OpenEdu Git – Phase 1 (Pamphlet Hub) Project Status

**Phase Goal:** Launch a website where teachers can upload, categorise, search, rate, and collaboratively improve handouts.
**Timeline:** Months 1–3
**Last Updated:** 2026-08-03

| # | Task | Assigned Agent | Status | Last Update |
| --- | ------ | ---------------- | -------- | ------------- |
| 1 | Set up project infrastructure (Docker Compose, GitHub repo, CI/CD) | devops-automator | Completed | 2026-08-03 |
| 2 | Design system architecture & API contracts | software-architect | Completed | 2026-08-03 |
| 3 | Set up FastAPI backend with project structure | api-platform-engineer | In Progress | 2026-08-03 |
| 4 | Configure PostgreSQL + SQLAlchemy + Alembic | database-optimizer | In Progress | 2026-08-03 |
| 5 | Design database schema (Users, Pamphlets, Versions, Comments, Ratings, IP%) | database-optimizer | Completed | 2026-08-03 |
| 6 | Implement authentication (JWT + refresh tokens, httpOnly cookies, Google OAuth) | backend-architect | In Progress | 2026-08-03 |
| 7 | Implement User model, profile, expertise tags, credential metrics | backend-architect | In Progress | 2026-08-03 |
| 8 | Set up MinIO (S3-compatible) file storage integration | backend-architect | In Progress | 2026-08-03 |
| 9 | Build Pamphlet CRUD APIs (upload, metadata, versioning) | api-platform-engineer | In Progress | 2026-08-03 |
| 10 | Implement LaTeX storage pipeline & versioning | backend-architect | Pending | 2026-08-03 |
| 11 | Build LaTeX compiler Docker image & CI/CD pipeline | devops-automator | Pending | 2026-08-03 |
| 12 | Implement PostgreSQL full-text search (pg_trgm + tsvector) | database-optimizer | Pending | 2026-08-03 |
| 13 | Build Fork & Merge Request workflow (Git-like collaboration) | backend-architect | Pending | 2026-08-03 |
| 14 | Implement Intellectual Property percentage calculation & display | backend-architect | Pending | 2026-08-03 |
| 15 | Implement Rating & Comment system | api-platform-engineer | Pending | 2026-08-03 |
| 16 | Implement Teacher Credential system (metrics, expertise, rankings) | backend-architect | Pending | 2026-08-03 |
| 17 | Set up Next.js frontend with TypeScript, Tailwind, RTL | frontend-developer | Pending | 2026-08-03 |
| 18 | Implement design token system (colors, spacing, fonts from BRAND.md) | ui-designer | Pending | 2026-08-03 |
| 19 | Build authentication UI (login, register, profile) | frontend-developer | Pending | 2026-08-03 |
| 20 | Build Pamphlet upload UI with metadata forms | frontend-developer | Pending | 2026-08-03 |
| 21 | Build in-browser handout viewer (PDF, Markdown, LaTeX) | frontend-developer | Pending | 2026-08-03 |
| 22 | Build search UI with Persian full-text support | frontend-developer | Pending | 2026-08-03 |
| 23 | Build Pamphlet detail page (version history, IP%, ratings, comments) | frontend-developer | Pending | 2026-08-03 |
| 24 | Build Fork & Merge Request UI (GitHub-inspired) | frontend-developer | Pending | 2026-08-03 |
| 25 | Build Teacher Profile & Credential dashboard | frontend-developer | Pending | 2026-08-03 |
| 26 | Build LaTeX Editor page (Monaco + real-time PDF preview) | frontend-developer | Pending | 2026-08-03 |
| 27 | Implement responsive RTL-first layout & accessibility | ui-designer + accessibility-auditor | Pending | 2026-08-03 |
| 28 | Write backend unit & integration tests (pytest, >80% coverage) | test-automation-engineer | Pending | 2026-08-03 |
| 29 | Write frontend unit tests (Jest) & E2E tests (Playwright) | test-automation-engineer | Pending | 2026-08-03 |
| 30 | Security audit (auth, file upload, XSS, SQLi, rate limiting) | security-architect | Pending | 2026-08-03 |
| 31 | Code review of all implementations | code-reviewer | Pending | 2026-08-03 |
| 32 | Performance benchmarking (API latency, search, PDF compile) | performance-benchmarker | Pending | 2026-08-03 |
| 33 | Write API documentation (OpenAPI/Swagger) | technical-writer | Pending | 2026-08-03 |
| 34 | Write user-facing documentation (Persian/English guides) | technical-writer | Pending | 2026-08-03 |
| 35 | Compliance audit (AGPLv3, CC BY-SA 4.0, data privacy) | compliance-auditor | Pending | 2026-08-03 |
| 36 | Set up monitoring (Sentry, logging) | devops-automator | Pending | 2026-08-03 |
| 37 | Deploy to Iranian VPS (staging) | devops-automator | Pending | 2026-08-03 |
| 38 | Bootstrap content: founder uploads 5-10 initial handouts | project-shepherd | Pending | 2026-08-03 |
| 39 | Community onboarding: invite 10-15 trusted teachers | customer-success-manager | Pending | 2026-08-03 |
| 40 | Growth hacking: launch announcement, social media, SEO | growth-hacker | Pending | 2026-08-03 |
