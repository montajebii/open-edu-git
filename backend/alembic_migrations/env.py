"""
Alembic environment for OpenEdu Git migrations.

Configures Alembic to use our SQLAlchemy models for autogenerating migrations.

The database URL is resolved in order: DATABASE_URL env var > app settings >
alembic.ini. This mirrors the backend container, where compose injects
DATABASE_URL, so `alembic upgrade head` always targets the same database as
the application.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings

# Import all models to ensure they're registered with SQLAlchemy's metadata
from app.db import models as db_models  # noqa: F401
from app.db.base import Base

# The target metadata contains all our models
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Resolve the database URL from the environment, falling back to app settings
# and finally the value in alembic.ini.
db_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
