import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestI18nAPI:
    """Integration tests for i18n API variants (small, medium, large, huge)."""

    async def test_small_variant_lifecycle(self, client: AsyncClient):
        # 1. Create translation
        payload = {
            "key": "dashboard.welcome",
            "language_code": "en",
            "value": "Welcome to the dashboard!"
        }
        create_response = await client.post("/api/v1/i18n/small/", json=payload)
        assert create_response.status_code == 201
        assert create_response.json()["translation"]["key"] == "dashboard.welcome"

        # 2. Get translation (item)
        get_response = await client.get(
            "/api/v1/i18n/small/item",
            params={"key": "dashboard.welcome", "lang": "en"}
        )
        assert get_response.status_code == 200
        assert get_response.json()["value"] == "Welcome to the dashboard!"

        # 3. List translations
        list_response = await client.get("/api/v1/i18n/small/")
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 1

    async def test_large_variant_content_limit(self, client: AsyncClient):
        # Test large translation has no practical limit in Text/Text (SQLAlchemy)
        # But we still use standard create route
        payload = {
            "key": "app.legal",
            "language_code": "en",
            "value": "Lorem Ipsum " * 1000  # Large content
        }
        response = await client.post("/api/v1/i18n/large/", json=payload)
        assert response.status_code == 201

    async def test_nonexistent_translation_fails(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/i18n/small/item",
            params={"key": "not.exist", "lang": "zz"}
        )
        assert response.status_code == 404
        assert "TranslationNotFoundError" in response.json()["type"]

    async def test_duplicate_translation_fails(self, client: AsyncClient):
        payload = {
            "key": "dup.test",
            "language_code": "ru",
            "value": "Value 1"
        }
        await client.post("/api/v1/i18n/small/", json=payload)
        
        response = await client.post("/api/v1/i18n/small/", json=payload)
        assert response.status_code == 409
        assert "TranslationAlreadyExistsError" in response.json()["type"]
