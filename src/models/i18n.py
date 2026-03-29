from typing import Annotated

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from src.database import BasePk
from src.core.constants import MEDIUM_CHARS, SMALL_CHARS


TranslationKey = Annotated[str, mapped_column(String(128), index=True)]
LanguageCode = Annotated[str, mapped_column(String(3), index=True)]


@declarative_mixin
class Translation:
    key1: Mapped[TranslationKey]
    key2: Mapped[TranslationKey]
    language_code: Mapped[LanguageCode]


class TranslationSmall(BasePk, Translation):
    __tablename__ = "translations_small"
    __table_args__ = (
        UniqueConstraint(
            "key1",
            "key2",
            "language_code",
            name="uq_translations_small_key_language",
        ),
    )
    values: Mapped[str] = mapped_column(String(SMALL_CHARS), nullable=False)


class TranslationMedium(BasePk, Translation):
    __tablename__ = "translations_medium"
    __table_args__ = (
        UniqueConstraint(
            "key1",
            "key2",
            "language_code",
            name="uq_translations_medium_key_language",
        ),
    )
    values: Mapped[str] = mapped_column(String(MEDIUM_CHARS), nullable=False)


class TranslationLarge(BasePk, Translation):
    __tablename__ = "translations_large"
    __table_args__ = (
        UniqueConstraint(
            "key1",
            "key2",
            "language_code",
            name="uq_translations_large_key_language",
        ),
    )
    values: Mapped[str] = mapped_column(Text, nullable=False)


class TranslationHuge(BasePk, Translation):
    __tablename__ = "translations_huge"
    __table_args__ = (
        UniqueConstraint(
            "key1",
            "key2",
            "language_code",
            name="uq_translations_huge_key_language",
        ),
    )
    values: Mapped[str] = mapped_column(Text, nullable=False)
