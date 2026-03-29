from fastapi import APIRouter, HTTPException, Request, status
from typing import Annotated

from src.core.security import CurrentUser, create_access_token
from src.crud.user import (
    UserError,
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidCredentialsError,
    authenticate_user,
    create_user,
    delete_user,
    get_user_by_id,
)
from src.database import SessionDep
from src.schemas.user import UserAuthSchema, UserCreateSchema, UserResponseSchema, UserTokenSchema
from src.utils.logging import get_logger

logger = get_logger("users_api")
user_router = APIRouter()

@user_router.post("/auth", response_model=UserTokenSchema)
async def auth_user(request: Request, body: UserAuthSchema, session: SessionDep):
    """Authenticate and obtain a JWT access token."""
    try:
        user_uuid = await authenticate_user(body, session)
        logger.info(f"User authenticated: {body.username}")
        return UserTokenSchema(access_token=create_access_token(user_uuid))
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

@user_router.post("/", status_code=status.HTTP_201_CREATED)
async def signup(request: Request, body: UserCreateSchema, session: SessionDep):
    """Register a new user."""
    try:
        user_uuid = await create_user(body, session)
        logger.info(f"User created: {body.username}")
        return {"user_uuid": user_uuid}
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

@user_router.get("/me", response_model=UserResponseSchema)
async def get_me(current_user: CurrentUser, session: SessionDep):
    """Fetch profile info of the current user."""
    return await get_user_by_id(current_user.id, session)

@user_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(current_user: CurrentUser, session: SessionDep):
    """Permanently delete the current user."""
    try:
        await delete_user(current_user.id, session)
        logger.info(f"User self-deleted: {current_user.id}")
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
