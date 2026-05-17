"""Настройка подключения к базе данных."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Параметры пула только для PostgreSQL (SQLite не поддерживает)
engine_kwargs: dict = {"echo": settings.DEBUG}
if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs.update(pool_size=20, max_overflow=10)

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Генератор асинхронных сессий для DI."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
