from typing import Final

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.core.settings import app_settings

RATE_LIMIT_STATUS_CODE: Final[int] = 429
RATE_LIMIT_MESSAGE: Final[str] = (
    "Rate limit exceeded. Too many requests. Please try again later."
)


def get_client_ip(request: Request) -> str:
    if app_settings.trust_proxy_headers:
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()

    client_host = request.client.host if request.client else None
    if client_host:
        return client_host

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=get_client_ip)


def build_rate_limit_response() -> JSONResponse:
    return JSONResponse(
        status_code=RATE_LIMIT_STATUS_CODE,
        content={
            "error": {
                "type": "rate_limited",
                "message": RATE_LIMIT_MESSAGE,
                "status": RATE_LIMIT_STATUS_CODE,
            }
        }
    )


async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return build_rate_limit_response()