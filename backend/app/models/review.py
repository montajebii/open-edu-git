"""
Review model for OpenEdu Git.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class Review(Base):
    """Review model."""
    
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    pamphlet_id = Column(Integer, ForeignKey("pamphlets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())