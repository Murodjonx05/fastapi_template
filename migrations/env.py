from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

import importlib
import pkgutil
import src.models
from src.core.settings import app_settings
from src.database import Base, ensure_database_directory
from src.utils.logging import configure_logging, get_logger

# Best Practice: Dynamically discover and load all modules in src.models
# to ensure Base.metadata is fully populated for autogenerate.
def discover_models():
    for _, name, _ in pkgutil.iter_modules(src.models.__path__, "src.models."):
        importlib.import_module(name)

discover_models()

config = context.config
configure_logging()
alembic_logger = get_logger("alembic")

config.set_main_option("sqlalchemy.url", app_settings.sync_database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    alembic_logger.info("Running migrations in offline mode", extra={"module": "alembic"})
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    ensure_database_directory()
    alembic_logger.info("Running migrations in online mode", extra={"module": "alembic"})
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
