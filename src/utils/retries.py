import asyncio
from functools import wraps
from time import sleep
from typing import Any, Callable, TypeVar

from src.utils.logging import get_logger

logger = get_logger("retries")

F = TypeVar("F", bound=Callable[..., Any])


def retry(max_retries: int = 3, delay: float = 1.0, step_multiply: float = 1.0) -> Callable[[F], F]:
    if max_retries < 1:
        raise ValueError("max_retries must be at least 1")
    if delay < 0:
        raise ValueError("delay must be greater than or equal to 0")
    if step_multiply <= 0:
        raise ValueError("step_multiply must be greater than 0")

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                current_delay = delay

                for attempt in range(1, max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as exc:
                        if attempt == max_retries:
                            logger.error(
                                f"{func.__name__} failed after {attempt} attempts: {exc}",
                                extra={"module": "retries"},
                            )
                            raise

                        logger.warning(
                            f"{func.__name__} failed on attempt {attempt}/{max_retries}: {exc}. "
                            f"Retrying in {current_delay:.2f}s",
                            extra={"module": "retries"},
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= step_multiply

            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {attempt} attempts: {exc}",
                            extra={"module": "retries"},
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt}/{max_retries}: {exc}. "
                        f"Retrying in {current_delay:.2f}s",
                        extra={"module": "retries"},
                    )
                    sleep(current_delay)
                    current_delay *= step_multiply

        return sync_wrapper

    return decorator
