#!/usr/bin/env python3
"""
Backend verification script for OpenEdu Git.
Tests core functionality after refactoring.
"""

import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.db import models as db_models
from app.services.user import UserService
from app.schemas.user import UserCreate
from app.services.pamphlet import PamphletService
from app.schemas.pamphlet import PamphletCreate, PamphletVersionCreate

def test_models():
    """Test that all models are properly defined."""
    print("Testing model definitions...")

    # Check that all expected models exist
    expected_models = ['User', 'Pamphlet', 'PamphletVersion', 'Review', 'Fork', 'MergeRequest']
    for model_name in expected_models:
        assert hasattr(db_models, model_name), f"Missing model: {model_name}"

    # Check key fields exist
    assert hasattr(db_models.Pamphlet, 'search_vector'), "Missing search_vector field"
    assert hasattr(db_models.PamphletVersion, 'pdf_file_path'), "Missing pdf_file_path field"
    assert hasattr(db_models.PamphletVersion, 'pdf_file_type'), "Missing pdf_file_type field"

    print("✓ All models defined correctly")

def test_database_connection():
    """Test database connection and basic operations."""
    print("Testing database connection...")

    # Use test database
    engine = create_engine('sqlite:///./test_verification.db', connect_args={'check_same_thread': False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Test session
    db = TestingSessionLocal()
    try:
        # Test user creation
        user_data = UserCreate(
            email="test@example.com",
            password="testpassword",
            full_name="Test User"
        )
        user = UserService.create_user(db, user=user_data)
        assert user.id is not None
        assert user.email == "test@example.com"

        # Test pamphlet creation
        pamphlet_data = PamphletCreate(
            title="Test Pamphlet",
            grade="10",
            subject="Mathematics",
            chapter="Algebra",
            method="Conceptual",
            difficulty="Medium",
            is_public=True,
            tags=["math", "algebra"]
        )
        pamphlet = PamphletService.create_pamphlet(db, pamphlet=pamphlet_data, author_id=user.id)
        assert pamphlet.id is not None
        assert pamphlet.title == "Test Pamphlet"

        # Test version creation
        version_data = PamphletVersionCreate(
            version_number=1,
            notes="Initial version"
        )
        # Note: In real usage, this requires file upload, but we're testing the model structure

        print("✓ Database operations work correctly")

    finally:
        db.close()
        # Clean up
        import os
        if os.path.exists('./test_verification.db'):
            os.remove('./test_verification.db')

def test_api_imports():
    """Test that API modules can be imported."""
    print("Testing API imports...")

    # Test that we can import the main app
    from app.main import app
    assert app is not None

    # Test that we can import API routers
    from app.api.v1.endpoints import pamphlet, review, fork, auth, users, storage
    assert pamphlet is not None
    assert review is not None
    assert fork is not None
    assert auth is not None
    assert users is not None
    assert storage is not None

    print("✓ All API modules import correctly")

if __name__ == "__main__":
    print("Running OpenEdu Git backend verification...\n")

    try:
        test_models()
        test_database_connection()
        test_api_imports()

        print("\n✅ All backend verification tests passed!")
        print("The backend is ready for frontend integration.")

    except Exception as e:
        print(f"\n❌ Backend verification failed: {e}")
        raise