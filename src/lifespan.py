from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy import create_engine, inspect, text

from src.core.settings import BASE_DIR, app_settings
from src.database import Base, ensure_database_directory
from src.utils.logging import get_logger

app_logger = get_logger()
ALEMBIC_VERSION_TABLE = "alembic_version"
CHECK_VERSION_SQL = text("SELECT 1 FROM alembic_version LIMIT 1")


def get_alembic_config() -> Config:
    return Config(str(BASE_DIR / "alembic.ini"))


def get_existing_tables() -> set[str]:
    engine = create_engine(app_settings.sync_database_url)

    try:
        with engine.connect() as connection:
            return set(inspect(connection).get_table_names())
    finally:
        engine.dispose()


def has_alembic_revision() -> bool:
    engine = create_engine(app_settings.sync_database_url)

    try:
        with engine.connect() as connection:
            return connection.execute(CHECK_VERSION_SQL).scalar() is not None
    finally:
        engine.dispose()


def should_stamp_existing_schema() -> bool:
    existing_tables = get_existing_tables()
    model_tables = set(Base.metadata.tables)

    if not model_tables.issubset(existing_tables):
        return False

    if ALEMBIC_VERSION_TABLE not in existing_tables:
        return True

    return not has_alembic_revision()


def run_migrations() -> None:
    ensure_database_directory()
    alembic_config = get_alembic_config()

    if should_stamp_existing_schema():
        command.stamp(alembic_config, "head")

    command.upgrade(alembic_config, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Application startup", extra={"module": "lifespan"})
    run_migrations()
    yield
    app_logger.info("Application shutdown", extra={"module": "lifespan"})
