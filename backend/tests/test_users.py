"""
Tests for user endpoints.
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
    import uuid
    unique_id = uuid.uuid4()
    user_data = UserCreate(
        email=f"{unique_id}@example.com",
        password="testpassword",
        full_name="Test User",
        expertise_tags=[],
        avatar_url=None,
    )
    return UserService.create_user(db_session, user=user_data)


def test_create_user():
    """Test creating a new user."""
    response = client.post(
        "/api/v1/users/",
        json={
            "email": "newuser@example.com",
            "password": "newpassword",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    assert response.json()["email"] == "newuser@example.com"


def test_get_user(test_user):
    """Test getting a user by ID."""
    response = client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email


def test_update_user(test_user):
    """Test updating a user."""
    update_data = {
        "full_name": "Updated User",
        "bio": "This is an updated bio",
    }
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json=update_data,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == update_data["full_name"]
    assert response.json()["bio"] == update_data["bio"]
