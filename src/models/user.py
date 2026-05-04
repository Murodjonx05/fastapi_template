import uuid
from typing import TYPE_CHECKING, Annotated

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import BasePK, timestamp, updated_timestamp

if TYPE_CHECKING:
    from src.models.rbac import Permission, Role

UserUuid = Annotated[
    str,
    mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    ),
]
UsernameStr = Annotated[str, mapped_column(String(32), unique=True)]
PasswordHash = Annotated[str, mapped_column(String(255))]


class User(BasePK):
    __tablename__ = "users"

    uuid: Mapped[UserUuid]
    username: Mapped[UsernameStr]
    password: Mapped[PasswordHash]

    created_at: Mapped[timestamp]
    updated_at: Mapped[updated_timestamp]

    role_id: Mapped[int | None] = mapped_column(
        ForeignKey("rbac.id", ondelete="SET NULL"), nullable=True
    )
    role: Mapped["Role | None"] = relationship("Role", foreign_keys=[role_id])

    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="user_permissions",
        back_populates="users",
        cascade="all, delete",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"

    def to_dict(self) -> dict[str, str | int | None]:
        """Return a dictionary representation of the user."""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "username": self.username,
            "role_id": self.role_id,
        }
