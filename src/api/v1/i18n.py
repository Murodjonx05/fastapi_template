from fastapi import APIRouter, HTTPException, Request

from src.core.limiter import limit_minute
from src.crud.i18n import (
    create_translation,
    delete_translation,
    get_translation,
    get_translations,
)
from src.database import SessionDep
from src.schemas.base import PaginationSchemaDep
from src.schemas.i18n import (
    TranslationAlreadyExistsError,
    TranslationCreateResponseSchema,
    TranslationCreateSchema,
    TranslationCreateSchemaDep,
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
small_i18n_router = APIRouter(prefix="/small", tags=["i18n-small"])
medium_i18n_router = APIRouter(prefix="/medium", tags=["i18n-medium"])
large_i18n_router = APIRouter(prefix="/large", tags=["i18n-large"])
huge_i18n_router = APIRouter(prefix="/huge", tags=["i18n-huge"])
i18n_router = APIRouter(prefix="/i18n")


def _bad_request(exc: TranslationValidationError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


async def _list_i18n_translations(
    size: TranslationSize,
    session: SessionDep,
    page: int,
    count: int,
) -> list[TranslationResponseSchema]:
    try:
        rows = await get_translations(size, session, page=page, count=count)
        i18n_logger.info(f"Translations listed for size: {size}")
        return [TranslationResponseSchema.model_validate(r) for r in rows]
    except TranslationValidationError as exc:
        raise _bad_request(exc) from exc
    except Exception as exc:
        i18n_logger.exception(f"Unexpected error listing translations: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


async def _get_i18n_translation(
    size: TranslationSize,
    key1: str,
    key2: str,
    language_code: str,
    session: SessionDep,
) -> TranslationResponseSchema:
    try:
        row = await get_translation(key1, key2, language_code, size, session)
        i18n_logger.info(f"Translation fetched: {key1}.{key2} {language_code}")
        return TranslationResponseSchema.model_validate(row)
    except TranslationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        i18n_logger.exception(f"Unexpected error getting translation: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


async def _create_i18n_translation(
    translation: TranslationCreateSchema,
    size: TranslationSize,
    session: SessionDep,
) -> TranslationCreateResponseSchema:
    try:
        created = await create_translation(translation, size, session)
        i18n_logger.info(
            f"Translation created: {created.key1}.{created.key2} {created.language_code}"
        )
        return TranslationCreateResponseSchema(
            message="Translation created successfully",
            translation=TranslationResponseSchema.model_validate(created),
        )
    except TranslationAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except TranslationValidationError as exc:
        raise _bad_request(exc) from exc
    except Exception as exc:
        i18n_logger.exception(f"Unexpected error creating translation: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


async def _delete_i18n_translation(
    size: TranslationSize,
    translation_id: int,
    session: SessionDep,
) -> None:
    try:
        await delete_translation(translation_id, size, session)
        i18n_logger.info(f"Translation deleted: {translation_id}")
    except TranslationDeleteNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        i18n_logger.error(f"Unexpected error deleting translation: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@small_i18n_router.get("/", response_model=list[TranslationResponseSchema])
@limiter.limit(limit_minute(10))
async def list_small_translations(
    request: Request,
    session: SessionDep,
    pagination: PaginationSchemaDep,
):
    return await _list_i18n_translations(
        TranslationSize.SMALL, session, pagination.page, pagination.count
    )


@medium_i18n_router.get("/", response_model=list[TranslationResponseSchema])
@limiter.limit(limit_minute(10))
async def list_medium_translations(
    request: Request,
    session: SessionDep,
    pagination: PaginationSchemaDep,
):
    return await _list_i18n_translations(
        TranslationSize.MEDIUM, session, pagination.page, pagination.count
    )


@large_i18n_router.get("/", response_model=list[TranslationResponseSchema])
@limiter.limit(limit_minute(10))
async def list_large_translations(
    request: Request,
    session: SessionDep,
    pagination: PaginationSchemaDep,
):
    return await _list_i18n_translations(
        TranslationSize.LARGE, session, pagination.page, pagination.count
    )


@huge_i18n_router.get("/", response_model=list[TranslationResponseSchema])
@limiter.limit(limit_minute(10))
async def list_huge_translations(
    request: Request,
    session: SessionDep,
    pagination: PaginationSchemaDep,
):
    return await _list_i18n_translations(
        TranslationSize.HUGE, session, pagination.page, pagination.count
    )


@small_i18n_router.get(
    "/{key1}/{key2}/{language_code}",
    response_model=TranslationResponseSchema,
)
@limiter.limit(limit_minute(10))
async def get_small_translation(
    request: Request,
    translation: TranslationGetSchemaDep,
    session: SessionDep,
):
    return await _get_i18n_translation(
        TranslationSize.SMALL,
        translation.key1,
        translation.key2,
        translation.language_code,
        session,
    )


@medium_i18n_router.get(
    "/{key1}/{key2}/{language_code}",
    response_model=TranslationResponseSchema,
)
@limiter.limit(limit_minute(10))
async def get_medium_translation(
    request: Request,
    translation: TranslationGetSchemaDep,
    session: SessionDep,
):
    return await _get_i18n_translation(
        TranslationSize.MEDIUM,
        translation.key1,
        translation.key2,
        translation.language_code,
        session,
    )


@large_i18n_router.get(
    "/{key1}/{key2}/{language_code}",
    response_model=TranslationResponseSchema,
)
@limiter.limit(limit_minute(10))
async def get_large_translation(
    request: Request,
    translation: TranslationGetSchemaDep,
    session: SessionDep,
):
    return await _get_i18n_translation(
        TranslationSize.LARGE,
        translation.key1,
        translation.key2,
        translation.language_code,
        session,
    )


@huge_i18n_router.get(
    "/{key1}/{key2}/{language_code}",
    response_model=TranslationResponseSchema,
)
@limiter.limit(limit_minute(10))
async def get_huge_translation(
    request: Request,
    translation: TranslationGetSchemaDep,
    session: SessionDep,
):
    return await _get_i18n_translation(
        TranslationSize.HUGE,
        translation.key1,
        translation.key2,
        translation.language_code,
        session,
    )


@small_i18n_router.post("/", status_code=201, response_model=TranslationCreateResponseSchema)
@limiter.limit(limit_minute(5))
async def create_small_translation(
    request: Request,
    translation: TranslationCreateSchemaDep,
    session: SessionDep,
):
    return await _create_i18n_translation(translation, TranslationSize.SMALL, session)


@medium_i18n_router.post("/", status_code=201, response_model=TranslationCreateResponseSchema)
@limiter.limit(limit_minute(5))
async def create_medium_translation(
    request: Request,
    translation: TranslationCreateSchemaDep,
    session: SessionDep,
):
    return await _create_i18n_translation(translation, TranslationSize.MEDIUM, session)


@large_i18n_router.post("/", status_code=201, response_model=TranslationCreateResponseSchema)
@limiter.limit(limit_minute(5))
async def create_large_translation(
    request: Request,
    translation: TranslationCreateSchemaDep,
    session: SessionDep,
):
    return await _create_i18n_translation(translation, TranslationSize.LARGE, session)


@huge_i18n_router.post("/", status_code=201, response_model=TranslationCreateResponseSchema)
@limiter.limit(limit_minute(5))
async def create_huge_translation(
    request: Request,
    translation: TranslationCreateSchemaDep,
    session: SessionDep,
):
    return await _create_i18n_translation(translation, TranslationSize.HUGE, session)


@small_i18n_router.delete("/{id}", status_code=204)
@limiter.limit(limit_minute(5))
async def delete_small_translation(request: Request, id: int, session: SessionDep):
    await _delete_i18n_translation(TranslationSize.SMALL, id, session)


@medium_i18n_router.delete("/{id}", status_code=204)
@limiter.limit(limit_minute(5))
async def delete_medium_translation(request: Request, id: int, session: SessionDep):
    await _delete_i18n_translation(TranslationSize.MEDIUM, id, session)


@large_i18n_router.delete("/{id}", status_code=204)
@limiter.limit(limit_minute(5))
async def delete_large_translation(request: Request, id: int, session: SessionDep):
    await _delete_i18n_translation(TranslationSize.LARGE, id, session)


@huge_i18n_router.delete("/{id}", status_code=204)
@limiter.limit(limit_minute(5))
async def delete_huge_translation(request: Request, id: int, session: SessionDep):
    await _delete_i18n_translation(TranslationSize.HUGE, id, session)


i18n_router.include_router(small_i18n_router)
i18n_router.include_router(medium_i18n_router)
i18n_router.include_router(large_i18n_router)
i18n_router.include_router(huge_i18n_router)
