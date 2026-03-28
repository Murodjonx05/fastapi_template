from fastapi import FastAPI

from src.api import api
from src.api.root import root_router


def load_routers(app: FastAPI) -> None:
    """Include all project routers into the FastAPI app."""
    app.include_router(root_router)
    app.include_router(api)