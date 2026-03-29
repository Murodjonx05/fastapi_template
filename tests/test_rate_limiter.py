import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestRateLimiter:
    """Tests for the rate limiting logic and its integration with FastAPI."""

    async def test_root_rate_limit(self, client: AsyncClient):
        # The root endpoint should have a rate limit (we set it to 5/minute)
        # We'll hit it 6 times and expect a 429
        for i in range(5):
            response = await client.get("/api/")
            assert response.status_code == 200

        # The 6th attempt should be blocked
        response = await client.get("/api/")
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
        assert response.json()["type"] == "rate_limit_error"
