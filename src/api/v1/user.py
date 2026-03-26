from fastapi import APIRouter, HTTPException, Request

from src.core.limiter import limit_day, limit_minute
from src.crud.user import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
)
from src.database import SessionDep
from src.schemas.user import UserAuthSchema, UserCreateSchema
from src.utils.logging import get_logger
from src.utils.rate_limiter import limiter

user_logger = get_logger("users_api_endpoint")
user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post("/auth")
@limiter.limit(limit_minute(5))
async def auth_user(request: Request, user: UserAuthSchema, session: SessionDep):
    try:
        user_id = await authenticate_user(user, session)
        user_logger.info(f"User authenticated: {user.username}")
        return {"message": "User authenticated successfully", "user_id": user_id}
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@user_router.post("/create", status_code=201)
@limiter.limit(limit_day(5))
async def create_user_endpoint(request: Request, user: UserCreateSchema, session: SessionDep):
    try:
        user_id = await create_user(user, session)
        return {"message": "User created successfully", "user_id": user_id}
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        user_logger.exception("Unexpected error creating user")
        raise HTTPException(status_code=500, detail="Internal server error")