from __future__ import annotations

from typing import TypeAlias

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import HUGE_KB, LARGE_KB, MEDIUM_CHARS, SMALL_CHARS
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
)
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

_MAX_VALUE_CHARS: dict[TranslationSize, int] = {
    TranslationSize.SMALL: SMALL_CHARS,
    TranslationSize.MEDIUM: MEDIUM_CHARS,
    TranslationSize.LARGE: LARGE_KB * 1024,
    TranslationSize.HUGE: HUGE_KB * 1024,
}


def _get_model(size: TranslationSize) -> type[TranslationModel]:
    model = TRANSLATION_MODEL_MAP.get(size)
    if model is None:
        raise TranslationValidationError(f"Unsupported translation size: {size}")
    return model


def _is_duplicate_error(exc: IntegrityError) -> bool:
    orig = exc.orig
    msg = str(orig) if orig is not None else str(exc)
    if "UNIQUE constraint failed" in msg:
        return True
    if orig is not None:
        if getattr(orig, "pgcode", None) == "23505":
            return True
        if getattr(orig, "sqlstate", None) == "23505":
            return True
        if getattr(orig, "errno", None) == 1062:
            return True
        args = getattr(orig, "args", None)
        if isinstance(args, (list, tuple)) and args and args[0] == 1062:
            return True
    if "duplicate key value violates unique constraint" in msg:
        return True
    if "Duplicate entry" in msg:
        return True
    return False


async def create_translation(
    translation: TranslationCreateSchema,
    size: TranslationSize,
    session: AsyncSession,
) -> TranslationModel:
    model = _get_model(size)
    max_chars = _MAX_VALUE_CHARS.get(size)
    if max_chars is None:
        raise TranslationValidationError(f"Unsupported translation size limit: {size}")
    if len(translation.value) > max_chars:
        raise TranslationValidationError(
            f"Translation value exceeds maximum length of {max_chars} characters "
            f"for size {size.value}"
        )

    try:
        stmt = (
            insert(model)
            .values(
                key1=translation.key1,
                key2=translation.key2,
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
                translation.key1,
                translation.key2,
                translation.language_code,
            ) from exc
        raise

    i18n_logger.info(
        f"Translation created: {created.key1}.{created.key2} {created.language_code}"
    )
    return created


async def get_translation(
    key1: str,
    key2: str,
    language_code: str,
    size: TranslationSize,
    session: AsyncSession,
) -> TranslationModel:
    model = _get_model(size)
    stmt = select(model).where(
        model.key1 == key1,
        model.key2 == key2,
        model.language_code == language_code,
    )
    result = await session.execute(stmt)
    translation = result.scalar_one_or_none()
    if translation is None:
        raise TranslationNotFoundError(key1, key2, language_code)
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
        .order_by(model.key1, model.key2, model.language_code)
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
