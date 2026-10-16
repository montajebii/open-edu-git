"""Verification token model for OpenEdu Git."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.base import Base


class VerificationToken(Base):
    """Verification token model (for email verification)."""

    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    purpose = Column(String(50), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
