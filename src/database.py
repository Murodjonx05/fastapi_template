import datetime
from pathlib import Path
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy import DateTime, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column

from src.core.settings import app_settings as app

async_engine = create_async_engine(
    url=app.database_url,
    echo=False,
)

async_session = async_sessionmaker[AsyncSession](
    bind=async_engine,
    expire_on_commit=False,
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        async with session.begin():
            yield session


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def ensure_database_directory() -> None:
    if app.database_url.startswith("sqlite"):
        db_path = app.database_url.removeprefix("sqlite+aiosqlite:///")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

intpk = Annotated[int, mapped_column(primary_key=True)]
str255 = Annotated[str, mapped_column(String(255))]
str255_nullable = Annotated[str, mapped_column(String(255), nullable=True)]
str255_unique = Annotated[str, mapped_column(String(255), unique=True)]



common_datetime_kwargs = dict(type_=DateTime, default=datetime.datetime.utcnow, server_default=func.now())
updated_at = Annotated[datetime.datetime, mapped_column(**common_datetime_kwargs, onupdate=datetime.datetime.utcnow)]
created_at = Annotated[datetime.datetime, mapped_column(**common_datetime_kwargs)]

class Base(DeclarativeBase):
    pass

class BasePk(Base):
    __abstract__ = True

    id: Mapped[intpk]
