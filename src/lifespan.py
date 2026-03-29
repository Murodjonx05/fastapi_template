import asyncio
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from src.core.settings import BASE_DIR, app_settings
from src.database import ensure_database_directory
from src.utils.logging import get_logger

app_logger = get_logger()


def get_alembic_config() -> Config:
    return Config(str(BASE_DIR / "alembic.ini"))


def _sanitize_database_url(db_url: str) -> str:
    parsed = urlparse(db_url)
    host = parsed.hostname or "localhost"
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path or ""
    return f"{parsed.scheme}://{host}{port}{path}"


def run_migrations() -> None:
    ensure_database_directory()
    alembic_config = get_alembic_config()
    app_logger.info(
        "Running Alembic migrations",
        extra={
            "module": "lifespan",
            "database_url": _sanitize_database_url(app_settings.sync_database_url),
        },
    )
    command.upgrade(alembic_config, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Application startup", extra={"module": "lifespan"})
    await asyncio.to_thread(run_migrations)
    yield
    app_logger.info("Application shutdown", extra={"module": "lifespan"})
