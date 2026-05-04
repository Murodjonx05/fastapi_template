from typing import Annotated, Self
import re

from pydantic import Field, SecretStr, StringConstraints, model_validator

from src.schemas.base import BaseSchema

Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$"
    ),
    Field(description="Unique username", examples=["john_doe"]),
]
Password = Annotated[
    SecretStr,
    Field(
        min_length=8,
        max_length=128,
        description="Password must contain uppercase, lowercase, number, and special character",
        examples=["StrongPass123!"],
    ),
]


class UserAuthSchema(BaseSchema):
    username: Username
    password: Password


class UserCreateSchema(UserAuthSchema):
    password_confirm: Password

    @model_validator(mode="after")
    def validate_passwords_match(self) -> Self:
        if self.password.get_secret_value() != self.password_confirm.get_secret_value():
            raise ValueError("Passwords do not match")
        return self

    @model_validator(mode="after")
    def validate_password_complexity(self) -> Self:
        """Validate password meets complexity requirements."""
        pw = self.password.get_secret_value()
        if not re.search(r"[a-z]", pw):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", pw):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", pw):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[@$!%*?&]", pw):
            raise ValueError(
                "Password must contain at least one special character (@$!%*?&)"
            )
        return self


class UserResponseSchema(BaseSchema):
    uuid: str
    username: Username


class UserTokenSchema(BaseSchema):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400
    refresh_token: str | None = None  # 24 hours in seconds
