from fastapi import APIRouter
from src.api.v1.i18n import i18n_closed_router
from src.api.v1.rbac import rbac_closed_router
from src.api.v1.user import user_closed_router, user_opened_router

v1_opened_router = APIRouter(prefix="/v1")
v1_closed_router = APIRouter(prefix="/v1")

v1_opened_router.include_router(user_opened_router)

v1_closed_router.include_router(user_closed_router)
v1_closed_router.include_router(i18n_closed_router)
v1_closed_router.include_router(rbac_closed_router)
