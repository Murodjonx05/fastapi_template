from __future__ import annotations

import datetime
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy import DateTime, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.core.settings import app_settings

# --- Engine & Session ---
engine = create_async_engine(app_settings.database_url, echo=False)
AsyncSessionMaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing an async database session."""
    async with AsyncSessionMaker() as session:
        yield session

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

# --- ORM Base ---
class Base(DeclarativeBase):
    """Base for all ORM models."""
    pass

class BasePK(Base):
    """Base for models with an integer primary key."""
    __abstract__ = True
    id: Mapped[int_pk]
    