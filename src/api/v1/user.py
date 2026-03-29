from fastapi import APIRouter, status
from src.core.security import CurrentUser, create_access_token
from src.crud.user import UserNotFoundError, user_crud
from src.database import SessionDep
from src.schemas.user import UserAuthSchema, UserCreateSchema, UserResponseSchema, UserTokenSchema
from src.utils.logging import get_logger

logger = get_logger("users_api")
user_router = APIRouter()

@user_router.post("/auth", response_model=UserTokenSchema)
async def auth_user(body: UserAuthSchema, session: SessionDep):
    """Authenticate and obtain a JWT access token."""
    user_uuid = await user_crud.authenticate(body, session)
    logger.info(f"User authenticated: {body.username}")
    return UserTokenSchema(access_token=create_access_token(user_uuid))

@user_router.post("/", status_code=status.HTTP_201_CREATED)
async def signup(body: UserCreateSchema, session: SessionDep):
    """Register a new user."""
    user_uuid = await user_crud.create(session, body)
    logger.info(f"User created: {body.username}")
    return {"user_uuid": user_uuid}

@user_router.get("/me", response_model=UserResponseSchema)
async def get_me(current_user: CurrentUser):
    """Fetch profile info of the current user."""
    return current_user

@user_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(current_user: CurrentUser, session: SessionDep):
    """Permanently delete the current user."""
    if not await user_crud.delete(session, current_user.id):
        raise UserNotFoundError(f"ID {current_user.id}")
    logger.info(f"User self-deleted: {current_user.id}")
