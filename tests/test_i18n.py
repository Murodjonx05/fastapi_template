"""Unit tests for i18n CRUD operations and schema validation."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.i18n import (
    create_translation,
    delete_translation,
    get_translation,
    get_translations,
)
from src.schemas.i18n import (
    MAX_VALUE_CHARS,
    TranslationAlreadyExistsError,
    TranslationCreateSchema,
    TranslationDeleteNotFoundError,
    TranslationNotFoundError,
    TranslationSize,
    TranslationValidationError,
    validate_translation_value,
)


# ---------------------------------------------------------------------------
# Schema-level validation (pure, no DB)
# ---------------------------------------------------------------------------


class TestValidateTranslationValue:
    """Tests for the centralised ``validate_translation_value`` function."""

    def test_value_within_limit_passes(self):
        result = validate_translation_value("hello", TranslationSize.SMALL)
        assert result == "hello"

    def test_value_exactly_at_limit_passes(self):
        limit = MAX_VALUE_CHARS[TranslationSize.SMALL]
        value = "x" * limit
        result = validate_translation_value(value, TranslationSize.SMALL)
        assert result == value

    def test_value_exceeding_limit_raises(self):
        limit = MAX_VALUE_CHARS[TranslationSize.SMALL]
        with pytest.raises(TranslationValidationError, match="exceeds maximum length"):
            validate_translation_value("x" * (limit + 1), TranslationSize.SMALL)

    def test_all_sizes_have_limits(self):
        for size in TranslationSize:
            assert size in MAX_VALUE_CHARS, f"Missing limit for {size}"


class TestTranslationCreateSchema:
    """Tests for Pydantic-level validation on TranslationCreateSchema."""

    def test_valid_schema(self):
        schema = TranslationCreateSchema(
            key="home.title", language_code="en", value="Welcome"
        )
        assert schema.key == "home.title"

    def test_key_too_long(self):
        with pytest.raises(Exception):  # Pydantic ValidationError
            TranslationCreateSchema(key="k" * 200, language_code="en", value="ok")

    def test_language_code_too_short(self):
        with pytest.raises(Exception):
            TranslationCreateSchema(key="some.key", language_code="x", value="ok")

    def test_value_empty_after_strip(self):
        with pytest.raises(Exception):
            TranslationCreateSchema(key="some.key", language_code="en", value="   ")


# ---------------------------------------------------------------------------
# CRUD tests (require DB session)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestCreateTranslation:
    async def test_create_and_read_back(self, db_session: AsyncSession):
        schema = TranslationCreateSchema(
            key="greeting", language_code="en", value="Hello"
        )
        created = await create_translation(schema, TranslationSize.SMALL, db_session)

        assert created.key == "greeting"
        assert created.language_code == "en"
        assert created.values == "Hello"

    async def test_duplicate_raises(self, db_session: AsyncSession):
        schema = TranslationCreateSchema(
            key="dup_test", language_code="en", value="First"
        )
        await create_translation(schema, TranslationSize.SMALL, db_session)

        with pytest.raises(TranslationAlreadyExistsError, match="already exists"):
            await create_translation(schema, TranslationSize.SMALL, db_session)

    async def test_value_too_long_raises(self, db_session: AsyncSession):
        limit = MAX_VALUE_CHARS[TranslationSize.SMALL]
        long_value = "x" * (limit + 1)
        schema = TranslationCreateSchema(
            key="long", language_code="en", value=long_value
        )

        with pytest.raises(TranslationValidationError, match="exceeds maximum length"):
            await create_translation(schema, TranslationSize.SMALL, db_session)


@pytest.mark.asyncio
class TestGetTranslation:
    async def test_get_existing(self, db_session: AsyncSession):
        schema = TranslationCreateSchema(
            key="get_test", language_code="ru", value="Привет"
        )
        await create_translation(schema, TranslationSize.SMALL, db_session)

        result = await get_translation(
            "get_test", "ru", TranslationSize.SMALL, db_session
        )
        assert result.values == "Привет"

    async def test_get_nonexistent_raises(self, db_session: AsyncSession):
        with pytest.raises(TranslationNotFoundError, match="not found"):
            await get_translation(
                "nonexistent", "zz", TranslationSize.SMALL, db_session
            )


@pytest.mark.asyncio
class TestGetTranslations:
    async def test_pagination(self, db_session: AsyncSession):
        # Create 5 translations
        for i in range(5):
            schema = TranslationCreateSchema(
                key=f"page_test_{i}", language_code="en", value=f"value_{i}"
            )
            await create_translation(schema, TranslationSize.MEDIUM, db_session)

        page1 = await get_translations(
            TranslationSize.MEDIUM, db_session, page=1, count=3
        )
        assert len(page1) == 3

        page2 = await get_translations(
            TranslationSize.MEDIUM, db_session, page=2, count=3
        )
        assert len(page2) == 2


@pytest.mark.asyncio
class TestDeleteTranslation:
    async def test_delete_existing(self, db_session: AsyncSession):
        schema = TranslationCreateSchema(
            key="del_test", language_code="en", value="temp"
        )
        created = await create_translation(schema, TranslationSize.SMALL, db_session)

        # Should not raise
        await delete_translation(created.id, TranslationSize.SMALL, db_session)

        with pytest.raises(TranslationNotFoundError):
            await get_translation("del_test", "en", TranslationSize.SMALL, db_session)

    async def test_delete_nonexistent_raises(self, db_session: AsyncSession):
        with pytest.raises(TranslationDeleteNotFoundError, match="not found"):
            await delete_translation(999999, TranslationSize.SMALL, db_session)
