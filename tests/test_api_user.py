import pytest
from httpx import AsyncClient
from src.core.security import create_access_token
from src.schemas.user import UserCreateSchema

@pytest.mark.asyncio
class TestUserAPI:
    """Integration tests for User API endpoints."""

    async def test_signup_success(self, client: AsyncClient):
        payload = {
            "username": "new_user_123",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!"
        }
        response = await client.post("/api/v1/users/", json=payload)
        assert response.status_code == 201
        assert "user_uuid" in response.json()

    async def test_signup_duplicate_fails(self, client: AsyncClient):
        payload = {
            "username": "duplicate_user",
            "password": "Password123!",
            "password_confirm": "Password123!"
        }
        # First signup
        await client.post("/api/v1/users/", json=payload)
        # Second signup
        response = await client.post("/api/v1/users/", json=payload)
        assert response.status_code == 409
        assert "UserAlreadyExistsError" in response.json()["type"]

    async def test_auth_and_get_me(self, client: AsyncClient):
        # 1. Signup
        username = "test_auth_user"
        password = "SecurePassword123!"
        await client.post("/api/v1/users/", json={
            "username": username,
            "password": password,
            "password_confirm": password
        })

        # 2. Auth (Login)
        auth_response = await client.post("/api/v1/users/auth", json={
            "username": username,
            "password": password
        })
        assert auth_response.status_code == 200
        token = auth_response.json()["access_token"]
        assert token

        # 3. Get Me
        headers = {"Authorization": f"Bearer {token}"}
        me_response = await client.get("/api/v1/users/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["username"] == username

    async def test_unauthorized_get_me(self, client: AsyncClient):
        response = await client.get("/api/v1/users/me")
        # AuthX returns 401 when subject is not found or token missing
        assert response.status_code == 401
