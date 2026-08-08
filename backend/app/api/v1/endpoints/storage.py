"""
Storage endpoints for OpenEdu Git API v1.
"""

from io import BytesIO
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ...core.auth import get_current_user
from ...db.session import get_db
from ...services.storage import StorageService

router = APIRouter(prefix="/storage", tags=["storage"])


@router.post("/upload/{bucket_name}")
def upload_file(
    bucket_name: str,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[UUID, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Upload a file to MinIO storage."""
    storage = StorageService()

    # Validate bucket
    if bucket_name not in ["pamphlets", "pamphlets-latex", "pamphlets-pdf", "avatars"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bucket name",
        )

    # Create bucket if not exists
    storage.create_bucket_if_not_exists(bucket_name)

    # Upload file
    file_data = await file.read()
    object_name = storage.upload_file(
        bucket_name=bucket_name,
        file_data=BytesIO(file_data),
        file_name=file.filename,
        content_type=file.content_type,
    )

    return {
        "object_name": object_name,
        "bucket_name": bucket_name,
        "file_name": file.filename,
    }


@router.get("/download/{bucket_name}/{object_name}")
def download_file(
    bucket_name: str,
    object_name: str,
):
    """Download a file from MinIO storage."""
    storage = StorageService()
    file_data = storage.download_file(bucket_name, object_name)

    if not file_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return {
        "file_data": file_data,
        "file_name": object_name,
    }


@router.get("/presigned/{bucket_name}/{object_name}")
def get_presigned_url(
    bucket_name: str,
    object_name: str,
    expires: int = 3600,
):
    """Generate a presigned URL for temporary access."""
    storage = StorageService()
    url = storage.generate_presigned_url(bucket_name, object_name, expires)
    return {"url": url}
