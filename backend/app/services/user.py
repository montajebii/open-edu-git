"""
User service for OpenEdu Git.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from ..db.models import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash, verify_password


class UserService:
    """Service for user-related operations."""

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create a new user."""
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            password_hash=hashed_password,
            full_name=user.full_name,
            title=user.title,
            bio=user.bio,
            avatar_url=user.avatar_url,
            expertise_tags=user.expertise_tags,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user(db: Session, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        """Update user."""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user."""
        user = UserService.get_user_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            return None
        return user