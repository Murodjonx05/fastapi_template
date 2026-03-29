from __future__ import annotations
from typing import TYPE_CHECKING, Any
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from src.crud.base import CRUDBase
from src.models.rbac import Permission
from src.models.user import User
from src.core.security import hash_password, verify_password
from src.core.exceptions import AlreadyExistsError, NotFoundError, UnauthorizedError
if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.schemas.user import UserAuthSchema, UserCreateSchema


class UserError(Exception):
    pass

class UserAlreadyExistsError(AlreadyExistsError):
    def __init__(self):
        super().__init__("User already exists")

class UserNotFoundError(NotFoundError):
    def __init__(self, identifier: Any):
        super().__init__(f"User not found: {identifier}")

class InvalidCredentialsError(UnauthorizedError):
    def __init__(self):
        super().__init__("Invalid credentials")

class UserCRUD(CRUDBase[User]):
    """Optimized User service with authentication and registration logic."""
    def __init__(self):
        super().__init__(User)

    async def get_with_permissions(self, session: AsyncSession, user_id: int) -> User:
        stmt = (
            select(User)
            .options(selectinload(User.permissions), selectinload(User.role))
            .where(User.id == user_id)
        )
        if not (user := await session.scalar(stmt)):
            raise UserNotFoundError(user_id)
        return user

    async def list_permissions(self, session: AsyncSession, user_id: int) -> list[Permission]:
        user = await self.get_with_permissions(session, user_id)
        return list(user.permissions)

    async def add_permission(self, session: AsyncSession, user_id: int, permission_id: int) -> User:
        user = await self.get_with_permissions(session, user_id)
        permission = await session.get(Permission, permission_id)
        if permission is None:
            raise ValueError(f"Permission not found: {permission_id}")
        if all(existing.id != permission_id for existing in user.permissions):
            user.permissions.append(permission)
            await session.flush()
        return user

    async def remove_permission(self, session: AsyncSession, user_id: int, permission_id: int) -> User:
        user = await self.get_with_permissions(session, user_id)
        user.permissions[:] = [
            permission for permission in user.permissions if permission.id != permission_id
        ]
        await session.flush()
        return user

    async def authenticate(self, auth: UserAuthSchema, session: AsyncSession) -> str:
        if not (user := await self.get_by_field(session, username=auth.username)):
            raise UserNotFoundError(auth.username)
        if not await verify_password(auth.password, user.password):
            raise InvalidCredentialsError()
        return str(user.uuid)

    async def create(self, session: AsyncSession, data: UserCreateSchema) -> str:
        try:
            hashed = await hash_password(data.password)
            dump = data.model_dump(exclude={"password", "password_confirm"})
            user = await super().create(session, {**dump, "password": hashed})
            return str(user.uuid)
        except IntegrityError as exc:
            raise UserAlreadyExistsError() from exc

user_crud = UserCRUD()
