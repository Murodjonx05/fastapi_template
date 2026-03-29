from fastapi import APIRouter
from src.api.v1.user import user_router
from src.api.v1.i18n import i18n_router

v1_router = APIRouter()

v1_router.include_router(user_router, prefix="/users", tags=["users"])
v1_router.include_router(i18n_router, prefix="/i18n")
