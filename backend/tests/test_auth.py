"""
Tests for authentication endpoints.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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


# Create test client
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Set up the test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """Create a test user."""
    db = TestingSessionLocal()
    unique_id = uuid.uuid4()
    user_data = UserCreate(
        email=f"{unique_id}@example.com",
        password="testpassword",
        full_name="Test User",
        expertise_tags=[],
        avatar_url=None,
    )
    db_user = UserService.create_user(db, user=user_data)
    db.close()
    yield db_user
    # Cleanup
    db = TestingSessionLocal()
    db.delete(db.query(UserModel := __import__("app.models.user", fromlist=["User"]).User).filter_by(id=db_user.id).one())
    db.commit()
    db.close()


def test_register_user():
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "newpassword",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    assert response.json()["email"] == "newuser@example.com"


def test_login_user(test_user):
    """Test user login."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_get_current_user(test_user):
    """Test getting current user via Authorization header."""
    # First login to get tokens
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword",
        },
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens

    # Then get current user using Bearer token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email


def test_logout_user(test_user):
    """Test user logout."""
    # First login to get cookies
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword",
        },
    )
    assert login_response.status_code == 200

    # Then logout
    response = client.post(
        "/api/v1/auth/logout",
        cookies=login_response.cookies,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
