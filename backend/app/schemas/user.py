"""
Pydantic schemas for User model.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    title: str | None = None
    bio: str | None = None
    expertise_tags: list[str] = []
    avatar_url: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    title: str | None = None
    bio: str | None = None
    expertise_tags: list[str] | None = None
    avatar_url: str | None = None
    password: str | None = None


class UserInDBBase(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    expertise_tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None = None
    # Credential metrics
    pamphlet_count: int = 0
    total_downloads: int = 0
    average_rating: float = 0.0
    total_reviews: int = 0
    forks_received: int = 0
    merges_approved: int = 0
    credential_score: float = 0.0

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    password_hash: str