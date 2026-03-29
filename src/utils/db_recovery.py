from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from sqlalchemy.exc import OperationalError

from src.lifespan import apply_migrations
from src.utils.logging import get_logger

_T = TypeVar("_T")
_migrate_lock = asyncio.Lock()
recovery_logger = get_logger("db_recovery")


def _is_missing_table_error(exc: OperationalError) -> bool:
    msg = str(exc).lower()
    return "no such table" in msg or "does not exist" in msg


async def _run_migrations_once() -> None:
    async with _migrate_lock:
        recovery_logger.warning(
            "Missing DB object detected, running migrations and retrying once",
            extra={"module": "db_recovery"},
        )
        await asyncio.to_thread(apply_migrations)


def retry_after_migration_on_missing_table(
    func: Callable[..., Awaitable[_T]],
) -> Callable[..., Awaitable[_T]]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> _T:
        try:
            return await func(*args, **kwargs)
        except OperationalError as exc:
            if _is_missing_table_error(exc):
                await _run_migrations_once()
                return await func(*args, **kwargs)
            raise

    return wrapper
