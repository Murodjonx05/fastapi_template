from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from src.core.security import hash_password, verify_password
from src.database import async_session
from src.models.user import User
from src.schemas.user import UserAuthSchema, UserCreateSchema

class UserAlreadyExistsError(Exception):
    def __init__(self, username: str):
        super().__init__(f"User with username '{username}' already exists")


class InvalidCredentialsError(Exception):
    def __init__(self):
        super().__init__("Invalid username or password")


def _is_duplicate_username_error(exc: IntegrityError) -> bool:
    return "users.username" in str(exc.orig)


async def create_user(user: UserCreateSchema) -> int:
    async with async_session() as session:
        try:
            async with session.begin():
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


async def authenticate_user(user: UserAuthSchema) -> int:
    async with async_session() as session:
        stmt = select(User.id, User.password).where(User.username == user.username)
        result = await session.execute(stmt)
        row = result.one_or_none()

        if row is None:
            raise InvalidCredentialsError()

        user_id, password_hash = row
        if not await verify_password(user.password, password_hash):
            raise InvalidCredentialsError()

        return user_id
