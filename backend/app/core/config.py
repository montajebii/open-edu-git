"""
Configuration settings for OpenEdu Git backend.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://${POSTGRES_USER:-openedu}:${POSTGRES_PASSWORD:-openedu}@db:5432/${POSTGRES_DB:-openedu_db}"
    
    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_PAMPHLETS: str = "pamphlets"
    MINIO_BUCKET_AVATARS: str = "avatars"
    
    # Auth
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]
    
    # Email (for verification)
    SMTP_SERVER: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "your-email@example.com"
    SMTP_PASSWORD: str = "your-email-password"
    EMAIL_FROM: str = "noreply@openedugit.ir"
    
    # Sentry
    SENTRY_DSN: str = ""
    
    class Config:
        env_file = ".env"
        extra = 'ignore'


settings = Settings()