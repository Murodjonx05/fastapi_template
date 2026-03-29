from __future__ import annotations
import datetime
from pathlib import Path
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy import DateTime, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.core.settings import app_settings as app

# ---------------------------------------------------------------------------
# Engine & session
# ---------------------------------------------------------------------------

async_engine = create_async_engine(url=app.database_url, echo=False)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
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

intpk           = Annotated[int, mapped_column(primary_key=True)]
str255          = Annotated[str, mapped_column(String(255))]
str255_nullable = Annotated[str | None, mapped_column(String(255), nullable=True)]
str255_unique   = Annotated[str, mapped_column(String(255), unique=True)]

def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

_dt = {"type_": DateTime(timezone=True), "server_default": func.now()}

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
