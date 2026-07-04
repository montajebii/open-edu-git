"""
Pamphlet and PamphletVersion models for OpenEdu Git.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Pamphlet(Base):
    """Pamphlet model."""
    
    __tablename__ = "pamphlets"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    grade = Column(String(50), nullable=False)  # e.g., "دهم", "یازدهم"
    subject = Column(String(100), nullable=False)  # e.g., "ریاضی", "فیزیک"
    chapter = Column(String(100), nullable=False)  # e.g., "مشتق", "الکتریسیته"
    method = Column(String(100))  # e.g., "مفهومی", "کنکوری", "حل مسئله"
    difficulty = Column(String(50))  # e.g., "آسان", "متوسط", "سخت"
    is_public = Column(Integer, default=1)  # 1 = public, 0 = private
    tags = Column(JSON, default=[])  # e.g., ["کنکوری", "مثال‌محور"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("User", backref="pamphlets")
    versions = relationship("PamphletVersion", backref="pamphlet", cascade="all, delete-orphan")
    reviews = relationship("Review", backref="pamphlet", cascade="all, delete-orphan")


class PamphletVersion(Base):
    """Pamphlet version model."""
    
    __tablename__ = "pamphlet_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    pamphlet_id = Column(Integer, ForeignKey("pamphlets.id"), nullable=False)
    version_number = Column(Integer, nullable=False)  # e.g., 1, 2, 3
    file_path = Column(String(512), nullable=False)  # Path in MinIO
    file_type = Column(String(50), nullable=False)  # e.g., "pdf", "docx", "md"
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    creator = relationship("User", backref="created_versions")