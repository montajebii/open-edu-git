"""
Pydantic schemas for pamphlets.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class PamphletBase(BaseModel):
    title: str
    grade: str
    subject: str
    chapter: str
    method: str | None = None
    difficulty: str | None = None
    is_public: int = 1
    tags: list[str] = []


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
    notes: str | None = None


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


class MergeRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MergeRequestCreate(BaseModel):
    source_pamphlet_id: int
    title: str
    description: str | None = None


class MergeRequestReview(BaseModel):
    review_note: str | None = None


class MergeRequest(BaseModel):
    id: int
    source_pamphlet_id: int
    target_pamphlet_id: int
    status: MergeRequestStatus
    created_by: int
    reviewed_by: int | None = None
    title: str
    description: str | None = None
    review_note: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None

    class Config:
        from_attributes = True
