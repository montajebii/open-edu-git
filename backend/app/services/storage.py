"""
Storage service for MinIO (S3-compatible) file storage.
"""

from io import BytesIO
from typing import Optional
from minio import Minio
from minio.error import S3Error
from uuid import uuid4

from ..core.config import settings


class StorageService:
    """Service for MinIO file storage operations."""

    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

    def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        """Create a bucket if it doesn't exist."""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            return True
        return False

    def upload_file(
        self,
        bucket_name: str,
        file_data: BytesIO,
        file_name: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to MinIO."""
        object_name = f"{uuid4()}_{file_name}"
        self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=file_data,
            length=file_data.getbuffer().nbytes,
            content_type=content_type,
        )
        return object_name

    def download_file(self, bucket_name: str, object_name: str) -> Optional[BytesIO]:
        """Download a file from MinIO."""
        try:
            data = BytesIO()
            self.client.get_object(bucket_name, object_name, data)
            data.seek(0)
            return data
        except S3Error:
            return None

    def generate_presigned_url(
        self, bucket_name: str, object_name: str, expires: int = 3600
    ) -> str:
        """Generate a presigned URL for temporary access."""
        return self.client.presigned_get_object(
            bucket_name, object_name, expires=expires
        )

    def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(bucket_name, object_name)
            return True
        except S3Error:
            return False