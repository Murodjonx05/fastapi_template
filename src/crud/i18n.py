from __future__ import annotations

from typing import TypeAlias

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.i18n import (
    TranslationHuge,
    TranslationLarge,
    TranslationMedium,
    TranslationSmall,
)
from src.schemas.i18n import (
    TranslationAlreadyExistsError,
    TranslationCreateSchema,
    TranslationDeleteNotFoundError,
    TranslationNotFoundError,
    TranslationSize,
    TranslationValidationError,
    validate_translation_value,
)
from src.utils.db_errors import ConstraintViolationKind, get_constraint_violation_kind
from src.utils.logging import get_logger

i18n_logger = get_logger("i18n_crud")

TranslationModel: TypeAlias = (
    TranslationSmall | TranslationMedium | TranslationLarge | TranslationHuge
)

TRANSLATION_MODEL_MAP: dict[TranslationSize, type[TranslationModel]] = {
    TranslationSize.SMALL: TranslationSmall,
    TranslationSize.MEDIUM: TranslationMedium,
    TranslationSize.LARGE: TranslationLarge,
    TranslationSize.HUGE: TranslationHuge,
}


def _get_model(size: TranslationSize) -> type[TranslationModel]:
    model = TRANSLATION_MODEL_MAP.get(size)
    if model is None:
        raise TranslationValidationError(f"Unsupported translation size: {size}")
    return model


def _is_duplicate_error(exc: IntegrityError) -> bool:
    return (
        get_constraint_violation_kind(
            exc,
            message_markers=(
                "translations_",
                "uq_translations_",
                "key",
                "language_code",
            ),
        )
        == ConstraintViolationKind.UNIQUE
    )


async def create_translation(
    translation: TranslationCreateSchema,
    size: TranslationSize,
    session: AsyncSession,
) -> TranslationModel:
    model = _get_model(size)
    # Centralised length check — raises TranslationValidationError on failure.
    validate_translation_value(translation.value, size)

    try:
        stmt = (
            insert(model)
            .values(
                key=translation.key,
                language_code=translation.language_code,
                values=translation.value,
            )
            .returning(model)
        )
        result = await session.execute(stmt)
        created = result.scalar_one()
    except IntegrityError as exc:
        if _is_duplicate_error(exc):
            raise TranslationAlreadyExistsError(
                translation.key,
                translation.language_code,
            ) from exc
        raise

    i18n_logger.info(
        f"Translation created: {created.key} {created.language_code}"
    )
    return created


async def get_translation(
    key: str,
    language_code: str,
    size: TranslationSize,
    session: AsyncSession,
) -> TranslationModel:
    model = _get_model(size)
    stmt = select(model).where(
        model.key == key,
        model.language_code == language_code,
    )
    result = await session.execute(stmt)
    translation = result.scalar_one_or_none()
    if translation is None:
        raise TranslationNotFoundError(key, language_code)
    return translation


async def get_translations(
    size: TranslationSize,
    session: AsyncSession,
    page: int = 1,
    count: int = 20,
) -> list[TranslationModel]:
    if page < 1:
        raise TranslationValidationError("page must be >= 1")
    if count < 1:
        raise TranslationValidationError("count must be > 0")

    model = _get_model(size)
    offset = (page - 1) * count
    stmt = (
        select(model)
        .order_by(model.key, model.language_code)
        .offset(offset)
        .limit(count)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_translation(
    translation_id: int, size: TranslationSize, session: AsyncSession
) -> None:
    model = _get_model(size)
    result = await session.execute(delete(model).where(model.id == translation_id))
    if result.rowcount == 0:
        raise TranslationDeleteNotFoundError(translation_id, size)
