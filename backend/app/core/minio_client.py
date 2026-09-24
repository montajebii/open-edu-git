"""
MinIO client for OpenEdu Git.

The client is lazily initialized to avoid connecting to MinIO during tests
or when MinIO is not available.
"""

from functools import cached_property

from app.core.config import settings


class MinioClient:
    """MinIO client with lazy initialization."""

    @cached_property
    def client(self):
        from minio import Minio
        from minio.error import S3Error

        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        # Ensure buckets exist
        try:
            if not client.bucket_exists(settings.MINIO_BUCKET_PAMPHLETS):
                client.make_bucket(settings.MINIO_BUCKET_PAMPHLETS)
            if not client.bucket_exists(settings.MINIO_BUCKET_AVATARS):
                client.make_bucket(settings.MINIO_BUCKET_AVATARS)
        except S3Error as e:
            print(f"MinIO bucket setup failed: {e}")
        return client

    def upload_fileobj(self, file_data, bucket_name, file_path):
        """Upload a file object to MinIO."""
        return self.client.upload_fileobj(file_data, bucket_name, file_path)

    def bucket_exists(self, bucket_name):
        """Check if a bucket exists."""
        return self.client.bucket_exists(bucket_name)

    def make_bucket(self, bucket_name):
        """Create a bucket."""
        return self.client.make_bucket(bucket_name)


# Singleton instance — client lazily initialized on first access
_minio_client = MinioClient()


def get_minio_client():
    """Get the singleton MinIO client instance."""
    return _minio_client


# Export for backward compatibility — accessed as attribute
class _LazyMinio:
    def __getattr__(self, name):
        return getattr(get_minio_client(), name)


minio_client = _LazyMinio()