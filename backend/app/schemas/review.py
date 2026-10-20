"""
Pydantic schemas for reviews.
"""

from datetime import datetime

from pydantic import BaseModel

from .pamphlet import UserBrief


class ReviewBase(BaseModel):
    rating: int
    comment: str | None = None


class ReviewCreate(ReviewBase):
    pass


class Review(ReviewBase):
    id: int
    pamphlet_id: int
    user_id: int
    user: UserBrief | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
