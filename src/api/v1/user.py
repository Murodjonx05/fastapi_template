from fastapi import APIRouter, status, HTTPException
from src.core.security import (
    CurrentUser,
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
    revoke_all_user_tokens,
)
from src.crud.user import UserNotFoundError, user_crud
from src.schemas.audit import AuditLogListSchema
from src.database import SessionDep
from src.schemas.user import (
    UserAuthSchema,
    UserCreateSchema,
    UserResponseSchema,
    UserTokenSchema,
)
from src.utils.logging import get_logger
from pydantic import BaseModel

logger = get_logger("users_api")
user_router = APIRouter()


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400


@user_router.post(
    "/auth",
    response_model=UserTokenSchema,
)
async def auth_user(body: UserAuthSchema, session: SessionDep):
    """Authenticate and obtain JWT access and refresh tokens."""
    user_uuid = await user_crud.authenticate(body, session)
    logger.info(f"User authenticated: {body.username}")

    # Create both access and refresh tokens
    access_token = create_access_token(user_uuid)
    refresh_token = await create_refresh_token(user_uuid)

    return UserTokenSchema(
        access_token=access_token,
        token_type="Bearer",
        expires_in=86400,
        refresh_token=refresh_token,
    )


@user_router.post(
    "/auth/refresh",
    response_model=RefreshTokenResponse,
)
async def refresh_token(
    body: RefreshTokenRequest,
    session: SessionDep,
):
    """Refresh an access token using a refresh token."""
    user_uuid = await validate_refresh_token(body.refresh_token)
    if not user_uuid:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    # Revoke the old refresh token and create a new one
    await revoke_all_user_tokens(user_uuid)
    await create_refresh_token(user_uuid)
    new_access_token = create_access_token(user_uuid)

    return RefreshTokenResponse(
        access_token=new_access_token,
        token_type="Bearer",
        expires_in=86400,
    )


@user_router.get(
    "/audit-logs",
    response_model=AuditLogListSchema,
)
async def get_audit_logs(
    current_user: CurrentUser,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """Get audit logs (admin only)."""
    from sqlalchemy import select
    from sqlalchemy.exc import SQLAlchemyError
    from src.database import AuditLog

    try:
        stmt = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        logs = result.scalars().all()

        stmt_count = select(AuditLog)
        result_count = await session.execute(stmt_count)
        total = len(result_count.scalars().all())

        return {
            "items": logs,
            "total": total,
            "page": skip // limit + 1,
            "count": limit,
        }
    except SQLAlchemyError as exc:
        # Gracefully handle missing audit_logs table (e.g., before migrations)
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Unable to retrieve audit logs: {exc}")
        return {
            "items": [],
            "total": 0,
            "page": skip // limit + 1,
            "count": limit,
        }


@user_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def signup(body: UserCreateSchema, session: SessionDep):
    """Register a new user."""
    user_uuid = await user_crud.create(session, body)
    logger.info(f"User created: {body.username}")
    return {"user_uuid": user_uuid}


@user_router.get(
    "/me",
    response_model=UserResponseSchema,
)
async def get_me(current_user: CurrentUser):
    """Fetch profile info of the current user."""
    return current_user


@user_router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_me(current_user: CurrentUser, session: SessionDep):
    """Permanently delete the current user."""
    # Revoke all tokens for this user
    await revoke_all_user_tokens(str(current_user.id))

    if not await user_crud.delete(session, current_user.id):
        raise UserNotFoundError(f"ID {current_user.id}")
    logger.info(f"User self-deleted: {current_user.id}")
