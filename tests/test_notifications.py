"""Тесты сервиса уведомлений."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.notification_service import NotificationService


class TestNotificationService:
    """Тесты отправки уведомлений."""

    @patch("app.services.notification_service.aiosmtplib.send", new_callable=AsyncMock)
    async def test_send_booking_confirmation(self, mock_send):
        mock_send.return_value = None
        result = await NotificationService.send_booking_confirmation(
            to_email="user@example.com",
            guest_name="Иван",
            restaurant_name="Ресторан Тест",
            booking_date="25.12.2025 19:00",
        )
        assert result is True
        mock_send.assert_called_once()

    @patch("app.services.notification_service.aiosmtplib.send", new_callable=AsyncMock)
    async def test_send_booking_cancellation(self, mock_send):
        mock_send.return_value = None
        result = await NotificationService.send_booking_cancellation(
            to_email="user@example.com",
            guest_name="Иван",
            restaurant_name="Ресторан Тест",
            booking_date="25.12.2025 19:00",
        )
        assert result is True
        mock_send.assert_called_once()

    @patch("app.services.notification_service.aiosmtplib.send", new_callable=AsyncMock)
    async def test_send_email_failure(self, mock_send):
        mock_send.side_effect = Exception("SMTP error")
        result = await NotificationService.send_booking_confirmation(
            to_email="user@example.com",
            guest_name="Иван",
            restaurant_name="Ресторан Тест",
            booking_date="25.12.2025 19:00",
        )
        assert result is False

    @patch("app.services.notification_service.aiosmtplib.send", new_callable=AsyncMock)
    async def test_send_cancellation_failure(self, mock_send):
        mock_send.side_effect = Exception("Connection refused")
        result = await NotificationService.send_booking_cancellation(
            to_email="user@example.com",
            guest_name="Иван",
            restaurant_name="Ресторан Тест",
            booking_date="25.12.2025 19:00",
        )
        assert result is False
