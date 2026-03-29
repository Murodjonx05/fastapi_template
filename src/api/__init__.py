from fastapi import APIRouter, Request
from src.core.settings import app_settings
from src.api.v1 import v1_router
from src.utils.rate_limiter import limiter, limit_minute

api_router = APIRouter(prefix="/api")

@api_router.get("/", tags=["root"])
@limiter.limit(limit_minute(5))
async def root(request: Request):
    """General project info and documentation link."""
    return {
        "title": app_settings.title,
        "version": app_settings.version,
        "docs": "/docs" if app_settings.is_docs_enabled else None
    }

api_router.include_router(v1_router, prefix="/v1")