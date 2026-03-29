from fastapi import APIRouter, Request
from src.core.settings import app_settings
from src.api.v1 import v1_router

api_router = APIRouter()

@api_router.get("/", tags=["root"])
async def root(request: Request):
    """General project info."""
    return {
        "title": app_settings.title,
        "version": app_settings.version,
        "docs": "/docs" if app_settings.is_docs_enabled else None
    }

api_router.include_router(v1_router, prefix="/v1")