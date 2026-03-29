import asyncio
import hashlib
import hmac
import secrets

from pydantic import SecretStr

ITERATIONS = 100_000
SALT_SIZE = 16


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
    return await asyncio.to_thread(_build_password_hash, password)


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
    return await asyncio.to_thread(_verify_password_hash, password, password_hash)
