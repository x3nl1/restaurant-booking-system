"""Тесты health-check."""

import pytest
from httpx import AsyncClient


class TestHealth:
    """Тесты проверки работоспособности."""

    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data
