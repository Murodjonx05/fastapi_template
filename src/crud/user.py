from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password, verify_and_update_password
from src.models.user import User
from src.schemas.user import UserAuthSchema, UserCreateSchema, UserResponseSchema
from src.utils.db_errors import ConstraintViolationKind, get_constraint_violation_kind

class UserAlreadyExistsError(Exception):
    def __init__(self, username: str):
        super().__init__(f"User with username '{username}' already exists")


class InvalidCredentialsError(Exception):
    def __init__(self):
        super().__init__("Invalid username or password")

class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        super().__init__(f"User with id {user_id} not found")


def _is_duplicate_username_error(exc: IntegrityError) -> bool:
    return (
        get_constraint_violation_kind(
            exc,
            message_markers=("users.username", "uq_users_username"),
        )
        == ConstraintViolationKind.UNIQUE
    )


async def create_user(user: UserCreateSchema, session: AsyncSession) -> str:
    try:
        hashed_password = await hash_password(user.password)

        stmt = insert(User).values(
            username=user.username,
            password=hashed_password,
        ).returning(User.uuid)

        result = await session.execute(stmt)
        return result.scalar_one()

    except IntegrityError as exc:
        if _is_duplicate_username_error(exc):
            raise UserAlreadyExistsError(user.username) from exc
        raise


async def authenticate_user(user: UserAuthSchema, session: AsyncSession) -> str:
    db_user = await session.scalar(
        select(User).where(User.username == user.username)
    )

    if db_user is None:
        raise InvalidCredentialsError()

    is_valid, updated_hash = await verify_and_update_password(user.password, db_user.password)
    if not is_valid:
        raise InvalidCredentialsError()

    if updated_hash is not None and updated_hash != db_user.password:
        db_user.password = updated_hash
        await session.flush()

    return db_user.uuid

async def delete_user(user_id: int, session: AsyncSession) -> None:
    stmt = delete(User).where(User.id == user_id)
    result = await session.execute(stmt)
    if not result.rowcount:
        raise UserNotFoundError(user_id)

async def get_user(user_id: int, session: AsyncSession) -> UserResponseSchema:
    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise UserNotFoundError(user_id)
    return UserResponseSchema.model_validate(
        {
            "uuid": user.uuid,
            "username": user.username,
        }
    )
