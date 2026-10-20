"""
Configuration settings for OpenEdu Git backend.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "OpenEdu Git API"

    # Database
    # NOTE: values are not shell-expanded. docker-compose builds the real URL
    # from POSTGRES_* variables; locally you can point this at any Postgres.
    DATABASE_URL: str = "postgresql://openedu:openedu_password@db:5432/openedu_db"

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_PAMPHLETS: str = "pamphlets"
    MINIO_BUCKET_AVATARS: str = "avatars"
    MINIO_AUTO_CREATE_BUCKETS: bool = True

    # Auth
    # SECRET_KEY must be provided in production. When empty, a random key is
    # generated at start-up (development only: tokens die on restart).
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    PASSWORD_HASH_ROUNDS: int = 12
    REQUIRE_EMAIL_VERIFICATION: bool = False

    # Uploads
    MAX_UPLOAD_MB: int = 25

    # CORS
    CORS_ORIGINS: list[str] = [
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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
