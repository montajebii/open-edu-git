"""
MinIO client for OpenEdu Git.
"""

from minio import Minio
from minio.error import S3Error
from app.core.config import settings


minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

# Ensure buckets exist
try:
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_PAMPHLETS):
        minio_client.make_bucket(settings.MINIO_BUCKET_PAMPHLETS)
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_AVATARS):
        minio_client.make_bucket(settings.MINIO_BUCKET_AVATARS)
except S3Error as e:
    print(f"MinIO bucket setup failed: {e}")