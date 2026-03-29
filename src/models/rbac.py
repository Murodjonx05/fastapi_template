from __future__ import annotations
import hashlib
import hmac
import secrets
from typing import TypeAlias

from sqlalchemy import ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column, relationship

from src.database import BasePk, str255_unique

PermissionsDict: TypeAlias = dict[str, bool]
ACCESS_KEY_BYTES = 32
HASH_HEX_LENGTH = 64


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@declarative_mixin
class _PermissionsDictMixin:
    permissions_dict: Mapped[PermissionsDict] = mapped_column(
        MutableDict.as_mutable(JSON), default=dict, nullable=False
    )

    def set_permissions(self, p: PermissionsDict) -> None:
        self.permissions_dict.clear()
        self.permissions_dict.update(p)

    def grant(self, key: str) -> None: self.permissions_dict[key] = True
    def revoke(self, key: str) -> None: self.permissions_dict[key] = False
    def has_permission(self, key: str) -> bool: return bool(self.permissions_dict.get(key, False))


@declarative_mixin
class _TranslationKeysMixin:
    title_key: Mapped[str] = mapped_column(String(128), nullable=False)
    description_key: Mapped[str] = mapped_column(String(128), nullable=False)


class Permission(BasePk, _TranslationKeysMixin):
    __tablename__ = "permissions"
    name: Mapped[str255_unique]
    roles: Mapped[list["Role"]] = relationship(back_populates="permissions")
    plugin_permissions: Mapped[list["PluginPermission"]] = relationship(
        back_populates="permissions", cascade="all, delete-orphan"
    )


class Role(BasePk, _TranslationKeysMixin):
    __tablename__ = "roles"
    name: Mapped[str255_unique]
    permissions_id: Mapped[int] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"))
    permissions: Mapped[Permission] = relationship(back_populates="roles")


class PluginPermission(BasePk, _PermissionsDictMixin):
    __tablename__ = "plugin_permissions"
    __table_args__ = (
        UniqueConstraint("permissions_id", "plugin_name", name="uq_plugin_permissions_container_plugin"),
        UniqueConstraint("access_key_hash", name="uq_plugin_permissions_access_key_hash"),
    )

    permissions_id: Mapped[int] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"))
    plugin_name: Mapped[str] = mapped_column(String(255), nullable=False)
    access_key_hash: Mapped[str] = mapped_column(String(HASH_HEX_LENGTH), nullable=False)
    permissions: Mapped[Permission] = relationship(back_populates="plugin_permissions")

    @classmethod
    def build(
        cls,
        *,
        plugin_name: str,
        permissions: PermissionsDict | None = None,
        permissions_id: int | None = None,
        permission: Permission | None = None,
    ) -> tuple["PluginPermission", str]:
        raw_key = secrets.token_urlsafe(ACCESS_KEY_BYTES)
        if permission is not None:
            permissions_id = permission.id
        return (
            cls(
                plugin_name=plugin_name,
                access_key_hash=_hash(raw_key),
                permissions_dict=permissions or {},
                permissions_id=permissions_id,
            ),
            raw_key,
        )

    def rotate_access_key(self) -> str:
        raw_key = secrets.token_urlsafe(ACCESS_KEY_BYTES)
        self.access_key_hash = _hash(raw_key)
        return raw_key

    def matches_access_key(self, raw: str) -> bool:
        return hmac.compare_digest(_hash(raw), self.access_key_hash)
