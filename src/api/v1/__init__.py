from fastapi import APIRouter
from src.api import load_routers
from src.api.v1.user import user_router

v1_router = APIRouter(prefix="/v1")

load_routers(v1_router, [
    user_router,
])