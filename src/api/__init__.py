from fastapi import APIRouter, Depends

from src.api.v1 import v1_closed_router, v1_opened_router
from src.core.security import get_current_user_with_token

api = APIRouter(prefix="/api")
opened_router = APIRouter()
closed_router = APIRouter(dependencies=[Depends(get_current_user_with_token)])

opened_router.include_router(v1_opened_router)
closed_router.include_router(v1_closed_router)

api.include_router(opened_router)
api.include_router(closed_router)