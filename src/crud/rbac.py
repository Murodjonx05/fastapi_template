from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.i18n import TranslationSmall
from src.models.rbac import Permission, PluginPermission, Role
from src.schemas.rbac import (
    PermissionCreateSchema,
    PluginPermissionCreateSchema,
    RoleCreateSchema,
)
from src.utils.db_errors import ConstraintViolationKind, get_constraint_violation_kind


class RbacNotFoundError(Exception):
    pass


class RbacAlreadyExistsError(Exception):
    pass


class InvalidAccessKeyError(Exception):
    pass


class RbacValidationError(Exception):
    pass


def _is_unique_violation(exc: IntegrityError, *markers: str) -> bool:
    return (
        get_constraint_violation_kind(exc, message_markers=markers)
        == ConstraintViolationKind.UNIQUE
    )


async def create_permission(data: PermissionCreateSchema, session: AsyncSession) -> Permission:
    await _validate_translation_keys_exist(
        title_key=data.title_key,
        description_key=data.description_key,
        session=session,
    )
    permission = Permission(
        name=data.name,
        title_key=data.title_key,
        description_key=data.description_key,
    )
    session.add(permission)
    try:
        await session.flush()
    except IntegrityError as exc:
        if _is_unique_violation(exc, "permissions", "name"):
            raise RbacAlreadyExistsError(f"Permission '{data.name}' already exists") from exc
        raise
    return permission


async def get_permission(permission_id: int, session: AsyncSession) -> Permission:
    stmt = (
        select(Permission)
        .options(selectinload(Permission.plugin_permissions))
        .where(Permission.id == permission_id)
    )
    permission = await session.scalar(stmt)
    if permission is None:
        raise RbacNotFoundError(f"Permission with id {permission_id} not found")
    return permission


async def create_role(data: RoleCreateSchema, session: AsyncSession) -> Role:
    await _validate_translation_keys_exist(
        title_key=data.title_key,
        description_key=data.description_key,
        session=session,
    )
    role = Role(
        name=data.name,
        title_key=data.title_key,
        description_key=data.description_key,
        permissions_id=data.permissions_id,
    )
    session.add(role)
    try:
        await session.flush()
    except IntegrityError as exc:
        if _is_unique_violation(exc, "roles", "name"):
            raise RbacAlreadyExistsError(f"Role '{data.name}' already exists") from exc
        raise
    return role


async def get_role(role_id: int, session: AsyncSession) -> Role:
    role = await session.scalar(select(Role).where(Role.id == role_id))
    if role is None:
        raise RbacNotFoundError(f"Role with id {role_id} not found")
    return role


async def create_plugin_permission(
    data: PluginPermissionCreateSchema,
    session: AsyncSession,
) -> tuple[PluginPermission, str]:
    plugin_permission, access_key = PluginPermission.build(
        plugin_name=data.plugin_name,
        permissions=data.permissions_dict,
        permissions_id=data.permissions_id,
    )
    session.add(plugin_permission)
    try:
        await session.flush()
    except IntegrityError as exc:
        if _is_unique_violation(exc, "plugin_permissions", "plugin_name"):
            raise RbacAlreadyExistsError(
                f"Plugin permission '{data.plugin_name}' already exists in this permission container"
            ) from exc
        raise
    return plugin_permission, access_key


async def get_plugin_permission(plugin_permission_id: int, session: AsyncSession) -> PluginPermission:
    plugin_permission = await session.scalar(
        select(PluginPermission).where(PluginPermission.id == plugin_permission_id)
    )
    if plugin_permission is None:
        raise RbacNotFoundError(
            f"Plugin permission with id {plugin_permission_id} not found"
        )
    return plugin_permission


async def get_plugin_permissions_dict_by_access_key(
    plugin_permission_id: int,
    access_key: str,
    session: AsyncSession,
) -> dict[str, bool]:
    plugin_permission = await get_plugin_permission(plugin_permission_id, session)
    if not plugin_permission.matches_access_key(access_key):
        raise InvalidAccessKeyError("Invalid plugin access key")
    return dict(plugin_permission.permissions_dict)


async def _validate_translation_keys_exist(
    *,
    title_key: str,
    description_key: str,
    session: AsyncSession,
) -> None:
    if not await _translation_key_exists(title_key, session):
        raise RbacValidationError(
            f"title key '{title_key}' is not found in translations_small"
        )
    if not await _translation_key_exists(description_key, session):
        raise RbacValidationError(
            f"description key '{description_key}' is not found in translations_small"
        )


async def _translation_key_exists(key: str, session: AsyncSession) -> bool:
    stmt = (
        select(TranslationSmall.id)
        .where(TranslationSmall.key == key)
        .limit(1)
    )
    return (await session.scalar(stmt)) is not None
