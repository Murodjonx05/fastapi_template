import asyncio
from functools import wraps
from time import sleep
from typing import Any, Callable, TypeVar, cast

from src.utils.logging import get_logger

logger = get_logger("retries")

F = TypeVar("F", bound=Callable[..., Any])
RETRYABLE_EXCEPTIONS = (Exception,)


def _validate_retry_args(max_retries: int, delay: float, step_multiply: float) -> None:
    if max_retries < 1:
        raise ValueError(f"max_retries must be >= 1, got {max_retries}")
    if delay < 0:
        raise ValueError(f"delay must be >= 0, got {delay}")
    if step_multiply <= 0:
        raise ValueError(f"step_multiply must be > 0, got {step_multiply}")


def _log_retry(func_name: str, attempt: int, max_retries: int, current_delay: float, exc: BaseException) -> None:
    logger.warning(
        f"{func_name} failed on attempt {attempt}/{max_retries}: {exc}. Retrying in {current_delay:.2f}s",
        extra={"module": "retries"},
    )


def _log_failure(func_name: str, attempt: int, exc: BaseException) -> None:
    logger.error(
        f"{func_name} failed after {attempt} attempts: {exc}",
        extra={"module": "retries"},
    )


def retry(max_retries: int = 3, delay: float = 1.0, step_multiply: float = 1.0) -> Callable[[F], F]:
    _validate_retry_args(max_retries, delay, step_multiply)

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                current_delay = delay
                for attempt in range(1, max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except RETRYABLE_EXCEPTIONS as exc:
                        if attempt == max_retries:
                            _log_failure(func.__name__, attempt, exc)
                            raise
                        _log_retry(func.__name__, attempt, max_retries, current_delay, exc)
                        await asyncio.sleep(current_delay)
                        current_delay *= step_multiply
                raise RuntimeError("Retry loop exited unexpectedly")

            return cast(F, async_wrapper)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RETRYABLE_EXCEPTIONS as exc:
                    if attempt == max_retries:
                        _log_failure(func.__name__, attempt, exc)
                        raise
                    _log_retry(func.__name__, attempt, max_retries, current_delay, exc)
                    sleep(current_delay)
                    current_delay *= step_multiply
            raise RuntimeError("Retry loop exited unexpectedly")

        return cast(F, sync_wrapper)

    return decorator
