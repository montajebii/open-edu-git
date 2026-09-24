"""
Tests for user endpoints.
"""

import uuid

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

# Use a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency
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
    """Set up the test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Get a database session for fixtures."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    unique_id = uuid.uuid4()
    user_data = UserCreate(
        email=f"{unique_id}@example.com",
        password="testpassword",
        full_name="Test User",
        expertise_tags=[],
        avatar_url=None,
    )
    return UserService.create_user(db_session, user=user_data)


def _auth_headers(user) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_register_route_removed():
    """The duplicate unauthenticated registration route is gone."""
    response = client.post(
        "/api/v1/users/",
        json={
            "email": "newuser@example.com",
            "password": "newpassword",
            "full_name": "New User",
        },
    )
    assert response.status_code == 404


def test_get_user(test_user):
    """Public profile lookup stays available without auth."""
    response = client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email


def test_update_user_requires_auth(test_user):
    """Unauthenticated update attempts are rejected."""
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json={"full_name": "Hijacked Name"},
    )
    assert response.status_code == 401


def test_update_user_forbidden_for_other_user(test_user):
    """Authenticated users cannot update someone else's profile."""
    db = TestingSessionLocal()
    try:
        attacker = UserService.create_user(
            db,
            user=UserCreate(
                email=f"{uuid.uuid4()}@example.com",
                password="testpassword",
                full_name="Attacker",
            ),
        )
    finally:
        db.close()

    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json={"full_name": "Hijacked Name"},
        headers=_auth_headers(attacker),
    )
    assert response.status_code == 403


def test_update_user_by_owner(test_user):
    """The owner can update their own profile."""
    update_data = {
        "full_name": "Updated User",
        "bio": "This is an updated bio",
    }
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json=update_data,
        headers=_auth_headers(test_user),
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == update_data["full_name"]
    assert response.json()["bio"] == update_data["bio"]


def test_update_user_ignores_password_field(test_user):
    """Password is not part of the update contract at all."""
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json={"full_name": "Still Updated", "password": "sneaky"},
        headers=_auth_headers(test_user),
    )
    assert response.status_code == 200
    assert "password" not in response.json()
