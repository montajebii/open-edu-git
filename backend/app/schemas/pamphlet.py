"""
Pydantic schemas for pamphlets.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


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