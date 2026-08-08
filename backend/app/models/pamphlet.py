"""
Pamphlet and PamphletVersion models for OpenEdu Git.
"""

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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
    file_size = Column(Integer, nullable=False)
    notes = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    author = relationship("User", backref="created_versions")


class MergeRequestStatus(str, Enum):
    """Merge request status enum."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PamphletFork(Base):
    """Pamphlet fork model."""

    __tablename__ = "pamphlet_forks"

    id = Column(Integer, primary_key=True, index=True)
    original_pamphlet_id = Column(Integer, ForeignKey("pamphlets.id"), nullable=False)
    forked_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    new_pamphlet_id = Column(Integer, ForeignKey("pamphlets.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    original = relationship("Pamphlet", foreign_keys=[original_pamphlet_id], backref="forks")
    forked_by_user = relationship("User", backref="forks")
    new_pamphlet = relationship("Pamphlet", foreign_keys=[new_pamphlet_id], backref="forked_from")


class MergeRequest(Base):
    """Merge request model."""

    __tablename__ = "merge_requests"

    id = Column(Integer, primary_key=True, index=True)
    source_pamphlet_id = Column(Integer, ForeignKey("pamphlets.id"), nullable=False)
    target_pamphlet_id = Column(Integer, ForeignKey("pamphlets.id"), nullable=False)
    status = Column(
        Enum(MergeRequestStatus, values_callable=lambda x: [e.value for e in x]),
        default=MergeRequestStatus.PENDING,
        nullable=False,
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    review_note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    source = relationship(
        "Pamphlet", foreign_keys=[source_pamphlet_id], backref="merge_requests_sent"
    )
    target = relationship(
        "Pamphlet", foreign_keys=[target_pamphlet_id], backref="merge_requests_received"
    )
    creator = relationship("User", foreign_keys=[created_by], backref="merge_requests_created")
    reviewer = relationship("User", foreign_keys=[reviewed_by], backref="merge_requests_reviewed")
