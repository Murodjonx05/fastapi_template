from fastapi import APIRouter, Request

from src.core.limiter import limit_minute
from src.settings import Application as app
from src.utils.profiling import profile
from src.utils.rate_limiter import limiter

root_router = APIRouter()


@root_router.get("/", tags=["root"])
@limiter.limit(limit_minute(1))
@profile()
async def root_api(request: Request):
    return {
        "version": app.version,
        "title": app.title,
        "description": app.description,
        **({"debug": app.debug_mode} if app.debug_mode else {})
    }
