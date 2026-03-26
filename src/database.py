import datetime
from pathlib import Path
from typing import Annotated

from sqlalchemy import DateTime, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from src.settings import Application as app
from src.utils.logging import get_logger
db_logger = get_logger()

async_engine = create_async_engine(
    url=app.database_url,
    echo=False,
)

async_session = async_sessionmaker[AsyncSession](
    bind=async_engine,
    expire_on_commit=False,
)

async def init_db_once():
    db_logger.info("Initializing database once", extra={"module": "database"})
    try:
        if app.database_url.startswith("sqlite"):
            db_path = app.database_url.removeprefix("sqlite+aiosqlite:///")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            db_logger.info("Database initialized", extra={"module": "database"})
    except Exception as e:
        db_logger.error("Error initializing database", extra={"module": "database", "error": str(e)})
        raise

intpk = Annotated[int, mapped_column(primary_key=True)]
str255 = Annotated[str, mapped_column(String(255))]
str255_nullable = Annotated[str, mapped_column(String(255), nullable=True)]
str255_unique = Annotated[str, mapped_column(String(255), unique=True)]
datetime_now = Annotated[
    datetime.datetime,
    mapped_column(
        DateTime,
        default=datetime.datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.datetime.utcnow,
    )
]

class Base(DeclarativeBase):
    pass

class BasePk(Base):
    __abstract__ = True

    id: Mapped[intpk]
