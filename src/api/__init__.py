from fastapi import APIRouter

def load_routers(router: APIRouter, routers: list[APIRouter]) -> None:
    for r in filter(None, routers):
        router.include_router(r)


api = APIRouter(prefix="/api")


from src.api.v1 import v1_router

load_routers(api, [
    v1_router,
])