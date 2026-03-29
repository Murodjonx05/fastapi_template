from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from src.core.settings import app_settings
from src.core.security import auth
from src.api import api
from src.api.root import root_router
from src.lifespan import lifespan
from src.utils.rate_limiter import _rate_limit_exceeded_handler, limiter

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
app.include_router(root_router)
app.include_router(api)
auth.handle_errors(app)
