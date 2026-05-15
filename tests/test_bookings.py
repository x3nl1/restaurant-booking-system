"""Тесты бронирований."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.booking import Booking, BookingStatus
from app.models.table import Table
from app.models.user import User


class TestCreateBooking:
    """Тесты создания бронирования."""

    async def test_create_success(
        self, client: AsyncClient, user_token: str, test_table: Table
    ):
        future_date = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        response = await client.post(
            "/api/v1/bookings",
            json={
                "table_id": str(test_table.id),
                "booking_date": future_date,
                "duration_minutes": 90,
                "guests_count": 2,
                "comment": "Ужин на двоих",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["guests_count"] == 2
        assert data["status"] == "pending"
        assert data["comment"] == "Ужин на двоих"

    async def test_create_table_not_found(self, client: AsyncClient, user_token: str):
        fake_id = uuid.uuid4()
        future_date = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        response = await client.post(
            "/api/v1/bookings",
            json={
                "table_id": str(fake_id),
                "booking_date": future_date,
                "guests_count": 2,
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404

    async def test_create_too_many_guests(
        self, client: AsyncClient, user_token: str, test_table: Table
    ):
        future_date = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        response = await client.post(
            "/api/v1/bookings",
            json={
                "table_id": str(test_table.id),
                "booking_date": future_date,
                "guests_count": 10,  # Столик на 4
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400

    async def test_create_past_date(
        self, client: AsyncClient, user_token: str, test_table: Table
    ):
        past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        response = await client.post(
            "/api/v1/bookings",
            json={
                "table_id": str(test_table.id),
                "booking_date": past_date,
                "guests_count": 2,
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400

    async def test_create_overlap(
        self,
        client: AsyncClient,
        user_token: str,
        test_table: Table,
        test_booking: Booking,
    ):
        # Пытаемся забронировать на то же время
        response = await client.post(
            "/api/v1/bookings",
            json={
                "table_id": str(test_table.id),
                "booking_date": test_booking.booking_date.isoformat(),
                "guests_count": 2,
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400

    async def test_create_unauthorized(self, client: AsyncClient, test_table: Table):
        future_date = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        response = await client.post(
            "/api/v1/bookings",
            json={
                "table_id": str(test_table.id),
                "booking_date": future_date,
                "guests_count": 2,
            },
        )
        assert response.status_code == 401


class TestGetMyBookings:
    """Тесты получения бронирований пользователя."""

    async def test_get_my_bookings(
        self, client: AsyncClient, user_token: str, test_booking: Booking
    ):
        response = await client.get(
            "/api/v1/bookings/my",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == str(test_booking.id)

    async def test_get_my_bookings_empty(
        self, client: AsyncClient, admin_token: str
    ):
        response = await client.get(
            "/api/v1/bookings/my",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


class TestCancelBooking:
    """Тесты отмены бронирования."""

    @patch("app.api.v1.bookings.NotificationService.send_booking_cancellation", new_callable=AsyncMock)
    async def test_cancel_success(
        self, mock_notify, client: AsyncClient, user_token: str, test_booking: Booking
    ):
        mock_notify.return_value = True
        response = await client.patch(
            f"/api/v1/bookings/{test_booking.id}/cancel",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    async def test_cancel_not_owner(
        self, client: AsyncClient, admin_token: str, test_booking: Booking
    ):
        response = await client.patch(
            f"/api/v1/bookings/{test_booking.id}/cancel",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 403

    async def test_cancel_not_found(self, client: AsyncClient, user_token: str):
        fake_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/bookings/{fake_id}/cancel",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 404

    @patch("app.api.v1.bookings.NotificationService.send_booking_cancellation", new_callable=AsyncMock)
    async def test_cancel_already_cancelled(
        self, mock_notify, client: AsyncClient, user_token: str, test_booking: Booking, session
    ):
        mock_notify.return_value = True
        test_booking.status = BookingStatus.CANCELLED
        session.add(test_booking)
        await session.commit()

        response = await client.patch(
            f"/api/v1/bookings/{test_booking.id}/cancel",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400


class TestConfirmBooking:
    """Тесты подтверждения бронирования."""

    @patch("app.api.v1.bookings.NotificationService.send_booking_confirmation", new_callable=AsyncMock)
    async def test_confirm_success(
        self, mock_notify, client: AsyncClient, admin_token: str, test_booking: Booking
    ):
        mock_notify.return_value = True
        response = await client.patch(
            f"/api/v1/bookings/{test_booking.id}/confirm",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    async def test_confirm_forbidden_for_user(
        self, client: AsyncClient, user_token: str, test_booking: Booking
    ):
        response = await client.patch(
            f"/api/v1/bookings/{test_booking.id}/confirm",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    @patch("app.api.v1.bookings.NotificationService.send_booking_confirmation", new_callable=AsyncMock)
    async def test_confirm_not_pending(
        self, mock_notify, client: AsyncClient, admin_token: str, test_booking: Booking, session
    ):
        mock_notify.return_value = True
        test_booking.status = BookingStatus.CONFIRMED
        session.add(test_booking)
        await session.commit()

        response = await client.patch(
            f"/api/v1/bookings/{test_booking.id}/confirm",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
