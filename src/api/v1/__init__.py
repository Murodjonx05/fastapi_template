from fastapi import APIRouter
from src.api.v1.user import user_router
from src.api.v1.i18n import i18n_router
from src.api.v1.rbac import rbac_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(user_router)
v1_router.include_router(i18n_router)
v1_router.include_router(rbac_router)