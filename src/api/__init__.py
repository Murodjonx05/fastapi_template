from fastapi import APIRouter
from src.api.v1 import v1_router

def load_routers(router: APIRouter, routers: list[APIRouter]) -> None:
    for r in filter(None, routers):
        router.include_router(r)


api = APIRouter(prefix="/api")


load_routers(api, [
    v1_router,
])