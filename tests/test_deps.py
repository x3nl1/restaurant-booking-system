"""Тесты зависимостей (deps)."""

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.user import User


class TestAuthDependency:
    """Тесты JWT-аутентификации через зависимости."""

    async def test_no_token(self, client: AsyncClient):
        response = await client.get("/api/v1/bookings/my")
        assert response.status_code == 401

    async def test_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/bookings/my",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_malformed_header(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/bookings/my",
            headers={"Authorization": "NotBearer token"},
        )
        assert response.status_code == 401

    async def test_token_with_nonexistent_user(self, client: AsyncClient):
        token = create_access_token({"sub": str(uuid.uuid4())})
        response = await client.get(
            "/api/v1/bookings/my",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_token_without_sub(self, client: AsyncClient):
        token = create_access_token({"data": "no-sub"})
        response = await client.get(
            "/api/v1/bookings/my",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_token_with_invalid_uuid(self, client: AsyncClient):
        token = create_access_token({"sub": "not-a-uuid"})
        response = await client.get(
            "/api/v1/bookings/my",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_inactive_user_token(
        self, client: AsyncClient, session, test_user: User
    ):
        test_user.is_active = False
        session.add(test_user)
        await session.commit()

        token = create_access_token({"sub": str(test_user.id)})
        response = await client.get(
            "/api/v1/bookings/my",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_admin_required(self, client: AsyncClient, user_token: str):
        response = await client.post(
            "/api/v1/restaurants",
            json={"name": "Test", "address": "Test address 123"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403
