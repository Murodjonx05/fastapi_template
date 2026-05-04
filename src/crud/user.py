from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.crud.audit import audit_log_crud
from src.crud.base import CRUDBase
from src.core.exceptions import AlreadyExistsError, NotFoundError, UnauthorizedError
from src.core.security import hash_password, verify_password
from src.models.rbac import Permission

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.models.user import User
    from src.schemas.user import UserAuthSchema, UserCreateSchema


class UserError(Exception): ...


class UserAlreadyExistsError(AlreadyExistsError):
    def __init__(self) -> None:
        super().__init__("User already exists")


class UserNotFoundError(NotFoundError):
    def __init__(self, identifier: Any) -> None:
        super().__init__(f"User not found: {identifier}")


class InvalidCredentialsError(UnauthorizedError):
    def __init__(self) -> None:
        super().__init__("Invalid credentials")


class UserCRUD(CRUDBase):
    """User service with authentication and registration logic."""

    def __init__(self) -> None:
        from src.models.user import User

        super().__init__(User)

    async def get_with_permissions(self, session: AsyncSession, user_id: int) -> "User":
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.permissions),
                selectinload(self.model.role),
            )
            .where(self.model.id == user_id)
        )
        if not (user := await session.scalar(stmt)):
            raise UserNotFoundError(user_id)
        return user

    async def list_permissions(
        self, session: AsyncSession, user_id: int
    ) -> list["Permission"]:
        user = await self.get_with_permissions(session, user_id)
        return list(user.permissions)

    async def add_permission(
        self, session: AsyncSession, user_id: int, permission_id: int
    ) -> "User":
        user = await self.get_with_permissions(session, user_id)
        permission = await session.get(Permission, permission_id)
        if not permission:
            raise ValueError(f"Permission not found: {permission_id}")
        if all(existing.id != permission_id for existing in user.permissions):
            user.permissions.append(permission)
            await session.flush()
            # Audit log
            await audit_log_crud.create_log(
                session,
                action="permission_added",
                user_id=user.id,
                target_type="permission",
                target_id=permission_id,
                details=f"Permission {permission_id} added to user {user.id}",
            )
        return user

    async def remove_permission(
        self, session: AsyncSession, user_id: int, permission_id: int
    ) -> "User":
        user = await self.get_with_permissions(session, user_id)
        old_perm_ids = [p.id for p in user.permissions]
        user.permissions[:] = [p for p in user.permissions if p.id != permission_id]
        await session.flush()
        # Audit log
        if permission_id not in old_perm_ids:
            return user
        await audit_log_crud.create_log(
            session,
            action="permission_removed",
            user_id=user.id,
            target_type="permission",
            target_id=permission_id,
            details=f"Permission {permission_id} removed from user {user.id}",
        )
        return user

    async def authenticate(self, auth: UserAuthSchema, session: AsyncSession) -> str:
        if not (user := await self.get_by_field(session, username=auth.username)):
            raise UserNotFoundError(auth.username)
        if not await verify_password(auth.password, user.password):
            # Audit log for failed login
            await audit_log_crud.create_log(
                session,
                action="login_failed",
                user_id=None,
                target_type="user",
                target_id=user.id,
                details=f"Failed login attempt for user: {auth.username}",
            )
            raise InvalidCredentialsError()
        # Audit log for successful login
        await audit_log_crud.create_log(
            session,
            action="login",
            user_id=user.id,
            target_type="user",
            target_id=user.id,
            details="User logged in successfully",
        )
        return str(user.uuid)

    async def create(self, session: AsyncSession, data: UserCreateSchema) -> str:
        try:
            hashed = await hash_password(data.password)
            dump = data.model_dump(exclude={"password", "password_confirm"})
            user = await super().create(session, {**dump, "password": hashed})
            # Audit log
            await audit_log_crud.create_log(
                session,
                action="user_created",
                user_id=user.id,
                target_type="user",
                target_id=user.id,
                details=f"New user created: {user.username}",
            )
            return str(user.uuid)
        except IntegrityError as exc:
            raise UserAlreadyExistsError() from exc

    async def delete(self, session: AsyncSession, id_: int) -> bool:
        # Get user before delete for audit log
        user = await self.get(session, id_)
        result = await session.execute(delete(self.model).where(self.model.id == id_))
        if result.rowcount > 0:
            # Audit log
            if user:
                await audit_log_crud.create_log(
                    session,
                    action="user_deleted",
                    user_id=id_,
                    target_type="user",
                    target_id=id_,
                    details=f"User deleted: {user.username if hasattr(user, 'username') else 'unknown'}",
                )
            return True
        return False


user_crud = UserCRUD()
