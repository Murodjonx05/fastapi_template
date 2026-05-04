import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestI18nAPI:
    """Integration tests for i18n API variants with mandatory authentication."""

    async def _get_auth_headers(
        self, client: AsyncClient, db_session=None
    ) -> dict[str, str]:
        # Signup and login to get a token for tests
        username, password = "test_i18n_user", "StrongSecure123!"
        await client.post(
            "/api/v1/users/",
            json={
                "username": username,
                "password": password,
                "password_confirm": password,
            },
        )
        auth_resp = await client.post(
            "/api/v1/users/auth", json={"username": username, "password": password}
        )
        token = auth_resp.json()["access_token"]

        # Give this user admin role for i18n operations
        if db_session is not None:
            from src.models.rbac import Role
            from src.models.i18n import TranslationSmall
            from src.models.user import User
            from sqlalchemy import select

            # Create translation for admin role title/description
            title_translation = TranslationSmall(
                key="admin_role_title", language_code="en", values="Administrator"
            )
            db_session.add(title_translation)
            await db_session.flush()
            desc_translation = TranslationSmall(
                key="admin_role_desc",
                language_code="en",
                values="System administrator with full access",
            )
            db_session.add(desc_translation)
            await db_session.flush()
            # Create admin role if it doesn't exist
            role = await db_session.scalar(select(Role).where(Role.name == "admin"))
            if role is None:
                role = Role(
                    name="admin",
                    title_id=title_translation.id,
                    description_id=desc_translation.id,
                )
                db_session.add(role)
                await db_session.flush()
            # Assign role to user
            user = await db_session.scalar(
                select(User).where(User.username == username)
            )
            if user:
                user.role = role
                await db_session.flush()

        return {"Authorization": f"Bearer {token}"}

    async def test_small_variant_lifecycle(self, client: AsyncClient, db_session):
        headers = await self._get_auth_headers(client, db_session)

        # 1. Create translation
        payload = {
            "key": "dashboard.welcome",
            "language_code": "en",
            "value": "Welcome to the dashboard!",
        }
        create_response = await client.post(
            "/api/v1/i18n/small/", json=payload, headers=headers
        )
        assert create_response.status_code == 201

        # 2. Get translation (item)
        get_response = await client.get(
            "/api/v1/i18n/small/item",
            params={"key": "dashboard.welcome", "lang": "en"},
            headers=headers,
        )
        assert get_response.status_code == 200
        assert get_response.json()["value"] == "Welcome to the dashboard!"

        # 3. List translations
        list_response = await client.get("/api/v1/i18n/small/", headers=headers)
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 1

    async def test_large_variant_content_limit(self, client: AsyncClient, db_session):
        headers = await self._get_auth_headers(client, db_session)
        payload = {
            "key": "app.legal",
            "language_code": "en",
            "value": "Lorem Ipsum " * 1000,
        }
        response = await client.post(
            "/api/v1/i18n/large/", json=payload, headers=headers
        )
        assert response.status_code == 201

    async def test_nonexistent_translation_fails(self, client: AsyncClient, db_session):
        headers = await self._get_auth_headers(client, db_session)
        response = await client.get(
            "/api/v1/i18n/small/item",
            params={"key": "not.exist", "lang": "zz"},
            headers=headers,
        )
        assert response.status_code == 404

    async def test_duplicate_translation_fails(self, client: AsyncClient, db_session):
        headers = await self._get_auth_headers(client, db_session)
        payload = {"key": "dup.test", "language_code": "ru", "value": "Value 1"}
        await client.post("/api/v1/i18n/small/", json=payload, headers=headers)

        response = await client.post(
            "/api/v1/i18n/small/", json=payload, headers=headers
        )
        assert response.status_code == 409
