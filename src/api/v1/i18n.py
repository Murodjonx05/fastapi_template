from fastapi import APIRouter, status
from src.crud.i18n import create_translation, delete_translation, get_translation, get_translations
from src.database import SessionDep
from src.schemas.base import PaginationSchemaDep
from src.schemas.i18n import (
    TranslationKey,
    LanguageCode,
    TranslationCreateSchema,
    TranslationCreateResponseSchema,
    TranslationResponseSchema,
    TranslationSize,
)
from src.utils.logging import get_logger

logger = get_logger("i18n_api")
i18n_router = APIRouter()

def register_size_routes(router: APIRouter, size: TranslationSize):
    """Factory helper to register CRUD routes for a specific translation size."""
    
    @router.get("/", response_model=list[TranslationResponseSchema])
    async def list_translations(session: SessionDep, pagination: PaginationSchemaDep):
        rows = await get_translations(size, session, page=pagination.page, count=pagination.count)
        return rows

    @router.post("/", status_code=status.HTTP_201_CREATED, response_model=TranslationCreateResponseSchema)
    async def create(body: TranslationCreateSchema, session: SessionDep):
        created = await create_translation(body, size, session)
        return TranslationCreateResponseSchema(
            message="Created successfully",
            translation=TranslationResponseSchema.model_validate(created)
        )

    @router.get("/item", response_model=TranslationResponseSchema)
    async def get_one(key: TranslationKey, lang: LanguageCode, session: SessionDep):
        return await get_translation(key, lang, size, session)

    @router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_one(id: int, session: SessionDep):
        await delete_translation(id, size, session)

# Unified registration of i18n variants
for size in TranslationSize:
    sub_router = APIRouter(prefix=f"/{size}", tags=[f"i18n-{size}"])
    register_size_routes(sub_router, size)
    i18n_router.include_router(sub_router)
