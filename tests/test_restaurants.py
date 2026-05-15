"""Тесты ресторанов."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.restaurant import Restaurant
from app.models.user import User


class TestGetRestaurants:
    """Тесты получения списка ресторанов."""

    async def test_get_empty_list(self, client: AsyncClient):
        response = await client.get("/api/v1/restaurants")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_get_list_with_restaurant(
        self, client: AsyncClient, test_restaurant: Restaurant
    ):
        response = await client.get("/api/v1/restaurants")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Тестовый ресторан"

    async def test_get_list_pagination(self, client: AsyncClient, test_restaurant: Restaurant):
        response = await client.get("/api/v1/restaurants?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10

    async def test_filter_by_cuisine(
        self, client: AsyncClient, test_restaurant: Restaurant
    ):
        response = await client.get("/api/v1/restaurants?cuisine=Итальянская")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    async def test_filter_by_cuisine_no_match(
        self, client: AsyncClient, test_restaurant: Restaurant
    ):
        response = await client.get("/api/v1/restaurants?cuisine=Японская")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


class TestGetRestaurant:
    """Тесты получения ресторана по ID."""

    async def test_get_by_id(self, client: AsyncClient, test_restaurant: Restaurant):
        response = await client.get(f"/api/v1/restaurants/{test_restaurant.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Тестовый ресторан"
        assert data["latitude"] == 55.7558

    async def test_get_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/restaurants/{fake_id}")
        assert response.status_code == 404


class TestCreateRestaurant:
    """Тесты создания ресторана."""

    async def test_create_success(self, client: AsyncClient, admin_token: str):
        response = await client.post(
            "/api/v1/restaurants",
            json={
                "name": "Новый ресторан",
                "address": "ул. Новая, д. 5",
                "cuisine_type": "Французская",
                "latitude": 55.75,
                "longitude": 37.62,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Новый ресторан"
        assert data["cuisine_type"] == "Французская"

    async def test_create_unauthorized(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/restaurants",
            json={"name": "Ресторан", "address": "ул. Тест, д. 1"},
        )
        assert response.status_code == 401

    async def test_create_forbidden_for_user(
        self, client: AsyncClient, user_token: str
    ):
        response = await client.post(
            "/api/v1/restaurants",
            json={"name": "Ресторан", "address": "ул. Тест, д. 1"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    async def test_create_invalid_data(self, client: AsyncClient, admin_token: str):
        response = await client.post(
            "/api/v1/restaurants",
            json={"name": "A", "address": "123"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422


class TestUpdateRestaurant:
    """Тесты обновления ресторана."""

    async def test_update_success(
        self, client: AsyncClient, admin_token: str, test_restaurant: Restaurant
    ):
        response = await client.patch(
            f"/api/v1/restaurants/{test_restaurant.id}",
            json={"name": "Обновлённый ресторан"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Обновлённый ресторан"

    async def test_update_not_found(self, client: AsyncClient, admin_token: str):
        fake_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/restaurants/{fake_id}",
            json={"name": "Новое имя"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


class TestDeleteRestaurant:
    """Тесты удаления ресторана."""

    async def test_delete_success(
        self, client: AsyncClient, admin_token: str, test_restaurant: Restaurant
    ):
        response = await client.delete(
            f"/api/v1/restaurants/{test_restaurant.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

    async def test_delete_not_found(self, client: AsyncClient, admin_token: str):
        fake_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/restaurants/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
