"""
Pydantic schemas for VerificationToken model.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class VerificationTokenBase(BaseModel):
    user_id: UUID
    token: str
    purpose: str
    expires_at: datetime


class VerificationTokenCreate(VerificationTokenBase):
    pass


class VerificationToken(VerificationTokenBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
