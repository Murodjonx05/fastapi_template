from typing import Annotated

from sqlalchemy import String, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column, relationship, declared_attr

from src.database import BasePk
from src.core.constants import MEDIUM_CHARS, SMALL_CHARS

TranslationKey = Annotated[str, mapped_column(String(128), index=True)]
LanguageCode = Annotated[str, mapped_column(String(16), index=True)]


@declarative_mixin
class Translation:
    key: Mapped[TranslationKey]
    language_code: Mapped[LanguageCode]


class TranslationSmall(BasePk, Translation):
    __tablename__ = "translations_small"
    __table_args__ = (
        UniqueConstraint(
            "key",
            "language_code",
            name="uq_translations_small_key_language",
        ),
    )
    values: Mapped[str] = mapped_column(String(SMALL_CHARS), nullable=False)


class TranslationMedium(BasePk, Translation):
    __tablename__ = "translations_medium"
    __table_args__ = (
        UniqueConstraint(
            "key",
            "language_code",
            name="uq_translations_medium_key_language",
        ),
    )
    values: Mapped[str] = mapped_column(String(MEDIUM_CHARS), nullable=False)


class TranslationLarge(BasePk, Translation):
    __tablename__ = "translations_large"
    __table_args__ = (
        UniqueConstraint(
            "key",
            "language_code",
            name="uq_translations_large_key_language",
        ),
    )
    values: Mapped[str] = mapped_column(Text, nullable=False)


class TranslationHuge(BasePk, Translation):
    __tablename__ = "translations_huge"
    __table_args__ = (
        UniqueConstraint(
            "key",
            "language_code",
            name="uq_translations_huge_key_language",
        ),
    )
    values: Mapped[str] = mapped_column(Text, nullable=False)


@declarative_mixin
class TranslationSmallTitleDescriptionMixin:
    @declared_attr
    def title_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("translations_small.id"))

    @declared_attr
    def description_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("translations_small.id"))

    @declared_attr
    def title(cls) -> Mapped[TranslationSmall]:
        return relationship(foreign_keys=[cls.title_id])

    @declared_attr
    def description(cls) -> Mapped[TranslationSmall]:
        return relationship(foreign_keys=[cls.description_id])

@declarative_mixin
class TranslationMediumTitleDescriptionMixin:
    @declared_attr
    def title_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("translations_medium.id"))

    @declared_attr
    def description_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("translations_medium.id"))

    @declared_attr
    def title(cls) -> Mapped[TranslationMedium]:
        return relationship(foreign_keys=[cls.title_id])

    @declared_attr
    def description(cls) -> Mapped[TranslationMedium]:
        return relationship(foreign_keys=[cls.description_id])

@declarative_mixin
class TranslationLargeTitleDescriptionMixin:
    @declared_attr
    def title_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("translations_large.id"))

    @declared_attr
    def description_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("translations_large.id"))

    @declared_attr
    def title(cls) -> Mapped[TranslationLarge]:
        return relationship(foreign_keys=[cls.title_id])

    @declared_attr
    def description(cls) -> Mapped[TranslationLarge]:
        return relationship(foreign_keys=[cls.description_id])

@declarative_mixin
class TranslationHugeTitleDescriptionMixin:
    @declared_attr
    def title_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("translations_huge.id"))

    @declared_attr
    def description_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("translations_huge.id"))

    @declared_attr
    def title(cls) -> Mapped[TranslationHuge]:
        return relationship(foreign_keys=[cls.title_id])

    @declared_attr
    def description(cls) -> Mapped[TranslationHuge]:
        return relationship(foreign_keys=[cls.description_id])


# Backward-compat aliases for old typoed names.
TranslationSmallTitleDecriptionMixin = TranslationSmallTitleDescriptionMixin
TranslationMediumTitleDecriptionMixin = TranslationMediumTitleDescriptionMixin
TranslationLargeTitleDecriptionMixin = TranslationLargeTitleDescriptionMixin
TranslationHugeTitleDecriptionMixin = TranslationHugeTitleDescriptionMixin
