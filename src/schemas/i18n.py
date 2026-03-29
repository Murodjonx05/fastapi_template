from enum import StrEnum
from typing import Annotated

from fastapi import Depends
from pydantic import AliasChoices, Field, StringConstraints

from src.core.constants import HUGE_KB, LARGE_KB, MEDIUM_CHARS, SMALL_CHARS
from src.core.exceptions import AlreadyExistsError, DomainError, NotFoundError, ValidationError
from src.schemas.base import BaseSchema

TranslationKey = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=128),
]
LanguageCode = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=16),
]
TranslationValue = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class TranslationSize(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"


# ---------------------------------------------------------------------------
# Per-size max-length map — single source of truth for value length limits.
# Used by TranslationCreateSchema.validate_value_length() and in CRUD as a
# guard.  Changing a limit here automatically propagates everywhere.
# ---------------------------------------------------------------------------
MAX_VALUE_CHARS: dict["TranslationSize", int] = {
    TranslationSize.SMALL: SMALL_CHARS,
    TranslationSize.MEDIUM: MEDIUM_CHARS,
    TranslationSize.LARGE: LARGE_KB * 1024,
    TranslationSize.HUGE: HUGE_KB * 1024,
}


class I18nError(DomainError):
    """Base for i18n domain errors."""

class TranslationValidationError(ValidationError):
    """Invalid pagination, value length, or size."""
    def __init__(self, message: str) -> None:
        super().__init__(message)

class TranslationAlreadyExistsError(AlreadyExistsError):
    def __init__(self, key: str, language_code: str) -> None:
        super().__init__(
            f"Translation '{key}' for language '{language_code}' already exists"
        )

class TranslationNotFoundError(NotFoundError):
    def __init__(self, key: str, language_code: str) -> None:
        super().__init__(
            f"Translation '{key}' for language '{language_code}' not found"
        )

class TranslationDeleteNotFoundError(NotFoundError):
    def __init__(self, id: int, size: TranslationSize) -> None:
        super().__init__(
            f"Translation with id '{id}' and size '{size.value}' to delete not found"
        )


def validate_translation_value(value: str, size: TranslationSize) -> str:
    """Validate that *value* fits within the character limit for *size*.

    Raises ``TranslationValidationError`` when the value is too long.
    This is the **canonical** check — call it from CRUD or API layers to
    enforce the constraint before touching the database.
    """
    max_chars = MAX_VALUE_CHARS.get(size)
    if max_chars is None:
        raise TranslationValidationError(f"Unsupported translation size: {size}")
    if len(value) > max_chars:
        raise TranslationValidationError(
            f"Translation value exceeds maximum length of {max_chars} characters "
            f"for size {size.value}"
        )
    return value


class TranslationCreateSchema(BaseSchema):
    key: TranslationKey = Field(examples=["home.title"])
    language_code: LanguageCode = Field(examples=["en"])
    value: TranslationValue = Field(examples=["Welcome"])


class TranslationGetSchema(BaseSchema):
    key: TranslationKey = Field(examples=["home.title"])
    language_code: LanguageCode = Field(examples=["en"])


class TranslationResponseSchema(BaseSchema):
    id: int
    key: TranslationKey
    language_code: LanguageCode
    value: TranslationValue = Field(
        validation_alias=AliasChoices("value", "values"),
        serialization_alias="value",
    )


class TranslationCreateResponseSchema(BaseSchema):
    message: str
    translation: TranslationResponseSchema


TranslationCreateSchemaDep = Annotated[TranslationCreateSchema, Depends(TranslationCreateSchema)]
TranslationGetSchemaDep = Annotated[TranslationGetSchema, Depends(TranslationGetSchema)]
