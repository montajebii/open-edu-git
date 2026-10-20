"""
Shared pytest fixtures.

The environment is configured before any application module is imported so the
app never tries to reach the real Postgres/MinIO services during tests.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("MINIO_ENDPOINT", "127.0.0.1:1")
os.environ.setdefault("PASSWORD_HASH_ROUNDS", "4")  # keep the suite fast
os.environ.setdefault("MINIO_AUTO_CREATE_BUCKETS", "false")  # no network in tests

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: F401,E402  (register every model on the metadata)
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Fresh schema per test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """TestClient wired to the test database."""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def anonymous(client):
    """A client with no session cookies (a logged-out visitor)."""
    client.cookies.clear()
    return client


@pytest.fixture
def user_payload():
    return {
        "email": "teacher@example.com",
        "password": "secret123",
        "full_name": "Teacher One",
    }


@pytest.fixture
def auth(client, user_payload):
    """Register a user and return (headers, user_json)."""
    response = client.post("/api/v1/auth/register", json=user_payload)
    assert response.status_code == 201, response.text
    body = response.json()
    login = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": user_payload["password"]},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, body
