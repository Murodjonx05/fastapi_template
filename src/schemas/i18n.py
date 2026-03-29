from enum import StrEnum
from typing import Annotated

from fastapi import Depends
from pydantic import AliasChoices, Field, StringConstraints

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


class I18nError(Exception):
    """Base for i18n domain errors."""


class TranslationValidationError(I18nError):
    """Invalid pagination, value length, or size."""


class TranslationAlreadyExistsError(I18nError):
    def __init__(self, key: str, language_code: str) -> None:
        super().__init__(
            f"Translation '{key}' for language '{language_code}' already exists"
        )


class TranslationNotFoundError(I18nError):
    def __init__(self, key: str, language_code: str) -> None:
        super().__init__(
            f"Translation '{key}' for language '{language_code}' not found"
        )


class TranslationDeleteNotFoundError(I18nError):
    def __init__(self, id: int, size: TranslationSize) -> None:
        super().__init__(
            f"Translation with id '{id}' and size '{size.value}' to delete not found"
        )


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
