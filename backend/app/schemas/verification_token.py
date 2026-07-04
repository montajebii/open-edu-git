"""
Pydantic schemas for VerificationToken model.
"""

from pydantic import BaseModel
from datetime import datetime


class VerificationTokenBase(BaseModel):
    user_id: int
    token: str
    purpose: str
    expires_at: datetime


class VerificationTokenCreate(VerificationTokenBase):
    pass


class VerificationToken(VerificationTokenBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True