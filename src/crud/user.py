from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password, verify_and_update_password
from src.models.user import User
from src.schemas.user import UserAuthSchema, UserCreateSchema, UserResponseSchema
from src.utils.db_errors import ConstraintViolationKind, get_constraint_violation_kind

class UserError(Exception):
    """Base exception for user-related errors."""
    pass

class UserAlreadyExistsError(UserError):
    def __init__(self, username: str):
        super().__init__(f"User '{username}' already exists")

class InvalidCredentialsError(UserError):
    def __init__(self):
        super().__init__("Invalid username or password")

class UserNotFoundError(UserError):
    def __init__(self, identifier: str | int):
        super().__init__(f"User '{identifier}' not found")

def _is_duplicate_username(exc: IntegrityError) -> bool:
    kind = get_constraint_violation_kind(exc, message_markers=("users.username", "uq_users_username"))
    return kind == ConstraintViolationKind.UNIQUE

async def create_user(user: UserCreateSchema, session: AsyncSession) -> str:
    """Create a new user and return their UUID."""
    try:
        hashed = await hash_password(user.password)
        stmt = insert(User).values(username=user.username, password=hashed).returning(User.uuid)
        result = await session.execute(stmt)
        return result.scalar_one()
    except IntegrityError as exc:
        if _is_duplicate_username(exc):
            raise UserAlreadyExistsError(user.username) from exc
        raise

async def authenticate_user(user: UserAuthSchema, session: AsyncSession) -> str:
    """Authenticate a user and return their UUID. Handles hash upgrades."""
    db_user = await session.scalar(select(User).where(User.username == user.username))
    if not db_user:
        raise InvalidCredentialsError()

    is_valid, updated_hash = await verify_and_update_password(user.password, db_user.password)
    if not is_valid:
        raise InvalidCredentialsError()

    if updated_hash:
        db_user.password = updated_hash
        await session.flush()

    return db_user.uuid

async def get_user_by_id(user_id: int, session: AsyncSession) -> UserResponseSchema:
    """Retrieve user info by their internal numeric ID."""
    user = await session.get(User, user_id)
    if not user:
        raise UserNotFoundError(user_id)
    return UserResponseSchema.model_validate(user, from_attributes=True)

async def delete_user(user_id: int, session: AsyncSession) -> None:
    """Delete a user by their internal numeric ID."""
    stmt = delete(User).where(User.id == user_id)
    result = await session.execute(stmt)
    if result.rowcount == 0:
        raise UserNotFoundError(user_id)
