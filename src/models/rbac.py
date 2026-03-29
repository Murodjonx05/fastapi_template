from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base, BasePK
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

class Permission(BasePK):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(unique=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("translations_small.id"))
    description_id: Mapped[int] = mapped_column(ForeignKey("translations_small.id"))

    title: Mapped[TranslationSmall] = relationship(foreign_keys=[title_id])
    description: Mapped[TranslationSmall] = relationship(foreign_keys=[description_id])

class Role(BasePK):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(unique=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("translations_small.id"))
    description_id: Mapped[int] = mapped_column(ForeignKey("translations_small.id"))

    title: Mapped[TranslationSmall] = relationship(foreign_keys=[title_id])
    description: Mapped[TranslationSmall] = relationship(foreign_keys=[description_id])
    
    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permissions,
    )
