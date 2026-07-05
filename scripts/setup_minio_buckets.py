#!/usr/bin/env python3
"""
Script to create MinIO buckets for OpenEdu Git.
Run this after starting MinIO via Docker Compose.
"""

import os
from minio import Minio
from minio.error import S3Error

# Load environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Buckets to create
BUCKETS = [
    "pamphlets",      # For storing pamphlet files
    "avatars",        # For user profile pictures
    "video-courses",  # For future video courses (Phase 2)
]


def main():
    # Initialize MinIO client
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )

    # Create buckets
    for bucket in BUCKETS:
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                print(f"✅ Bucket '{bucket}' created successfully.")
            else:
                print(f"ℹ️ Bucket '{bucket}' already exists.")
        except S3Error as e:
            print(f"❌ Error creating bucket '{bucket}': {e}")


if __name__ == "__main__":
    main()