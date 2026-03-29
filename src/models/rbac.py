from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base, BasePk
from src.models.i18n import TranslationSmall

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)

user_permissions = Table(
    "user_permissions",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)


class Permission(BasePk):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    title_id: Mapped[int] = mapped_column(ForeignKey("translations_small.id"))
    description_id: Mapped[int] = mapped_column(ForeignKey("translations_small.id"))

    title: Mapped[TranslationSmall] = relationship(
        "TranslationSmall",
        foreign_keys=[title_id],
    )
    description: Mapped[TranslationSmall] = relationship(
        "TranslationSmall",
        foreign_keys=[description_id],
    )


class Role(BasePk):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    title_id: Mapped[int] = mapped_column(ForeignKey("translations_small.id"))
    description_id: Mapped[int] = mapped_column(ForeignKey("translations_small.id"))

    title: Mapped[TranslationSmall] = relationship(
        "TranslationSmall",
        foreign_keys=[title_id],
    )
    description: Mapped[TranslationSmall] = relationship(
        "TranslationSmall",
        foreign_keys=[description_id],
    )
    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary=role_permissions,
    )
