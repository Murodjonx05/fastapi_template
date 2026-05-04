from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api import api_router
from src.core.settings import app_settings
from src.core.security import auth
from src.core.exceptions import setup_exception_handlers
from src.lifespan import lifespan
from src.utils.rate_limiter import _rate_limit_exceeded_handler, limiter


def create_app() -> FastAPI:
    """FastAPI application factory."""
    _app = FastAPI(
        title=app_settings.title,
        version=app_settings.version,
        lifespan=lifespan,
        docs_url="/docs" if app_settings.is_docs_enabled else None,
        redoc_url="/redoc" if app_settings.is_docs_enabled else None,
        openapi_url="/openapi.json" if app_settings.is_docs_enabled else None,
        openapi_tags=[
            {"name": "auth", "description": "Authentication operations"},
            {"name": "users", "description": "User management operations"},
            {
                "name": "i18n",
                "description": "Internationalization operations (requires authentication)",
            },
        ],
    )

    _app.state.limiter = limiter
    _app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    _app.add_middleware(SlowAPIMiddleware)

    setup_exception_handlers(_app)

    # Include routers
    _app.include_router(api_router)
    auth.handle_errors(_app)

    # Add global authentication dependency
    # This adds a global security scheme that shows lock icons in docs
    _app.openapi_security_schemes = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Authentication token",
        }
    }

    @_app.get("/", include_in_schema=False)
    async def root_redirect():
        if app_settings.is_docs_enabled:
            return RedirectResponse(url="/docs")
        return {"status": "ok"}

    return _app


app = create_app()
