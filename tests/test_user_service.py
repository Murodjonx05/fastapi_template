import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.user import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    user_crud,
)
from src.schemas.user import UserAuthSchema, UserCreateSchema


@pytest.mark.asyncio
class TestUserService:
    """Business logic tests for User management service."""

    async def test_create_user_success(self, db_session: AsyncSession):
        schema = UserCreateSchema(
            username="john_doe",
            password=SecretStr("StrongPass123!"),
            password_confirm=SecretStr("StrongPass123!"),
        )
        user_uuid = await user_crud.create(db_session, schema)
        assert user_uuid

        user = await user_crud.get(db_session, 1)
        assert user.username == "john_doe"

    async def test_create_user_duplicate_fails(self, db_session: AsyncSession):
        schema = UserCreateSchema(
            username="test_dup",
            password=SecretStr("StrongPass123!"),
            password_confirm=SecretStr("StrongPass123!"),
        )
        await user_crud.create(db_session, schema)

        with pytest.raises(UserAlreadyExistsError):
            await user_crud.create(db_session, schema)

    async def test_authenticate_user_success(self, db_session: AsyncSession):
        username = "auth_test"
        password = "Secret123!"
        await user_crud.create(
            db_session,
            UserCreateSchema(
                username=username,
                password=SecretStr(password),
                password_confirm=SecretStr(password),
            ),
        )

        user_uuid = await user_crud.authenticate(
            UserAuthSchema(username=username, password=SecretStr(password)), db_session
        )
        assert user_uuid

    async def test_authenticate_user_wrong_password_fails(
        self, db_session: AsyncSession
    ):
        username = "wrong_pass_test"
        password = "Correct123!"
        await user_crud.create(
            db_session,
            UserCreateSchema(
                username=username,
                password=SecretStr(password),
                password_confirm=SecretStr(password),
            ),
        )

        with pytest.raises(InvalidCredentialsError):
            await user_crud.authenticate(
                UserAuthSchema(username=username, password=SecretStr("wrong_password")),
                db_session,
            )

    async def test_delete_user_success(self, db_session: AsyncSession):
        await user_crud.create(
            db_session,
            UserCreateSchema(
                username="to_delete",
                password=SecretStr("StrongPass123!"),
                password_confirm=SecretStr("StrongPass123!"),
            ),
        )

        assert await user_crud.delete(db_session, 1)
        assert await user_crud.get(db_session, 1) is None
