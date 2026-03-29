"""Shared pytest fixtures: in-memory SQLite database + async session + HTTPX test client."""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import src.database

# Pre-load ORM models and core components to avoid "Setup delay" during first test
from src.database import Base, get_db_session
from src.app import create_app
import src.models.user  # noqa: F401
import src.models.i18n  # noqa: F401
import src.models.rbac  # noqa: F401
import src.core.security
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# --- Performance Optimizations ---

# 1. Fast Hashing for Tests
src.core.security.PASSWORD_HASHER = PasswordHash((
    Argon2Hasher(time_cost=1, memory_cost=512, parallelism=1),
))

# 2. Silent Logs for maximum throughput
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# 3. Optimized SQLite Engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL, 
    echo=False,
    connect_args={"check_same_thread": False},
)

@event.listens_for(test_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA journal_mode = MEMORY")
    cursor.close()

TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)

# Monkey-patch global database layer for tests
src.database.AsyncSessionMaker = TestSessionLocal
src.database.engine = test_engine

# --- Fixtures ---

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Session-scoped database initialization."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Function-scoped transactional session."""
    async with TestSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()

@pytest.fixture(scope="session")
def app():
    """Cached FastAPI app instance."""
    return create_app()

@pytest_asyncio.fixture
async def client(app, db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Optimized and isolation-safe test client."""
    from src.utils.rate_limiter import limiter
    
    # Disable rate limiting entirely so `20/second` strict default limits don't 
    # crush test suite latency and rapid-fire checks.
    limiter.enabled = False
    
    # 1. Thread-safe session override for current task
    token = src.core.security.TEST_SESSION_OVERRIDE.set(db_session)
    app.dependency_overrides[get_db_session] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # 2. Cleanup
    app.dependency_overrides.clear()
    src.core.security.TEST_SESSION_OVERRIDE.reset(token)
