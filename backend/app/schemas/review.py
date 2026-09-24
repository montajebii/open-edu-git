"""
Pydantic schemas for reviews.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReviewBase(BaseModel):
    rating: int  # 1-5
    comment: str | None = None


class ReviewCreate(ReviewBase):
    pass


class Review(ReviewBase):
    id: UUID
    pamphlet_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
