# OpenEdu Git Tests

Test suite for OpenEdu Git backend and frontend.

## Backend Tests
Located in `backend/tests/`.
- **Unit Tests**: Test individual functions and models.
- **Integration Tests**: Test API endpoints and database interactions.
- **Fixtures**: Reusable test data (e.g., test users, pamphlets).

**Run Tests:**
```bash
cd backend
pytest
```

## Frontend Tests
Located in `frontend/src/` (e.g., `__tests__/`).
- **Unit Tests**: Test React components with Jest.
- **E2E Tests**: Test user flows with Playwright.

**Run Tests:**
```bash
cd frontend
npm test
```

## CI/CD
Tests run automatically on GitHub Actions for every push and PR.