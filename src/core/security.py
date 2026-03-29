from typing import Annotated
from authx import AuthX, AuthXConfig
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pwdlib import PasswordHash
from pwdlib.exceptions import HasherNotAvailable
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.settings import app_settings
from src.database import AsyncSessionMaker
from src.models.user import User

# --- Password Hashing ---
try:
    PASSWORD_HASHER = PasswordHash.recommended()
except HasherNotAvailable as exc:
    raise RuntimeError("Password hasher (Argon2) is not available. Install 'pwdlib[argon2]'.") from exc

async def hash_password(password: SecretStr) -> str:
    """Hash a password using the recommended algorithm."""
    return PASSWORD_HASHER.hash(password.get_secret_value())

async def verify_password(password: SecretStr, hashed: str) -> bool:
    """Verify a password against its hash."""
    return PASSWORD_HASHER.verify(password.get_secret_value(), hashed)

async def verify_and_update_password(password: SecretStr, hashed: str) -> tuple[bool, str | None]:
    """Verify and update the password hash if recommended."""
    is_valid, updated_hash = PASSWORD_HASHER.verify_and_update(password.get_secret_value(), hashed)
    return is_valid, updated_hash

# --- AuthX Configuration ---
config = AuthXConfig(
    JWT_SECRET_KEY=app_settings.effective_jwt_secret_key,
    JWT_TOKEN_LOCATION=["headers"],
)
auth = AuthX(config=config, model=User)

bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    scheme_name="BearerToken",
    description="Standard JWT Bearer token."
)

# --- AuthX Subject Retrieval ---
# In production, we use a fresh session. In tests, we can override this
# to use the same transactional session as the rest of the test.
TEST_SESSION_OVERRIDE: AsyncSession | None = None

async def _get_user_by_uuid(uid: str) -> User | None:
    """Internal helper for AuthX to retrieve a user by their UUID."""
    if TEST_SESSION_OVERRIDE:
        return await TEST_SESSION_OVERRIDE.scalar(select(User).where(User.uuid == uid))
        
    async with AsyncSessionMaker() as session:
        return await session.scalar(select(User).where(User.uuid == uid))

auth.set_subject_getter(_get_user_by_uuid)

# --- Dependencies ---
async def get_current_user(request: Request) -> User:
    """FastAPI dependency to get the current authenticated user."""
    user = await auth.get_current_subject(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def get_current_user_with_token(
    request: Request,
    _: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> User:
    """Wrapper to include the Bearer scheme in OpenAPI."""
    return await get_current_user(request)

CurrentUser = Annotated[User, Depends(get_current_user_with_token)]

def create_access_token(user_uuid: str) -> str:
    """Create a new JWT access token for the given user UUID."""
    return auth.create_access_token(uid=user_uuid)
