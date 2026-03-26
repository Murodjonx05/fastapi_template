import hashlib
import hmac
import secrets

from pydantic import SecretStr

ITERATIONS = 100_000
SALT_SIZE = 16


async def hash_password(password: SecretStr) -> str:
    salt = secrets.token_hex(SALT_SIZE)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.get_secret_value().encode("utf-8"),
        bytes.fromhex(salt),
        ITERATIONS,
    ).hex()
    return f"{salt}${password_hash}"


async def verify_password(password: SecretStr, password_hash: str) -> bool:
    try:
        salt, expected_hash = password_hash.split("$", maxsplit=1)
    except ValueError:
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.get_secret_value().encode("utf-8"),
        bytes.fromhex(salt),
        ITERATIONS,
    ).hex()
    return hmac.compare_digest(actual_hash, expected_hash)
