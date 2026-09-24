"""
Tests for pamphlet file upload validation.

These tests mock the MinIO client so no storage server is required;
they exercise the validation, rollback and DB-write logic of
POST /pamphlets/{id}/versions.
"""

import uuid
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.schemas.user import UserCreate
from app.services.user import UserService

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    try:
        user_data = UserCreate(
            email=f"{uuid.uuid4()}@example.com",
            password="testpassword",
            full_name="Upload User",
        )
        yield UserService.create_user(db, user=user_data)
    finally:
        db.close()


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fake_minio(monkeypatch):
    """Replace the MinIO client used by the pamphlet endpoints with a mock."""
    mock = MagicMock()
    monkeypatch.setattr("app.api.v1.endpoints.pamphlet.minio_client", mock)
    return mock


def _create_pamphlet(auth_headers: dict) -> str:
    response = client.post(
        "/api/v1/pamphlets/",
        json={
            "title": "Test Pamphlet",
            "grade": "10",
            "subject": "Math",
            "chapter": "Algebra",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_upload_version_rejects_disallowed_extension(auth_headers, fake_minio):
    pamphlet_id = _create_pamphlet(auth_headers)
    response = client.post(
        f"/api/v1/pamphlets/{pamphlet_id}/versions",
        files={"file": ("evil.exe", BytesIO(b"MZ..."), "application/x-msdownload")},
        data={"version_number": "1"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    fake_minio.upload_file.assert_not_called()


def test_upload_version_success_passes_length_and_creates_row(auth_headers, fake_minio):
    pamphlet_id = _create_pamphlet(auth_headers)
    content = b"%PDF-1.4 minimal pdf content"
    response = client.post(
        f"/api/v1/pamphlets/{pamphlet_id}/versions",
        files={"file": ("notes.pdf", BytesIO(content), "application/pdf")},
        data={"version_number": "1", "notes": "first"},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text

    fake_minio.upload_file.assert_called_once()
    kwargs = fake_minio.upload_file.call_args.kwargs
    assert kwargs["length"] == len(content)
    assert kwargs["content_type"] == "application/pdf"
    assert kwargs["object_name"].startswith(f"pamphlets/{pamphlet_id}/")

    body = response.json()
    assert body["file_size"] == len(content)
    assert body["version_number"] == 1


def test_upload_version_forbidden_for_non_author(auth_headers, fake_minio):
    pamphlet_id = _create_pamphlet(auth_headers)

    # A second, real user so the token resolves but lacks ownership
    db = TestingSessionLocal()
    try:
        other = UserService.create_user(
            db,
            user=UserCreate(
                email=f"{uuid.uuid4()}@example.com",
                password="testpassword",
                full_name="Other User",
            ),
        )
        other_token = create_access_token(data={"sub": str(other.id)})
    finally:
        db.close()
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = client.post(
        f"/api/v1/pamphlets/{pamphlet_id}/versions",
        files={"file": ("notes.pdf", BytesIO(b"content"), "application/pdf")},
        data={"version_number": "1"},
        headers=other_headers,
    )
    assert response.status_code == 403
    fake_minio.upload_file.assert_not_called()
