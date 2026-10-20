"""
Storage endpoints for OpenEdu Git API v1.
"""

from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ....core.security import get_current_user
from ....db.session import get_db
from ....models.user import User as UserModel
from ....services.storage import StorageService

router = APIRouter(prefix="/storage", tags=["storage"])

ALLOWED_BUCKETS = ("pamphlets", "pamphlets-latex", "pamphlets-pdf", "avatars")


@router.post("/upload/{bucket_name}")
async def upload_file(
    bucket_name: str,
    file: Annotated[UploadFile, File(...)],
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a file to MinIO storage."""
    if bucket_name not in ALLOWED_BUCKETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bucket name",
        )

    storage = StorageService()
    file_data = await file.read()
    if not file_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    try:
        storage.create_bucket_if_not_exists(bucket_name)
        object_name = storage.upload_file(
            bucket_name=bucket_name,
            file_data=BytesIO(file_data),
            file_name=file.filename or "upload.bin",
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as exc:  # noqa: BLE001 - surfaced as a 503 to the client
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage unavailable: {exc}",
        ) from None

    return {
        "object_name": object_name,
        "bucket_name": bucket_name,
        "file_name": file.filename,
        "file_size": len(file_data),
    }


@router.get("/presigned/{bucket_name}/{object_name}")
def get_presigned_url(
    bucket_name: str,
    object_name: str,
    expires: int = 3600,
    current_user: UserModel = Depends(get_current_user),
):
    """Generate a presigned URL for temporary access."""
    if bucket_name not in ALLOWED_BUCKETS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid bucket name")

    storage = StorageService()
    url = storage.generate_presigned_url(bucket_name, object_name, expires)
    return {"url": url}
