import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestRateLimiter:
    """Tests for the rate limiting logic and its integration with FastAPI."""

    async def test_global_rate_limit(self, client: AsyncClient):
        from src.utils.rate_limiter import limiter
        
        # Manually enable the limiter for this specific test
        limiter.enabled = True
        try:
            limiter._storage.reset()
            # `/api/` has an explicit `5/minute` decorator, which is stricter
            # than the global default limit. The first five requests pass, the
            # sixth immediate request is throttled.
            for _ in range(5):
                response = await client.get("/api/")
                assert response.status_code == 200

            blocked = await client.get("/api/")
            assert blocked.status_code == 429
            assert "Rate limit exceeded" in blocked.json()["detail"]
            assert blocked.json()["type"] == "rate_limit_error"
        finally:
            limiter.enabled = False
