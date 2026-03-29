from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

from src.core.settings import app_settings
from src.api import api
from src.api.root import root_router
from src.lifespan import lifespan
from src.utils.rate_limiter import _rate_limit_exceeded_handler, limiter

app = FastAPI(title=app_settings.title, version=app_settings.version, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(root_router)
app.include_router(api)
