import asyncio
import hashlib
import hmac
import secrets
from typing import Annotated

from authx import AuthX, AuthXConfig
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib.exceptions import HasherNotAvailable
from pwdlib import PasswordHash
from pydantic import SecretStr
from sqlalchemy import select

from src.core.settings import app_settings
from src.database import get_db_session
from src.models.user import User

ITERATIONS = 100_000
SALT_SIZE = 16
try:
    PASSWORD_HASHER = PasswordHash.recommended()
except HasherNotAvailable as exc:
    raise RuntimeError(
        "Argon2 backend is not installed. Install dependencies from requirements.txt "
        "or run: pip install 'pwdlib[argon2]'"
    ) from exc


def _build_password_hash(password: SecretStr) -> str:
    salt = secrets.token_hex(SALT_SIZE)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.get_secret_value().encode("utf-8"),
        bytes.fromhex(salt),
        ITERATIONS,
    ).hex()
    return f"{salt}${password_hash}"


async def hash_password(password: SecretStr) -> str:
    return await asyncio.to_thread(
        PASSWORD_HASHER.hash,
        password.get_secret_value(),
    )


def _verify_password_hash(password: SecretStr, password_hash: str) -> bool:
    try:
        salt, expected_hash = password_hash.split("$", maxsplit=1)
    except ValueError:
        return False
    try:
        salt_bytes = bytes.fromhex(salt)
    except ValueError:
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.get_secret_value().encode("utf-8"),
        salt_bytes,
        ITERATIONS,
    ).hex()
    return hmac.compare_digest(actual_hash, expected_hash)


async def verify_password(password: SecretStr, password_hash: str) -> bool:
    if password_hash.startswith("$argon2id$"):
        return await asyncio.to_thread(
            PASSWORD_HASHER.verify,
            password.get_secret_value(),
            password_hash,
        )
    return await asyncio.to_thread(_verify_password_hash, password, password_hash)


async def verify_and_update_password(password: SecretStr, password_hash: str) -> tuple[bool, str | None]:
    if password_hash.startswith("$argon2id$"):
        is_valid = await asyncio.to_thread(
            PASSWORD_HASHER.verify,
            password.get_secret_value(),
            password_hash,
        )
        if not is_valid:
            return False, None
        updated_hash = await asyncio.to_thread(
            PASSWORD_HASHER.verify_and_update,
            password.get_secret_value(),
            password_hash,
        )
        return True, updated_hash[1]

    is_valid = await asyncio.to_thread(_verify_password_hash, password, password_hash)
    if not is_valid:
        return False, None
    return True, await hash_password(password)


config = AuthXConfig(
    JWT_SECRET_KEY=app_settings.effective_jwt_secret_key,
    JWT_TOKEN_LOCATION=["headers"],
)
auth = AuthX(config=config, model=User)
bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    scheme_name="MainToken",
    description="Main token header. Use: Bearer <access_token>",
)


async def _get_user_by_token_subject(uid: str) -> User | None:
    async for session in get_db_session():
        return await session.scalar(select(User).where(User.uuid == uid))
    return None


auth.set_subject_getter(_get_user_by_token_subject)


def create_access_token(user_uuid: str) -> str:
    return auth.create_access_token(uid=user_uuid)


async def get_current_user(request: Request) -> User:
    user = await auth.get_current_subject(request)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_current_user_with_token(
    request: Request,
    _: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> User:
    return await get_current_user(request)


CurrentUserDep = Annotated[User, Depends(get_current_user_with_token)]
