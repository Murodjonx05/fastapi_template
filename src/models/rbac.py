from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from src.database import BasePK
from src.models.i18n import TranslationSmallMixin

if TYPE_CHECKING:
    from src.models.user import User

role_permissions = Table(
    "role_permissions",
    BasePK.metadata,
    Column("role_id", ForeignKey("rbac.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)

user_permissions = Table(
    "user_permissions",
    BasePK.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)


class Permission(BasePK, TranslationSmallMixin):
    __tablename__ = "permissions"
    name: Mapped[str] = mapped_column(unique=True)

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_permissions",
        back_populates="permissions",
    )


class Role(BasePK, TranslationSmallMixin):
    __tablename__ = "rbac"
    name: Mapped[str] = mapped_column(unique=True)
    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, back_populates="roles"
    )
    users: Mapped[list["User"]] = relationship(back_populates="role")


Permission.roles = relationship(
    "Role",
    secondary=role_permissions,
    back_populates="permissions",
)
