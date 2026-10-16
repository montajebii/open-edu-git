"""
Pamphlet endpoints for OpenEdu Git.
"""

import os
import uuid
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.minio_client import minio_client
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.pamphlet import Pamphlet as PamphletModel
from app.models.pamphlet import PamphletVersion as PamphletVersionModel
from app.models.user import User as UserModel
from app.schemas.pamphlet import Pamphlet, PamphletCreate, PamphletVersion

router = APIRouter()

# Allowed upload types and size cap (50 MB)
ALLOWED_FILE_EXTENSIONS = {".pdf", ".md", ".tex", ".docx", ".zip"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


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
async def create_pamphlet_version(
    pamphlet_id: uuid.UUID,
    version_number: int = Form(..., ge=1),
    notes: str | None = Form(None),
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

    # Validate file type and size before touching storage
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file_ext or 'unknown'}' not allowed. "
            f"Allowed: {sorted(ALLOWED_FILE_EXTENSIONS)}",
        )

    file_data = await file.read()
    if len(file_data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty"
        )
    if len(file_data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB",
        )

    # Upload file to MinIO
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = f"pamphlets/{pamphlet_id}/{file_name}"

    try:
        minio_client.upload_file(
            file_data=BytesIO(file_data),
            bucket_name=settings.MINIO_BUCKET_PAMPHLETS,
            object_name=file_path,
            length=len(file_data),
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}",
        ) from None

    # Create version; roll back the stored object if the DB write fails
    db_version = PamphletVersionModel(
        pamphlet_id=pamphlet_id,
        version_number=version_number,
        file_path=file_path,
        file_type=file.content_type or "application/octet-stream",
        file_size=len(file_data),
        notes=notes,
        author_id=current_user.id,
    )
    db.add(db_version)
    try:
        db.commit()
    except Exception:
        db.rollback()
        minio_client.remove_file(settings.MINIO_BUCKET_PAMPHLETS, file_path)
        raise
    db.refresh(db_version)

    return db_version


@router.get("/{pamphlet_id}", response_model=Pamphlet)
def get_pamphlet(pamphlet_id: uuid.UUID, db: Session = Depends(get_db)):
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

    # Full-text search using the precomputed search_vector column
    if search:
        from sqlalchemy import func

        query = query.filter(
            PamphletModel.search_vector.op("@@")(func.plainto_tsquery("persian", search))
        )

    return query.all()
