from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

from src.lifespan import lifespan
from src.core.settings import Application as application
from src.utils.loader import load_routers
from src.utils.rate_limiter import _rate_limit_exceeded_handler, limiter

app = FastAPI(title=application.title, version=application.version, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
load_routers(app)