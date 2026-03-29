import uuid
from typing import Annotated
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import BasePk, updated_at, created_at
from src.models.rbac import Role, UserPermissionOverride

UsernameStr = Annotated[str, mapped_column(String(32), unique=True, nullable=False)]
PasswordHash = Annotated[str, mapped_column(String(255), nullable=False)]
UserUuid = Annotated[str, mapped_column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))]

class User(BasePk):
    __tablename__ = "users"

    uuid: Mapped[UserUuid]
    username: Mapped[UsernameStr]
    password: Mapped[PasswordHash]
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    role: Mapped[Role | None] = relationship(back_populates="users", foreign_keys=[role_id])
    permission_overrides: Mapped[list[UserPermissionOverride]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
