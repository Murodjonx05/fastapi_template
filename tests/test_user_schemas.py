"""Unit tests for User schemas validation."""
from __future__ import annotations

import pytest
from pydantic import SecretStr, ValidationError

from src.schemas.user import UserAuthSchema, UserCreateSchema, UserResponseSchema


class TestUserAuthSchema:
    def test_valid_auth(self):
        schema = UserAuthSchema(username="john_doe", password=SecretStr("StrongPass123!"))
        assert schema.username == "john_doe"
        assert schema.password.get_secret_value() == "StrongPass123!"

    def test_username_too_short(self):
        with pytest.raises(ValidationError, match="too_short"):
            UserAuthSchema(username="ab", password=SecretStr("StrongPass123!"))

    def test_username_too_long(self):
        with pytest.raises(ValidationError):
            UserAuthSchema(username="a" * 33, password=SecretStr("StrongPass123!"))

    def test_username_invalid_chars(self):
        with pytest.raises(ValidationError, match="pattern"):
            UserAuthSchema(username="john doe!", password=SecretStr("StrongPass123!"))

    def test_password_too_short(self):
        with pytest.raises(ValidationError, match="too_short"):
            UserAuthSchema(username="john_doe", password=SecretStr("short"))

    def test_username_strips_whitespace(self):
        schema = UserAuthSchema(username="  john_doe  ", password=SecretStr("StrongPass123!"))
        assert schema.username == "john_doe"


class TestUserCreateSchema:
    def test_matching_passwords(self):
        schema = UserCreateSchema(
            username="test_user",
            password=SecretStr("StrongPass123!"),
            password_confirm=SecretStr("StrongPass123!"),
        )
        assert schema.username == "test_user"

    def test_mismatched_passwords(self):
        with pytest.raises(ValidationError, match="Passwords do not match"):
            UserCreateSchema(
                username="test_user",
                password=SecretStr("StrongPass123!"),
                password_confirm=SecretStr("DifferentPass!"),
            )


class TestUserResponseSchema:
    def test_valid_response(self):
        schema = UserResponseSchema(uuid="abc-123", username="john_doe")
        assert schema.uuid == "abc-123"
        assert schema.username == "john_doe"

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError, match="extra"):
            UserResponseSchema(uuid="x", username="john_doe", extra_field="bad")
