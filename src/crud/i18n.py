from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

from src.crud.base import CRUDBase
from src.models.i18n import (
    TranslationSmall,
    TranslationMedium,
    TranslationLarge,
    TranslationHuge,
)
from src.schemas.i18n import (
    TranslationSize,
    validate_translation_value,
    TranslationAlreadyExistsError,
    TranslationNotFoundError,
    TranslationDeleteNotFoundError,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.schemas.i18n import TranslationCreateSchema

_CRUD_MAP = {
    TranslationSize.SMALL: CRUDBase(TranslationSmall),
    TranslationSize.MEDIUM: CRUDBase(TranslationMedium),
    TranslationSize.LARGE: CRUDBase(TranslationLarge),
    TranslationSize.HUGE: CRUDBase(TranslationHuge),
}


async def create_translation(
    data: TranslationCreateSchema,
    size: TranslationSize,
    session: AsyncSession,
):
    validate_translation_value(data.value, size)
    try:
        return await _CRUD_MAP[size].create(
            session,
            {"key": data.key, "language_code": data.language_code, "values": data.value},
        )
    except IntegrityError as exc:
        raise TranslationAlreadyExistsError(data.key, data.language_code) from exc


async def get_translation(
    key: str, lang: str, size: TranslationSize, session: AsyncSession
):
    if not (obj := await _CRUD_MAP[size].get_by_field(session, key=key, language_code=lang)):
        raise TranslationNotFoundError(key, lang)
    return obj


async def get_translations(
    size: TranslationSize, session: AsyncSession, page: int = 1, count: int = 20
):
    return await _CRUD_MAP[size].list(session, offset=(page - 1) * count, limit=count)


async def delete_translation(id_: int, size: TranslationSize, session: AsyncSession):
    if not await _CRUD_MAP[size].delete(session, id_):
        raise TranslationDeleteNotFoundError(id_, size)
