from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

from src.api import api_router
from src.core.settings import app_settings
from src.core.security import auth
from src.core.exceptions import setup_exception_handlers
from src.lifespan import lifespan
from src.utils.rate_limiter import _rate_limit_exceeded_handler, limiter

def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=app_settings.title,
        version=app_settings.version,
        lifespan=lifespan,
        docs_url="/docs" if app_settings.is_docs_enabled else None,
        redoc_url="/redoc" if app_settings.is_docs_enabled else None,
        openapi_url="/openapi.json" if app_settings.is_docs_enabled else None,
    )
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    setup_exception_handlers(app)  # Register global exception handlers
    
    app.include_router(api_router)
    auth.handle_errors(app)
    
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        from fastapi.responses import RedirectResponse
        if app_settings.is_docs_enabled:
            return RedirectResponse(url="/docs")
        return {"status": "ok"}
    
    return app

app = create_app()
