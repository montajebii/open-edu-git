"""
Pydantic schemas for pamphlets.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class PamphletBase(BaseModel):
    title: str
    grade: str
    subject: str
    chapter: str
    method: str | None = None
    difficulty: str | None = None
    is_public: bool = True
    tags: list[str] = []


class PamphletCreate(PamphletBase):
    pass


class PamphletUpdate(BaseModel):
    title: str | None = None
    grade: str | None = None
    subject: str | None = None
    chapter: str | None = None
    method: str | None = None
    difficulty: str | None = None
    is_public: bool | None = None
    tags: list[str] | None = None


class Pamphlet(PamphletBase):
    id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    # IP% field
    original_author_ip_percentage: float = 100.0

    class Config:
        from_attributes = True


class PamphletVersionBase(BaseModel):
    version_number: int
    notes: str | None = None


class PamphletVersionCreate(PamphletVersionBase):
    pass


class PamphletVersion(PamphletVersionBase):
    id: UUID
    pamphlet_id: UUID
    file_path: str
    file_type: str
    file_size: int
    pdf_file_path: str | None = None
    pdf_file_type: str | None = None
    author_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class PamphletFork(BaseModel):
    id: UUID
    original_pamphlet_id: UUID
    forked_by: UUID
    new_pamphlet_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MergeRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MergeRequestCreate(BaseModel):
    source_pamphlet_id: UUID
    title: str
    description: str | None = None


class MergeRequestReview(BaseModel):
    review_note: str | None = None


class MergeRequest(BaseModel):
    id: UUID
    source_pamphlet_id: UUID
    target_pamphlet_id: UUID
    status: MergeRequestStatus
    created_by: UUID
    reviewed_by: UUID | None = None
    title: str
    description: str | None = None
    review_note: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    reviewed_at: datetime | None = None

    class Config:
        from_attributes = True