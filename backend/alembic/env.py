"""Alembic environment configuration for CoCo Platform (SQLite)."""
import os
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config object
config = context.config

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No SQLAlchemy MetaData object — we use raw SQL migrations
target_metadata = None

# Resolve the platform.db path
PLATFORM_DB_PATH = Path(os.environ.get(
    "COCO_PLATFORM_DB",
    str(Path.home() / ".coco" / "platform.db"),
))

# Override the sqlalchemy.url with the resolved path
config.set_main_option("sqlalchemy.url", f"sqlite:///{PLATFORM_DB_PATH}")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generate SQL script."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connect to the database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Enable foreign keys for SQLite
        connection.exec_driver_sql("PRAGMA foreign_keys = ON")

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite ALTER TABLE support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
