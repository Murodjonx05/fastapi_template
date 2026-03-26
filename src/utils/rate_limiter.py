from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def build_rate_limit_response() -> JSONResponse:
    """
    Returns a clear, developer-friendly response for rate-limited requests.
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "type": "rate_limited",
                "message": "Rate limit exceeded. Too many requests. Please try again later.",
                "status": 429,
            }
        },
    )


async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return build_rate_limit_response()
    