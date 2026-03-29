import uuid
from typing import Annotated
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.rbac import Permission, Role, user_permissions
from src.database import BasePK, timestamp, updated_timestamp

UserUuid = Annotated[str, mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))]
UsernameStr = Annotated[str, mapped_column(String(32), unique=True)]
PasswordHash = Annotated[str, mapped_column(String(255))]

class User(BasePK):
    __tablename__ = "users"

    uuid: Mapped[UserUuid]
    username: Mapped[UsernameStr]
    password: Mapped[PasswordHash]

    created_at: Mapped[timestamp]
    updated_at: Mapped[updated_timestamp]

    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)
    role: Mapped[Role | None] = relationship("Role", foreign_keys=[role_id])

    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary=user_permissions,
    )
