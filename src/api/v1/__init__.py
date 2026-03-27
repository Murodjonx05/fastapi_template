from fastapi import APIRouter
from src.api.v1.user import user_router

v1_router = APIRouter(prefix="/v1")

for router in filter(None, [user_router]):
    v1_router.include_router(router)
