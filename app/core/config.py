"""Конфигурация приложения через переменные окружения."""

import logging
import secrets

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_DEFAULT_SECRET = secrets.token_urlsafe(32)


class Settings(BaseSettings):
    """Настройки приложения."""

    APP_NAME: str = "Restaurant Booking System"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/restaurant_booking"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = _DEFAULT_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@restaurant-booking.local"

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()

# Предупреждение если SECRET_KEY не задан явно
if settings.SECRET_KEY == _DEFAULT_SECRET:
    logger.warning(
        "SECRET_KEY не задан через переменные окружения. "
        "Используется случайный ключ — JWT-токены будут инвалидированы при перезапуске."
    )
