import contextvars
from typing import Annotated

from authx import AuthX, AuthXConfig
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pwdlib import PasswordHash
from pwdlib.exceptions import HasherNotAvailable
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import secrets
import time

from src.core.settings import app_settings
from src.database import AsyncSessionMaker
from src.models.user import User


try:
    PASSWORD_HASHER = PasswordHash.recommended()
except HasherNotAvailable as exc:
    raise RuntimeError(
        "Password hasher (Argon2) is not available. Install 'pwdlib[argon2]'."
    ) from exc


async def hash_password(password: SecretStr) -> str:
    """Hash a password using the recommended algorithm."""
    return PASSWORD_HASHER.hash(password.get_secret_value())


async def verify_password(password: SecretStr, hashed: str) -> bool:
    """Verify a password against its hash."""
    return PASSWORD_HASHER.verify(password.get_secret_value(), hashed)


async def verify_and_update_password(
    password: SecretStr, hashed: str
) -> tuple[bool, str | None]:
    """Verify and update the password hash if recommended."""
    is_valid, updated_hash = PASSWORD_HASHER.verify_and_update(
        password.get_secret_value(), hashed
    )
    return is_valid, updated_hash


# --- AuthX Configuration ---
config = AuthXConfig(
    JWT_SECRET_KEY=app_settings.effective_jwt_secret_key,
    JWT_TOKEN_LOCATION=["headers"],
    JWT_ACCESS_TOKEN_EXPIRES=86400,  # 24 hours in seconds
)

auth = AuthX(config=config, model=User)

# Bearer token scheme for OpenAPI documentation (shows lock icons)
bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    scheme_name="BearerToken",
    description="JWT Authentication token - required for protected endpoints",
)

# --- AuthX Subject Retrieval ---
# Refresh token store (in production, use Redis or database)
_REFRESH_TOKENS: dict[str, dict] = {}


def _generate_refresh_token() -> str:
    """Generate a secure random refresh token."""
    return secrets.token_urlsafe(64)


def _create_refresh_token_data(user_uuid: str) -> dict:
    """Create refresh token metadata."""
    return {
        "user_uuid": user_uuid,
        "created_at": time.time(),
        "expires_at": time.time() + 7 * 24 * 3600,  # 7 days
    }


async def create_refresh_token(user_uuid: str) -> str:
    """Create and store a refresh token for a user."""
    token = _generate_refresh_token()
    _REFRESH_TOKENS[token] = _create_refresh_token_data(user_uuid)
    return token


async def validate_refresh_token(token: str) -> str | None:
    """Validate a refresh token and return the user UUID."""
    data = _REFRESH_TOKENS.get(token)
    if not data:
        return None
    if time.time() > data["expires_at"]:
        del _REFRESH_TOKENS[token]
        return None
    return data["user_uuid"]


async def revoke_refresh_token(token: str) -> None:
    """Revoke a refresh token."""
    _REFRESH_TOKENS.pop(token, None)


async def revoke_all_user_tokens(user_uuid: str) -> None:
    """Revoke all refresh tokens for a user."""
    tokens_to_remove = [
        token
        for token, data in _REFRESH_TOKENS.items()
        if data["user_uuid"] == user_uuid
    ]
    for token in tokens_to_remove:
        del _REFRESH_TOKENS[token]


# Use ContextVar for thread/coroutine safe session overrides in tests.
TEST_SESSION_OVERRIDE: contextvars.ContextVar[AsyncSession | None] = (
    contextvars.ContextVar("test_session", default=None)
)


async def _get_user_by_uuid(uid: str) -> User | None:
    """Internal helper for AuthX to retrieve a user by their UUID."""
    stmt = (
        select(User)
        .options(selectinload(User.role), selectinload(User.permissions))
        .where(User.uuid == uid)
    )
    if (session := TEST_SESSION_OVERRIDE.get()) is not None:
        return await session.scalar(stmt)

    async with AsyncSessionMaker() as session:
        return await session.scalar(stmt)


auth.set_subject_getter(_get_user_by_uuid)


# --- Dependencies ---
async def get_current_user(
    request: Request,
    _: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> User:
    """FastAPI dependency to get the current authenticated user.

    Shows lock icon in OpenAPI docs for protected endpoints.
    """
    user = await auth.get_current_subject(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


class RoleChecker:
    """Dependency for checking User rbac during requests."""

    def __init__(self, allowed_rbac: list[str]) -> None:
        self.allowed_rbac = allowed_rbac

    async def __call__(self, user: CurrentUser) -> User:
        if not user.role or user.role.name not in self.allowed_rbac:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions. Admin role required.",
            )
        return user


AdminOnly = Annotated[User, Depends(RoleChecker(["admin"]))]


def create_access_token(user_uuid: str) -> str:
    """Create a new JWT access token for the given user UUID."""
    return auth.create_access_token(uid=user_uuid)
