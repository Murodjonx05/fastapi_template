import asyncio
from functools import wraps
from time import perf_counter

from src.settings import Application as app
from src.utils.logging import get_logger

app_logger = get_logger("PROFILING")
def profile(debug:bool=app.debug_mode or False):
    def decorator(func):
        if not debug:
            return func
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = perf_counter()
                result = await func(*args, **kwargs)
                end_time = perf_counter()
                app_logger.info(f"Function {func.__name__} took {(end_time - start_time) * 1000 :.3f} ms to execute")
                return result
            return wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = perf_counter()
                result = func(*args, **kwargs)
                end_time = perf_counter()
                app_logger.info(f"Function {func.__name__} took {(end_time - start_time) * 1000:.3f} ms to execute")
                return result
            return wrapper
    return decorator