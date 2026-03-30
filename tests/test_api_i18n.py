import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestI18nAPI:
    """Integration tests for i18n API variants with mandatory authentication."""

    async def _get_auth_headers(self, client: AsyncClient) -> dict[str, str]:
        # Signup and login to get a token for tests
        username, password = "test_i18n_user", "StrongSecure123!"
        await client.post("/api/v1/users/", json={"username": username, "password": password, "password_confirm": password})
        auth_resp = await client.post("/api/v1/users/auth", json={"username": username, "password": password})
        token = auth_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_small_variant_lifecycle(self, client: AsyncClient):
        headers = await self._get_auth_headers(client)

        # 1. Create translation
        payload = {"key": "dashboard.welcome", "language_code": "en", "value": "Welcome to the dashboard!"}
        create_response = await client.post("/api/v1/i18n/small/", json=payload, headers=headers)
        assert create_response.status_code == 201

        # 2. Get translation (item)
        get_response = await client.get("/api/v1/i18n/small/item", params={"key": "dashboard.welcome", "lang": "en"}, headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["value"] == "Welcome to the dashboard!"

        # 3. List translations
        list_response = await client.get("/api/v1/i18n/small/", headers=headers)
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 1

    async def test_large_variant_content_limit(self, client: AsyncClient):
        headers = await self._get_auth_headers(client)
        payload = {"key": "app.legal", "language_code": "en", "value": "Lorem Ipsum " * 1000}
        response = await client.post("/api/v1/i18n/large/", json=payload, headers=headers)
        assert response.status_code == 201

    async def test_nonexistent_translation_fails(self, client: AsyncClient):
        headers = await self._get_auth_headers(client)
        response = await client.get("/api/v1/i18n/small/item", params={"key": "not.exist", "lang": "zz"}, headers=headers)
        assert response.status_code == 404

    async def test_duplicate_translation_fails(self, client: AsyncClient):
        headers = await self._get_auth_headers(client)
        payload = {"key": "dup.test", "language_code": "ru", "value": "Value 1"}
        await client.post("/api/v1/i18n/small/", json=payload, headers=headers)

        response = await client.post("/api/v1/i18n/small/", json=payload, headers=headers)
        assert response.status_code == 409
