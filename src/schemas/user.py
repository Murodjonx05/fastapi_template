from datetime import datetime
from typing import Self
from typing import Annotated

from fastapi import Form
from pydantic import Field, SecretStr, StringConstraints, model_validator

from src.schemas.base import BaseSchema

Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_]+$",
    ),
    Field(
        description="Unique username",
        examples=["john_doe"],
    ),
]
Password = Annotated[
    SecretStr,
    Field(
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters long and less than 128 characters",
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


class UserResponseSchema(BaseSchema):
    id:int
    username: Username

UserAuthSchemaForm = Annotated[UserAuthSchema, Form()]
UserCreateSchemaForm = Annotated[UserCreateSchema, Form()]