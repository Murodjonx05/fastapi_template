from typing import Final

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.core.settings import app_settings

ERROR_CODE: Final[int] = 429
ERROR_MSG: Final[str] = "Rate limit exceeded. Please try again later."


def resolve_key(request: Request) -> str:
    """Identify client for rate limiting purposes, respecting reverse proxy headers."""
    if app_settings.trust_proxy_headers:
        if real_ip := request.headers.get("x-real-ip"):
            return real_ip.strip()
        if forwarded_for := request.headers.get("x-forwarded-for"):
            return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else get_remote_address(request)


def limit_minute(x: int) -> str:
    return f"{x}/minute"


def limit_hour(x: int) -> str:
    return f"{x}/hour"


def limit_day(x: int) -> str:
    return f"{x}/day"


limiter = Limiter(key_func=resolve_key, default_limits=["20/second"])


async def _rate_limit_exceeded_handler(request: Request, _: RateLimitExceeded) -> Response:
    """Generic handler for rate limit violations."""
    return JSONResponse(
        status_code=ERROR_CODE,
        content={
            "detail": ERROR_MSG,
            "status": ERROR_CODE,
            "type": "rate_limit_error",
        },
    )
