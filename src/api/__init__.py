from fastapi import APIRouter
from src.api.v1 import v1_router

api = APIRouter(prefix="/api")
api.include_router(v1_router)