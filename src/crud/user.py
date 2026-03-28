from sqlalchemy import insert, select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password, verify_password
from src.models.user import User
from src.schemas.user import UserAuthSchema, UserCreateSchema, UserResponseSchema

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
    return "users.username" in str(exc.orig)


async def create_user(user: UserCreateSchema, session: AsyncSession) -> int:
    try:
        hashed_password = await hash_password(user.password)

        stmt = insert(User).values(
            username=user.username,
            password=hashed_password
        ).returning(User.id)

        result = await session.execute(stmt)
        return result.scalar_one()

    except IntegrityError as exc:
        if _is_duplicate_username_error(exc):
            raise UserAlreadyExistsError(user.username) from exc
        raise


async def authenticate_user(user: UserAuthSchema, session: AsyncSession) -> int:
    # Для SELECT можно обойтись без явного begin(), просто выполняем запрос
    stmt = select(User.id, User.password).where(User.username == user.username)
    result = await session.execute(stmt)
    row = result.one_or_none()

    if row is None:
        raise InvalidCredentialsError()

    user_id, password_hash = row
    if not await verify_password(user.password, password_hash):
        raise InvalidCredentialsError()

    return user_id

async def delete_user(user_id: int, session: AsyncSession) -> None:    
    stmt = delete(User).where(User.id == user_id)
    result = await session.execute(stmt)
    if not result.rowcount:
        raise UserNotFoundError(user_id)

async def get_user(user_id: int, session: AsyncSession) -> UserResponseSchema:
    user = await session.scalar(
        select(User).where(User.id == user_id)
    )
    if not user:
        raise UserNotFoundError(user_id)
    return UserResponseSchema.model_validate(user)