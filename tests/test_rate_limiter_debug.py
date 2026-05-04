import pytest
from httpx import AsyncClient
from src.utils.rate_limiter import limiter


@pytest.mark.asyncio
async def test_debug_limiter(client: AsyncClient):
    limiter.enabled = True
    try:
        limiter._storage.reset()  # pylint: disable=protected-access
        res1 = await client.get("/")  # Unprotected root
        print("Root pass 1:", res1.status_code)
        res2 = await client.get("/")  # Unprotected root
        print("Root pass 2:", res2.status_code)

        # Another unprotected endpoint
        res3 = await client.get("/api/v1/i18n/small")
        print("i18n pass 1:", res3.status_code)
        res4 = await client.get("/api/v1/i18n/small")
        print("i18n pass 2:", res4.status_code)
    finally:
        limiter.enabled = False
