import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from src.core.settings import BASE_DIR, app_settings
from src.utils.logging import get_logger

logger = get_logger("lifespan")

def ensure_sqlite_dir() -> None:
    """Ensure parent directory exists for SQLite database."""
    if app_settings.database_url.startswith("sqlite"):
        db_path = app_settings.database_url.removeprefix("sqlite+aiosqlite:///")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

def apply_migrations() -> None:
    """Run Alembic migrations to upgrade the schema to head."""
    ensure_sqlite_dir()
    logger.info("Initializing database migrations...")
    try:
        cfg = Config(str(BASE_DIR / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", app_settings.sync_database_url)
        command.upgrade(cfg, "head")
        logger.info("Database schema is up-to-date.")
    except Exception as exc:
        logger.error(f"Migration error: {exc}", exc_info=True)
        raise

@asynccontextmanager
async def lifespan(_: FastAPI):
    """FastAPI lifespan manager for startup and shutdown events."""
    logger.info("Application starting up...")
    
    if app_settings.run_migrations_on_startup:
        await asyncio.to_thread(apply_migrations)
    
    yield
    
    logger.info("Application shutting down...")