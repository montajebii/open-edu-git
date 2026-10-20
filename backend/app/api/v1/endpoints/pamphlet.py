"""
Pamphlet endpoints for OpenEdu Git.
"""

import os
import uuid
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from ....core.config import settings
from ....core.minio_client import minio_client
from ....core.security import get_current_user, get_optional_user
from ....db.session import get_db
from ....models.pamphlet import Pamphlet as PamphletModel
from ....models.pamphlet import PamphletVersion as PamphletVersionModel
from ....models.user import User as UserModel
from ....schemas.pamphlet import Pamphlet, PamphletCreate, PamphletVersion

router = APIRouter()


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards so user input is matched literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _visible_to(user: UserModel | None):
    """Filter clause: public pamphlets, plus the caller's own private ones."""
    if user is None:
        return PamphletModel.is_public == 1
    return or_(PamphletModel.is_public == 1, PamphletModel.author_id == user.id)


@router.post("/", response_model=Pamphlet, status_code=status.HTTP_201_CREATED)
def create_pamphlet(
    pamphlet: PamphletCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new pamphlet."""
    db_pamphlet = PamphletModel(
        title=pamphlet.title,
        author_id=current_user.id,
        grade=pamphlet.grade,
        subject=pamphlet.subject,
        chapter=pamphlet.chapter,
        method=pamphlet.method,
        difficulty=pamphlet.difficulty,
        is_public=pamphlet.is_public,
        tags=pamphlet.tags or [],
    )
    db.add(db_pamphlet)
    db.commit()
    db.refresh(db_pamphlet)
    return db_pamphlet


@router.get("/", response_model=list[Pamphlet])
def list_pamphlets(
    grade: str | None = None,
    subject: str | None = None,
    chapter: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: UserModel | None = Depends(get_optional_user),
):
    """List visible pamphlets with optional filters and text search."""
    query = db.query(PamphletModel).filter(_visible_to(current_user))

    if grade:
        query = query.filter(PamphletModel.grade == grade)
    if subject:
        query = query.filter(PamphletModel.subject == subject)
    if chapter:
        query = query.filter(PamphletModel.chapter == chapter)

    if search:
        pattern = f"%{_escape_like(search)}%"
        query = query.filter(
            or_(
                PamphletModel.title.ilike(pattern, escape="\\"),
                PamphletModel.subject.ilike(pattern, escape="\\"),
                PamphletModel.chapter.ilike(pattern, escape="\\"),
                PamphletModel.method.ilike(pattern, escape="\\"),
                cast(PamphletModel.tags, String).ilike(pattern, escape="\\"),
            )
        )

    return query.order_by(PamphletModel.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{pamphlet_id}", response_model=Pamphlet)
def get_pamphlet(
    pamphlet_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel | None = Depends(get_optional_user),
):
    """Get a pamphlet by ID."""
    db_pamphlet = (
        db.query(PamphletModel)
        .filter(PamphletModel.id == pamphlet_id)
        .filter(_visible_to(current_user))
        .first()
    )
    if not db_pamphlet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pamphlet not found")
    return db_pamphlet


@router.post("/{pamphlet_id}/versions", response_model=PamphletVersion)
def create_pamphlet_version(
    pamphlet_id: int,
    file: UploadFile = File(...),
    version_number: int | None = Form(None),
    notes: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Upload a new version of a pamphlet."""
    db_pamphlet = db.query(PamphletModel).filter(PamphletModel.id == pamphlet_id).first()
    if not db_pamphlet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pamphlet not found")
    if db_pamphlet.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB",
        )

    extension = os.path.splitext(file.filename or "")[1].lstrip(".").lower()
    object_path = f"pamphlets/{pamphlet_id}/{uuid.uuid4()}.{extension or 'bin'}"

    try:
        minio_client.put_object(
            settings.MINIO_BUCKET_PAMPHLETS,
            object_path,
            BytesIO(data),
            length=len(data),
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as exc:  # noqa: BLE001 - surfaced as a 503 to the client
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"File upload failed: {exc}",
        ) from None

    if version_number is None:
        latest = (
            db.query(PamphletVersionModel)
            .filter(PamphletVersionModel.pamphlet_id == pamphlet_id)
            .order_by(PamphletVersionModel.version_number.desc())
            .first()
        )
        version_number = 1 if latest is None else latest.version_number + 1

    db_version = PamphletVersionModel(
        pamphlet_id=pamphlet_id,
        version_number=version_number,
        file_path=object_path,
        file_type=extension or "bin",
        file_size=len(data),
        notes=notes,
        author_id=current_user.id,
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version
