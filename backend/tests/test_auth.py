"""
Tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings
from app.services.user import UserService
from app.schemas.user import UserCreate


# Use a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
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
def test_user(db):
    """Create a test user."""
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword",
        full_name="Test User",
    )
    return UserService.create_user(db, user=user_data)


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
    assert response.json()["message"] == "Login successful"


def test_get_current_user(test_user):
    """Test getting current user."""
    # First login to get cookies
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword",
        },
    )
    assert login_response.status_code == 200
    
    # Then get current user
    response = client.get(
        "/api/v1/auth/me",
        cookies=login_response.cookies,
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