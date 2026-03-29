import asyncio
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from src.core.settings import BASE_DIR, app_settings
from src.database import ensure_database_directory
from src.utils.logging import get_logger

_log = get_logger("lifespan")
_EXTRA = {"module": "lifespan"}


def _sanitize_url(url: str) -> str:
    if "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    _, location = rest.rsplit("@", 1)
    return f"{scheme}://***@{location}"


def run_migrations() -> None:
    ensure_database_directory()
    _log.info("Starting migrations", extra={**_EXTRA, "database_url": _sanitize_url(app_settings.sync_database_url)})
    try:
        cfg = Config(str(BASE_DIR / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", app_settings.sync_database_url)
        command.upgrade(cfg, "head")
        _log.info("Migrations completed", extra=_EXTRA)
    except Exception:
        _log.error("Migrations failed", extra=_EXTRA, exc_info=True)
        raise


@asynccontextmanager
async def lifespan(_: FastAPI):
    _log.info("Startup", extra=_EXTRA)
    if app_settings.run_migrations_on_startup:
        await asyncio.to_thread(run_migrations)
    else:
        _log.warning("Migrations on startup disabled", extra=_EXTRA)
    yield
    _log.info("Shutdown", extra=_EXTRA)