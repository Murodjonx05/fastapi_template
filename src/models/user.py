from typing import Annotated
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import BasePk, datetime_now

UsernameStr = Annotated[str, mapped_column(String(32), unique=True, nullable=False)]
PasswordHash = Annotated[str, mapped_column(String(128), nullable=False)]

class User(BasePk):
    __tablename__ = "users"

    username: Mapped[UsernameStr]
    password: Mapped[PasswordHash]
    created_at: Mapped[datetime_now]
    updated_at: Mapped[datetime_now]