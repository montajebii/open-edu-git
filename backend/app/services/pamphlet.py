"""
Pamphlet service for OpenEdu Git.
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from ..db.models import Pamphlet, PamphletVersion
from ..schemas.pamphlet import PamphletCreate, PamphletUpdate


class PamphletService:
    """Service for pamphlet-related operations."""

    @staticmethod
    def create_pamphlet(db: Session, pamphlet: PamphletCreate, author_id: UUID) -> Pamphlet:
        """Create a new pamphlet."""
        db_pamphlet = Pamphlet(
            title=pamphlet.title,
            author_id=author_id,
            grade=pamphlet.grade,
            subject=pamphlet.subject,
            chapter=pamphlet.chapter,
            method=pamphlet.method,
            difficulty=pamphlet.difficulty,
            is_public=pamphlet.is_public,
            tags=pamphlet.tags,
        )
        db.add(db_pamphlet)
        db.commit()
        db.refresh(db_pamphlet)
        return db_pamphlet

    @staticmethod
    def get_pamphlet_by_id(db: Session, pamphlet_id: UUID) -> Optional[Pamphlet]:
        """Get pamphlet by ID."""
        return db.query(Pamphlet).filter(Pamphlet.id == pamphlet_id).first()

    @staticmethod
    def get_pamphlets_by_author(db: Session, author_id: UUID, skip: int = 0, limit: int = 100) -> List[Pamphlet]:
        """Get pamphlets by author."""
        return db.query(Pamphlet).filter(Pamphlet.author_id == author_id).offset(skip).limit(limit).all()

    @staticmethod
    def update_pamphlet(db: Session, pamphlet_id: UUID, pamphlet_update: PamphletUpdate) -> Optional[Pamphlet]:
        """Update pamphlet."""
        db_pamphlet = PamphletService.get_pamphlet_by_id(db, pamphlet_id)
        if not db_pamphlet:
            return None

        update_data = pamphlet_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_pamphlet, field, value)

        db.commit()
        db.refresh(db_pamphlet)
        return db_pamphlet

    @staticmethod
    def create_pamphlet_version(db: Session, pamphlet_id: UUID, version_number: int, file_path: str, file_type: str, created_by: UUID) -> PamphletVersion:
        """Create a new version of a pamphlet."""
        db_version = PamphletVersion(
            pamphlet_id=pamphlet_id,
            version_number=version_number,
            file_path=file_path,
            file_type=file_type,
            created_by=created_by,
        )
        db.add(db_version)
        db.commit()
        db.refresh(db_version)
        return db_version