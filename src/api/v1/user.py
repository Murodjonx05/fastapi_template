from fastapi import APIRouter, HTTPException, Request

from src.core.limiter import limit_minute
from src.core.security import CurrentUserDep, create_access_token
from src.crud.user import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
    authenticate_user,
    create_user,
    delete_user,
    get_user,
)
from src.database import SessionDep
from src.schemas.user import UserAuthSchemaDep, UserCreateSchemaDep, UserResponseSchema, UserTokenSchema
from src.utils.logging import get_logger
from src.utils.rate_limiter import limiter

user_logger = get_logger("users_api_endpoint")
user_opened_router = APIRouter(prefix="/user", tags=["user"])
user_closed_router = APIRouter(prefix="/user", tags=["user"])


@user_opened_router.post("/auth", response_model=UserTokenSchema)
@limiter.limit(limit_minute(5))
async def auth_user(request: Request, user: UserAuthSchemaDep, session: SessionDep):
    try:
        user_uuid = await authenticate_user(user, session)
        user_logger.info(f"User authenticated: {user.username}")
        return UserTokenSchema(access_token=create_access_token(user_uuid))
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        user_logger.exception(f"Unexpected error authenticating user: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@user_opened_router.post("/", status_code=201)
@limiter.limit(limit_minute(5))
async def create_user_endpoint(request: Request, user: UserCreateSchemaDep, session: SessionDep):
    try:
        user_uuid = await create_user(user, session)
        user_logger.info(f"User created: {user.username}")
        return {"message": "User created successfully", "user_uuid": user_uuid}
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        user_logger.exception(f"Unexpected error creating user: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@user_closed_router.delete("", status_code=204)
@limiter.limit(limit_minute(5))
async def delete_user_endpoint(request: Request, current_user: CurrentUserDep, session: SessionDep):
    try:
        await delete_user(current_user.id, session)
        user_logger.info(f"User deleted: {current_user.id}")
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        user_logger.exception(f"Unexpected error deleting user: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@user_closed_router.get("", response_model=UserResponseSchema)
@limiter.limit(limit_minute(5))
async def get_user_endpoint(request: Request, current_user: CurrentUserDep, session: SessionDep):
    try:
        user = await get_user(current_user.id, session)
        user_logger.info(f"User fetched: {current_user.id}")
        return user
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        user_logger.exception(f"Unexpected error getting user: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
