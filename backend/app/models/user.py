"""
User model for OpenEdu Git.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    title = Column(String(255))  # e.g., "ریاضی", "فیزیک", "برنامه‌نویس"
    bio = Column(Text)
    avatar_url = Column(String(255))  # URL to avatar in MinIO
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    is_verified = Column(Integer, default=0)  # 1 = verified, 0 = not verified
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())