from typing import Annotated, Type
from sqlalchemy import String, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column, relationship, declared_attr

from src.database import BasePK
from src.core.constants import MEDIUM_CHARS, SMALL_CHARS

TranslationKey = Annotated[str, mapped_column(String(128), index=True)]
LanguageCode = Annotated[str, mapped_column(String(16), index=True)]

@declarative_mixin
class TranslationMixin:
    """Base mixin for translation models."""
    key: Mapped[TranslationKey]
    language_code: Mapped[LanguageCode]

class TranslationSmall(BasePK, TranslationMixin):
    __tablename__ = "translations_small"
    __table_args__ = (UniqueConstraint("key", "language_code", name="uq_translations_small_key_language"),)
    values: Mapped[str] = mapped_column(String(SMALL_CHARS))

class TranslationMedium(BasePK, TranslationMixin):
    __tablename__ = "translations_medium"
    __table_args__ = (UniqueConstraint("key", "language_code", name="uq_translations_medium_key_language"),)
    values: Mapped[str] = mapped_column(String(MEDIUM_CHARS))

class TranslationLarge(BasePK, TranslationMixin):
    __tablename__ = "translations_large"
    __table_args__ = (UniqueConstraint("key", "language_code", name="uq_translations_large_key_language"),)
    values: Mapped[str] = mapped_column(Text)

class TranslationHuge(BasePK, TranslationMixin):
    __tablename__ = "translations_huge"
    __table_args__ = (UniqueConstraint("key", "language_code", name="uq_translations_huge_key_language"),)
    values: Mapped[str] = mapped_column(Text)

def create_translation_mixin(model_cls: Type) -> Type:
    """Factory for creating translation title/description mixins."""
    class Mixin:
        @declared_attr
        def title_id(cls) -> Mapped[int]:
            return mapped_column(ForeignKey(f"{model_cls.__tablename__}.id"))

        @declared_attr
        def description_id(cls) -> Mapped[int]:
            return mapped_column(ForeignKey(f"{model_cls.__tablename__}.id"))

        @declared_attr
        def title(cls) -> Mapped[model_cls]:
            return relationship(model_cls, foreign_keys=[cls.title_id])

        @declared_attr
        def description(cls) -> Mapped[model_cls]:
            return relationship(model_cls, foreign_keys=[cls.description_id])
    return Mixin

TranslationSmallMixin = create_translation_mixin(TranslationSmall)
TranslationMediumMixin = create_translation_mixin(TranslationMedium)
TranslationLargeMixin = create_translation_mixin(TranslationLarge)
TranslationHugeMixin = create_translation_mixin(TranslationHuge)
