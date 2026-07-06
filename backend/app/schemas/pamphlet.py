"""
Pydantic schemas for pamphlets.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PamphletBase(BaseModel):
    title: str
    grade: str
    subject: str
    chapter: str
    method: Optional[str] = None
    difficulty: Optional[str] = None
    is_public: int = 1
    tags: List[str] = []


class PamphletCreate(PamphletBase):
    pass


class Pamphlet(PamphletBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PamphletVersionBase(BaseModel):
    version_number: str
    notes: Optional[str] = None


class PamphletVersionCreate(PamphletVersionBase):
    pass


class PamphletVersion(PamphletVersionBase):
    id: int
    pamphlet_id: int
    file_path: str
    file_type: str
    file_size: int
    author_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PamphletFork(BaseModel):
    id: int
    original_pamphlet_id: int
    forked_by: int
    new_pamphlet_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MergeRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MergeRequestCreate(BaseModel):
    source_pamphlet_id: int
    title: str
    description: Optional[str] = None


class MergeRequestReview(BaseModel):
    review_note: Optional[str] = None


class MergeRequest(BaseModel):
    id: int
    source_pamphlet_id: int
    target_pamphlet_id: int
    status: MergeRequestStatus
    created_by: int
    reviewed_by: Optional[int] = None
    title: str
    description: Optional[str] = None
    review_note: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True