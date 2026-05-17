"""Сервис уведомлений (email)."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис отправки email-уведомлений."""

    @staticmethod
    async def send_booking_confirmation(
        to_email: str, guest_name: str, restaurant_name: str, booking_date: str
    ) -> bool:
        """Отправка уведомления о подтверждении бронирования."""
        subject = f"Бронирование подтверждено — {restaurant_name}"
        body = (
            f"Здравствуйте, {guest_name}!\n\n"
            f"Ваше бронирование в ресторане «{restaurant_name}» подтверждено.\n"
            f"Дата и время: {booking_date}\n\n"
            f"Ждём вас!\n"
            f"С уважением, {settings.APP_NAME}"
        )
        return await NotificationService._send_email(to_email, subject, body)

    @staticmethod
    async def send_booking_cancellation(
        to_email: str, guest_name: str, restaurant_name: str, booking_date: str
    ) -> bool:
        """Отправка уведомления об отмене бронирования."""
        subject = f"Бронирование отменено — {restaurant_name}"
        body = (
            f"Здравствуйте, {guest_name}!\n\n"
            f"Ваше бронирование в ресторане «{restaurant_name}» "
            f"на {booking_date} было отменено.\n\n"
            f"С уважением, {settings.APP_NAME}"
        )
        return await NotificationService._send_email(to_email, subject, body)

    @staticmethod
    async def _send_email(to_email: str, subject: str, body: str) -> bool:
        """Отправка email через SMTP."""
        try:
            message = MIMEMultipart()
            message["From"] = settings.SMTP_FROM
            message["To"] = to_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain", "utf-8"))

            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER or None,
                password=settings.SMTP_PASSWORD or None,
            )
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception:
            logger.error("Failed to send email to %s", to_email, exc_info=True)
            return False
