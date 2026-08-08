"""
Pamphlet endpoints for OpenEdu Git.
"""

import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.minio_client import minio_client
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.pamphlet import Pamphlet as PamphletModel
from app.models.pamphlet import PamphletVersion as PamphletVersionModel
from app.models.user import User as UserModel
from app.schemas.pamphlet import Pamphlet, PamphletCreate, PamphletVersion, PamphletVersionCreate

router = APIRouter()


@router.post("/", response_model=Pamphlet)
def create_pamphlet(
    pamphlet: PamphletCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new pamphlet."""
    # Create pamphlet
    db_pamphlet = PamphletModel(
        title=pamphlet.title,
        author_id=current_user.id,
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


@router.post("/{pamphlet_id}/versions", response_model=PamphletVersion)
def create_pamphlet_version(
    pamphlet_id: int,
    version: PamphletVersionCreate,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Upload a new version of a pamphlet."""
    # Check pamphlet exists and user is author
    db_pamphlet = db.query(PamphletModel).filter(PamphletModel.id == pamphlet_id).first()
    if not db_pamphlet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pamphlet not found")
    if db_pamphlet.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # Upload file to MinIO
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = f"pamphlets/{pamphlet_id}/{file_name}"

    try:
        minio_client.upload_fileobj(file.file, settings.MINIO_BUCKET_PAMPHLETS, file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}",
        ) from None

    # Create version
    db_version = PamphletVersionModel(
        pamphlet_id=pamphlet_id,
        version_number=version.version_number,
        file_path=file_path,
        file_type=file.content_type,
        file_size=file.size,
        notes=version.notes,
        author_id=current_user.id,
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)

    return db_version


@router.get("/{pamphlet_id}", response_model=Pamphlet)
def get_pamphlet(pamphlet_id: int, db: Session = Depends(get_db)):
    """Get a pamphlet by ID."""
    db_pamphlet = db.query(PamphletModel).filter(PamphletModel.id == pamphlet_id).first()
    if not db_pamphlet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pamphlet not found")
    return db_pamphlet


@router.get("/", response_model=list[Pamphlet])
def list_pamphlets(
    grade: str = None,
    subject: str = None,
    chapter: str = None,
    search: str = None,
    db: Session = Depends(get_db),
):
    """List pamphlets with optional filters and full-text search."""
    query = db.query(PamphletModel)

    # Basic filters
    if grade:
        query = query.filter(PamphletModel.grade == grade)
    if subject:
        query = query.filter(PamphletModel.subject == subject)
    if chapter:
        query = query.filter(PamphletModel.chapter == chapter)

    # Full-text search
    if search:
        search_vector = (
            PamphletModel.title
            + " "
            + PamphletModel.subject
            + " "
            + PamphletModel.chapter
            + " "
            + func.array_to_string(PamphletModel.tags, " ")
        )
        query = query.filter(search_vector.op("@@")(func.plainto_tsquery("simple", search)))

    return query.all()
