"""
Database session management for OpenEdu Git.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_engine_options: dict = {"pool_pre_ping": True}
if not settings.DATABASE_URL.startswith("sqlite"):
    # QueuePool tuning only applies to server databases.
    _engine_options.update(pool_size=10, max_overflow=20)

engine = create_engine(settings.DATABASE_URL, **_engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency that yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
