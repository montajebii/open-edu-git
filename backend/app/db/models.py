"""
Database models for OpenEdu Git.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    title = Column(String(50))
    bio = Column(Text)
    avatar_url = Column(String(512))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    expertise_tags = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    pamphlets = relationship("Pamphlet", back_populates="author")
    reviews = relationship("Review", back_populates="user")
    forks = relationship("Fork", back_populates="forked_by")
    merge_requests = relationship("MergeRequest", back_populates="created_by")


class Pamphlet(Base):
    """Pamphlet model."""
    __tablename__ = "pamphlets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    title = Column(String(255), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    grade = Column(String(50), nullable=False)
    subject = Column(String(100), nullable=False)
    chapter = Column(String(100), nullable=False)
    method = Column(String(100))
    difficulty = Column(String(50))
    is_public = Column(Boolean, default=True)
    tags = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("User", back_populates="pamphlets")
    versions = relationship("PamphletVersion", back_populates="pamphlet")
    reviews = relationship("Review", back_populates="pamphlet")
    forks = relationship("Fork", back_populates="original_pamphlet")
    merge_requests = relationship("MergeRequest", back_populates="source_pamphlet")


class PamphletVersion(Base):
    """Pamphlet version model."""
    __tablename__ = "pamphlet_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    pamphlet_id = Column(UUID(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    pamphlet = relationship("Pamphlet", back_populates="versions")
    created_by_user = relationship("User", back_populates="created_versions")


class Review(Base):
    """Review model."""
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    pamphlet_id = Column(UUID(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    pamphlet = relationship("Pamphlet", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class Fork(Base):
    """Fork model."""
    __tablename__ = "forks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    original_pamphlet_id = Column(UUID(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    forked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    new_pamphlet_id = Column(UUID(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    original_pamphlet = relationship("Pamphlet", back_populates="forks")
    forked_by_user = relationship("User", back_populates="forks")
    new_pamphlet = relationship("Pamphlet", back_populates="forks")


class MergeRequest(Base):
    """Merge request model."""
    __tablename__ = "merge_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    source_pamphlet_id = Column(UUID(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    target_pamphlet_id = Column(UUID(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    status = Column(String(20), nullable=False)  # open, approved, rejected, merged
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    source_pamphlet = relationship("Pamphlet", back_populates="merge_requests")
    target_pamphlet = relationship("Pamphlet", back_populates="merge_requests")
    created_by_user = relationship("User", back_populates="merge_requests")
    reviewed_by_user = relationship("User", back_populates="merge_requests")