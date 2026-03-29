from fastapi import APIRouter, HTTPException, Request

from src.core.constants import HUGE_KB, LARGE_KB, MEDIUM_CHARS, SMALL_CHARS
from src.core.limiter import limit_minute
from src.crud.i18n import create_translation, delete_translation, get_translation, get_translations
from src.database import SessionDep
from src.schemas.base import PaginationSchemaDep
from src.schemas.i18n import (
    TranslationAlreadyExistsError,
    TranslationCreateSchemaDep,
    TranslationCreateResponseSchema,
    TranslationDeleteNotFoundError,
    TranslationGetSchemaDep,
    TranslationNotFoundError,
    TranslationResponseSchema,
    TranslationSize,
    TranslationValidationError,
)
from src.utils.logging import get_logger
from src.utils.rate_limiter import limiter

i18n_logger = get_logger("i18n_api_endpoint")
i18n_router = APIRouter(prefix="/i18n")


def _to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TranslationValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, TranslationAlreadyExistsError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, TranslationNotFoundError | TranslationDeleteNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=500, detail="Internal server error")


async def _list(size: TranslationSize, session: SessionDep, page: int, count: int) -> list[TranslationResponseSchema]:
    try:
        rows = await get_translations(size, session, page=page, count=count)
        i18n_logger.info(f"Translations listed for size: {size}")
        return [TranslationResponseSchema.model_validate(r) for r in rows]
    except Exception as exc:
        i18n_logger.exception(f"Unexpected error listing translations: {exc}")
        raise _to_http_error(exc) from exc


async def _get(size: TranslationSize, key: str, language_code: str, session: SessionDep) -> TranslationResponseSchema:
    try:
        row = await get_translation(key, language_code, size, session)
        i18n_logger.info(f"Translation fetched: {key} {language_code}")
        return TranslationResponseSchema.model_validate(row)
    except Exception as exc:
        i18n_logger.exception(f"Unexpected error getting translation: {exc}")
        raise _to_http_error(exc) from exc


async def _create(size: TranslationSize, translation: TranslationCreateSchemaDep, session: SessionDep) -> TranslationCreateResponseSchema:
    try:
        created = await create_translation(translation, size, session)
        i18n_logger.info(f"Translation created: {created.key} {created.language_code}")
        return TranslationCreateResponseSchema(
            message="Translation created successfully",
            translation=TranslationResponseSchema.model_validate(created),
        )
    except Exception as exc:
        i18n_logger.exception(f"Unexpected error creating translation: {exc}")
        raise _to_http_error(exc) from exc


async def _delete(size: TranslationSize, translation_id: int, session: SessionDep) -> None:
    try:
        await delete_translation(translation_id, size, session)
        i18n_logger.info(f"Translation deleted: {translation_id}")
    except Exception as exc:
        i18n_logger.exception(f"Unexpected error deleting translation: {exc}")
        raise _to_http_error(exc) from exc


def _register_size_router(prefix: str, tag: str, size: TranslationSize) -> None:
    router = APIRouter(prefix=prefix, tags=[tag])

    # 1) LIST
    @router.get("/", response_model=list[TranslationResponseSchema])
    @limiter.limit(limit_minute(10))
    async def list_translations(request: Request, session: SessionDep, pagination: PaginationSchemaDep):
        return await _list(size, session, pagination.page, pagination.count)

    # 2) CREATE
    @router.post("/", status_code=201, response_model=TranslationCreateResponseSchema)
    @limiter.limit(limit_minute(5))
    async def create_translation_item(request: Request, translation: TranslationCreateSchemaDep, session: SessionDep):
        return await _create(size, translation, session)

    # 3) GET ITEM
    @router.get("/item", response_model=TranslationResponseSchema)
    @limiter.limit(limit_minute(10))
    async def get_translation_by_key(request: Request, translation: TranslationGetSchemaDep, session: SessionDep):
        return await _get(size, translation.key, translation.language_code, session)

    # 4) DELETE
    @router.delete("", status_code=204)
    @limiter.limit(limit_minute(5))
    async def delete_translation_item(request: Request, translation_id: int, session: SessionDep):
        await _delete(size, translation_id, session)

    i18n_router.include_router(router)


for _prefix, _tag, _size in (
    ("/small", f"i18n-small({SMALL_CHARS} chars)", TranslationSize.SMALL),
    ("/medium", f"i18n-medium({MEDIUM_CHARS} chars)", TranslationSize.MEDIUM),
    ("/large", f"i18n-large({LARGE_KB * 1024} chars)", TranslationSize.LARGE),
    ("/huge", f"i18n-huge({HUGE_KB * 1024} chars)", TranslationSize.HUGE),
):
    _register_size_router(_prefix, _tag, _size)
