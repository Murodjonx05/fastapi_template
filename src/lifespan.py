from fastapi import FastAPI

from src.database import init_db_once
from src.utils.logging import get_logger
app_logger = get_logger()

async def lifespan(app: FastAPI):
    app_logger.info("Application startup", extra={"module": "lifespan"})
    await init_db_once()
    yield
    app_logger.info("Application shutdown", extra={"module": "lifespan"})
