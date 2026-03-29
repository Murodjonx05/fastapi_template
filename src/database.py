from __future__ import annotations

import datetime
from pathlib import Path
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy import DateTime, MetaData, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.core.settings import app_settings

# --- Engine & Session ---
engine = create_async_engine(app_settings.database_url, echo=False)
AsyncSessionMaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


def ensure_database_directory() -> None:
    """Ensure the parent directory exists for SQLite database files."""
    if app_settings.database_url.startswith("sqlite"):
        db_path = app_settings.database_url.removeprefix("sqlite+aiosqlite:///")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing an async database session."""
    async with AsyncSessionMaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]

# --- Common Column Types ---
int_pk = Annotated[int, mapped_column(primary_key=True)]
str_255 = Annotated[str, mapped_column(String(255))]
now_utc = func.now()

def _now_py() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

timestamp = Annotated[
    datetime.datetime,
    mapped_column(DateTime(timezone=True), server_default=now_utc, default=_now_py)
]
updated_timestamp = Annotated[
    datetime.datetime,
    mapped_column(DateTime(timezone=True), server_default=now_utc, default=_now_py, onupdate=_now_py)
]


naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s"
}

class Base(DeclarativeBase):
    """Base for all ORM models."""
    metadata = MetaData(naming_convention=naming_convention)

class BasePK(Base):
    """Base for models with an integer primary key."""
    __abstract__ = True
    id: Mapped[int_pk]
