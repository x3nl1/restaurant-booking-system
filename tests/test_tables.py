"""Тесты столиков."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.models.booking import Booking, BookingStatus
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.models.user import User


class TestGetAvailableTables:
    """Тесты получения доступных столиков."""

    async def test_get_available(
        self, client: AsyncClient, test_restaurant: Restaurant, test_table: Table
    ):
        future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        response = await client.get(
            "/api/v1/tables/available",
            params={
                "restaurant_id": str(test_restaurant.id),
                "date": future_date,
                "guests": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["number"] == 1

    async def test_get_available_no_capacity(
        self, client: AsyncClient, test_restaurant: Restaurant, test_table: Table
    ):
        future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        response = await client.get(
            "/api/v1/tables/available",
            params={
                "restaurant_id": str(test_restaurant.id),
                "date": future_date,
                "guests": 10,  # Столик на 4 места
            },
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_available_booked(
        self,
        client: AsyncClient,
        test_restaurant: Restaurant,
        test_table: Table,
        test_booking: Booking,
    ):
        # Используем ту же дату, что и у бронирования
        booking_date = test_booking.booking_date.isoformat()
        response = await client.get(
            "/api/v1/tables/available",
            params={
                "restaurant_id": str(test_restaurant.id),
                "date": booking_date,
                "guests": 2,
            },
        )
        assert response.status_code == 200
        assert response.json() == []


class TestFloorPlan:
    """Тесты карты зала."""

    async def test_get_floor_plan(
        self, client: AsyncClient, test_restaurant: Restaurant, test_table: Table
    ):
        response = await client.get(
            f"/api/v1/tables/floor-plan/{test_restaurant.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["restaurant_name"] == "Тестовый ресторан"
        assert data["width"] == 800
        assert data["height"] == 600
        assert len(data["tables"]) == 1
        assert data["tables"][0]["position_x"] == 100
        assert data["tables"][0]["position_y"] == 200

    async def test_get_floor_plan_with_date(
        self,
        client: AsyncClient,
        test_restaurant: Restaurant,
        test_table: Table,
        test_booking: Booking,
    ):
        booking_date = test_booking.booking_date.isoformat()
        response = await client.get(
            f"/api/v1/tables/floor-plan/{test_restaurant.id}",
            params={"date": booking_date},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tables"][0]["is_available"] is False

    async def test_get_floor_plan_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/tables/floor-plan/{fake_id}")
        assert response.status_code == 404


class TestCreateTable:
    """Тесты создания столика."""

    async def test_create_success(
        self, client: AsyncClient, admin_token: str, test_restaurant: Restaurant
    ):
        response = await client.post(
            "/api/v1/tables",
            json={
                "restaurant_id": str(test_restaurant.id),
                "number": 5,
                "capacity": 6,
                "position_x": 300,
                "position_y": 400,
                "shape": "square",
                "zone": "vip",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["number"] == 5
        assert data["capacity"] == 6
        assert data["zone"] == "vip"

    async def test_create_restaurant_not_found(
        self, client: AsyncClient, admin_token: str
    ):
        fake_id = uuid.uuid4()
        response = await client.post(
            "/api/v1/tables",
            json={
                "restaurant_id": str(fake_id),
                "number": 1,
                "capacity": 4,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    async def test_create_forbidden_for_user(
        self, client: AsyncClient, user_token: str, test_restaurant: Restaurant
    ):
        response = await client.post(
            "/api/v1/tables",
            json={
                "restaurant_id": str(test_restaurant.id),
                "number": 1,
                "capacity": 4,
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403


class TestUpdateTable:
    """Тесты обновления столика."""

    async def test_update_success(
        self, client: AsyncClient, admin_token: str, test_table: Table
    ):
        response = await client.patch(
            f"/api/v1/tables/{test_table.id}",
            json={"capacity": 8, "zone": "vip"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["capacity"] == 8
        assert data["zone"] == "vip"

    async def test_update_not_found(self, client: AsyncClient, admin_token: str):
        fake_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/tables/{fake_id}",
            json={"capacity": 8},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


class TestDeleteTable:
    """Тесты удаления столика."""

    async def test_delete_success(
        self, client: AsyncClient, admin_token: str, test_table: Table
    ):
        response = await client.delete(
            f"/api/v1/tables/{test_table.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

    async def test_delete_not_found(self, client: AsyncClient, admin_token: str):
        fake_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/tables/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
