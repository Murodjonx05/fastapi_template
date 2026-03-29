from __future__ import annotations

import asyncio
import datetime
from pathlib import Path
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy import DateTime, String, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.core.settings import app_settings as app
from src.utils.logging import get_logger

_log = get_logger("database")

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

async_engine = create_async_engine(url=app.database_url, echo=False)


def _is_missing_table(exc: OperationalError) -> bool:
    msg = str(exc).lower()
    return "no such table" in msg or "does not exist" in msg


# ---------------------------------------------------------------------------
# Self-healing session
# ---------------------------------------------------------------------------

class RecoveringAsyncSession(AsyncSession):
    """Runs Alembic migrations exactly once when a missing-table error is
    detected, then retries the failing operation.  Any subsequent failure
    propagates normally so we never enter an infinite retry loop."""

    async def _maybe_migrate(self) -> None:
        from src.lifespan import run_migrations  # late import – avoids circular deps

        _log.warning("Missing DB object – running migrations and retrying once")
        await self.rollback()
        await asyncio.to_thread(run_migrations)

    async def _with_recovery(self, coro_fn):
        try:
            return await coro_fn()
        except OperationalError as exc:
            if not _is_missing_table(exc):
                raise
            await self._maybe_migrate()
            return await coro_fn()  # raises normally on second failure

    # Only the three call-sites that touch the DB before a flush need wrapping.
    async def execute(self, *a, **kw):
        return await self._with_recovery(lambda: AsyncSession.execute(self, *a, **kw))

    async def scalar(self, *a, **kw):
        return await self._with_recovery(lambda: AsyncSession.scalar(self, *a, **kw))

    async def flush(self, *a, **kw):
        return await self._with_recovery(lambda: AsyncSession.flush(self, *a, **kw))


async_session: async_sessionmaker[RecoveringAsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=RecoveringAsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session, session.begin():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_database_directory() -> None:
    """Create parent dirs for SQLite databases; no-op for other backends."""
    if app.database_url.startswith("sqlite"):
        db_path = app.database_url.removeprefix("sqlite+aiosqlite:///")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Column type aliases
# ---------------------------------------------------------------------------

intpk          = Annotated[int, mapped_column(primary_key=True)]
str255         = Annotated[str, mapped_column(String(255))]
str255_nullable= Annotated[str | None, mapped_column(String(255), nullable=True)]
str255_unique  = Annotated[str, mapped_column(String(255), unique=True)]

def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


_dt  = dict(type_=DateTime(timezone=True), server_default=func.now())

created_at = Annotated[datetime.datetime, mapped_column(**_dt, default=_now)]
updated_at = Annotated[datetime.datetime, mapped_column(**_dt, default=_now, onupdate=_now)]

# ---------------------------------------------------------------------------
# ORM bases
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class BasePk(Base):
    __abstract__ = True
    id: Mapped[intpk]
