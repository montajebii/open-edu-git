"""
MinIO client for OpenEdu Git.

The client is created lazily and bucket creation is best-effort: the API must be
able to start (and serve non-storage routes) even when MinIO is unavailable.
"""

import logging

from minio import Minio

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Minio | None = None


def get_minio_client() -> Minio:
    """Return a shared MinIO client, creating it on first use."""
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _client


def ensure_buckets() -> None:
    """Create the required buckets if they are missing (best effort)."""
    if not settings.MINIO_AUTO_CREATE_BUCKETS:
        logger.info("MinIO bucket auto-creation disabled (MINIO_AUTO_CREATE_BUCKETS=false)")
        return
    try:
        client = get_minio_client()
        for bucket in (settings.MINIO_BUCKET_PAMPHLETS, settings.MINIO_BUCKET_AVATARS):
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info("Created MinIO bucket %s", bucket)
    except Exception as exc:  # noqa: BLE001 - startup must not fail on storage
        logger.warning("MinIO bucket setup skipped: %s", exc)


class _MinioProxy:
    """Keeps ``minio_client.upload_fileobj(...)`` working without an import-time connection."""

    def __getattr__(self, item):
        return getattr(get_minio_client(), item)


minio_client = _MinioProxy()
