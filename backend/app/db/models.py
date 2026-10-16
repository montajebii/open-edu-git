"""
Database models for OpenEdu Git.

This is the canonical location for SQLAlchemy models. The
``app.models.*`` modules re-export these for backward compatibility.
"""

import uuid
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index

from .base import Base
from .types import TSVector


class MergeRequestStatus(str, Enum):
    """Merge request status enum."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    title = Column(String(50))
    bio = Column(Text)
    avatar_url = Column(String(512))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    expertise_tags = Column(JSON, default=[])
    # Teacher credential metrics
    pamphlet_count = Column(Integer, default=0)
    total_downloads = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    forks_received = Column(Integer, default=0)
    merges_approved = Column(Integer, default=0)
    # Composite credential score (0-100) calculated from above metrics
    credential_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    pamphlets = relationship("Pamphlet", back_populates="author")
    reviews = relationship("Review", back_populates="user")
    forks = relationship("Fork", back_populates="forked_by_user")
    merge_requests_created = relationship(
        "MergeRequest", foreign_keys="MergeRequest.created_by", back_populates="created_by_user"
    )
    merge_requests_reviewed = relationship(
        "MergeRequest", foreign_keys="MergeRequest.reviewed_by", back_populates="reviewed_by_user"
    )
    created_versions = relationship("PamphletVersion", back_populates="created_by_user")


class Pamphlet(Base):
    """Pamphlet model."""

    __tablename__ = "pamphlets"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    author_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    grade = Column(String(50), nullable=False)
    subject = Column(String(100), nullable=False)
    chapter = Column(String(100), nullable=False)
    method = Column(String(100))
    difficulty = Column(String(50))
    is_public = Column(Boolean, default=True)
    tags = Column(JSON, default=[])
    search_vector = Column(TSVector)  # tsvector on PG; trigger-maintained for FTS
    # IP% represents the percentage of intellectual property from the original author
    # For directly authored pamphlets, this starts at 100.0
    # For forked pamphlets, it decreases as more contributors add content
    original_author_ip_percentage = Column(Float, default=100.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index(
            "ix_pamphlets_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    # Relationships
    author = relationship("User", back_populates="pamphlets")
    versions = relationship("PamphletVersion", back_populates="pamphlet")
    reviews = relationship("Review", back_populates="pamphlet")
    forks = relationship(
        "Fork", foreign_keys="Fork.original_pamphlet_id", back_populates="original_pamphlet"
    )
    forks_created = relationship(
        "Fork", foreign_keys="Fork.new_pamphlet_id", back_populates="new_pamphlet"
    )
    merge_requests_created = relationship(
        "MergeRequest",
        foreign_keys="MergeRequest.source_pamphlet_id",
        back_populates="source_pamphlet",
    )
    merge_requests_received = relationship(
        "MergeRequest",
        foreign_keys="MergeRequest.target_pamphlet_id",
        back_populates="target_pamphlet",
    )


class PamphletVersion(Base):
    """Pamphlet version model."""

    __tablename__ = "pamphlet_versions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pamphlet_id = Column(Uuid(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    notes = Column(Text)
    author_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    pdf_file_path = Column(String(512), nullable=True)
    pdf_file_type = Column(String(50), nullable=True)

    # Relationships
    pamphlet = relationship("Pamphlet", back_populates="versions")
    created_by_user = relationship("User", back_populates="created_versions")


class Review(Base):
    """Review model."""

    __tablename__ = "reviews"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pamphlet_id = Column(Uuid(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    pamphlet = relationship("Pamphlet", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class Fork(Base):
    """Fork model."""

    __tablename__ = "forks"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_pamphlet_id = Column(Uuid(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    forked_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    new_pamphlet_id = Column(Uuid(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    original_pamphlet = relationship("Pamphlet", foreign_keys=[original_pamphlet_id])
    forked_by_user = relationship("User", foreign_keys=[forked_by], back_populates="forks")
    new_pamphlet = relationship("Pamphlet", foreign_keys=[new_pamphlet_id])


class MergeRequest(Base):
    """Merge request model."""

    __tablename__ = "merge_requests"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_pamphlet_id = Column(Uuid(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    target_pamphlet_id = Column(Uuid(as_uuid=True), ForeignKey("pamphlets.id"), nullable=False)
    status = Column(
        SQLEnum(MergeRequestStatus, values_callable=lambda x: [e.value for e in x]),
        default=MergeRequestStatus.PENDING,
        nullable=False,
    )
    created_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    review_note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    source_pamphlet = relationship(
        "Pamphlet", foreign_keys=[source_pamphlet_id], back_populates="merge_requests_created"
    )
    target_pamphlet = relationship("Pamphlet", foreign_keys=[target_pamphlet_id])
    created_by_user = relationship(
        "User", foreign_keys=[created_by], back_populates="merge_requests_created"
    )
    reviewed_by_user = relationship(
        "User", foreign_keys=[reviewed_by], back_populates="merge_requests_reviewed"
    )
