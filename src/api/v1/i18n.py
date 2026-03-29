from fastapi import APIRouter, HTTPException, Request, status
from src.core.constants import HUGE_KB, LARGE_KB, MEDIUM_CHARS, SMALL_CHARS
from src.crud.i18n import create_translation, delete_translation, get_translation, get_translations
from src.database import SessionDep
from src.schemas.base import PaginationSchemaDep
from src.schemas.i18n import (
    I18nError,
    TranslationAlreadyExistsError,
    TranslationCreateSchema,
    TranslationCreateResponseSchema,
    TranslationNotFoundError,
    TranslationResponseSchema,
    TranslationSize,
    TranslationValidationError,
)
from src.utils.logging import get_logger

logger = get_logger("i18n_api")
i18n_router = APIRouter()

def handle_i18n_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TranslationValidationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, TranslationAlreadyExistsError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, TranslationNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

def register_size_routes(router: APIRouter, size: TranslationSize):
    @router.get("/", response_model=list[TranslationResponseSchema])
    async def list_translations(session: SessionDep, pagination: PaginationSchemaDep):
        rows = await get_translations(size, session, page=pagination.page, count=pagination.count)
        return [TranslationResponseSchema.model_validate(r) for r in rows]

    @router.post("/", status_code=status.HTTP_201_CREATED, response_model=TranslationCreateResponseSchema)
    async def create(body: TranslationCreateSchema, session: SessionDep):
        try:
            created = await create_translation(body, size, session)
            return TranslationCreateResponseSchema(
                message="Created successfully",
                translation=TranslationResponseSchema.model_validate(created)
            )
        except I18nError as exc:
            raise handle_i18n_error(exc)

    @router.get("/item", response_model=TranslationResponseSchema)
    async def get_one(key: str, lang: str, session: SessionDep):
        try:
            row = await get_translation(key, lang, size, session)
            return TranslationResponseSchema.model_validate(row)
        except I18nError as exc:
            raise handle_i18n_error(exc)

    @router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_one(id: int, session: SessionDep):
        try:
            await delete_translation(id, size, session)
        except I18nError as exc:
            raise handle_i18n_error(exc)

for path, size in [
    ("/small", TranslationSize.SMALL),
    ("/medium", TranslationSize.MEDIUM),
    ("/large", TranslationSize.LARGE),
    ("/huge", TranslationSize.HUGE),
]:
    sub_router = APIRouter(prefix=path, tags=[f"i18n-{size}"])
    register_size_routes(sub_router, size)
    i18n_router.include_router(sub_router)
