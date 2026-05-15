"""Скрипт заполнения БД тестовыми данными.

Использование:
    python -m scripts.seed

Требует запущенной БД (docker-compose up db).
"""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.booking import Booking, BookingStatus
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.models.user import User

RESTAURANTS_DATA = [
    {
        "name": "Итальянский дворик",
        "description": "Уютный ресторан итальянской кухни в центре города",
        "address": "ул. Пушкина, д. 15",
        "phone": "+7 (495) 123-45-67",
        "email": "info@italian-dvorik.ru",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "working_hours": "11:00-23:00",
        "average_check": 2500,
        "cuisine_type": "Итальянская",
        "floor_plan_width": 900,
        "floor_plan_height": 700,
    },
    {
        "name": "Сакура",
        "description": "Японский ресторан с панорамным видом",
        "address": "пр. Мира, д. 42",
        "phone": "+7 (495) 987-65-43",
        "email": "hello@sakura-rest.ru",
        "latitude": 55.7720,
        "longitude": 37.6316,
        "working_hours": "12:00-00:00",
        "average_check": 3500,
        "cuisine_type": "Японская",
        "floor_plan_width": 1000,
        "floor_plan_height": 600,
    },
    {
        "name": "Бургер Хаус",
        "description": "Лучшие бургеры в городе, крафтовое пиво",
        "address": "ул. Арбат, д. 7",
        "phone": "+7 (495) 555-12-34",
        "email": "order@burgerhouse.ru",
        "latitude": 55.7520,
        "longitude": 37.5930,
        "working_hours": "10:00-02:00",
        "average_check": 1200,
        "cuisine_type": "Американская",
        "floor_plan_width": 800,
        "floor_plan_height": 500,
    },
]

TABLES_CONFIG = [
    # (number, capacity, x, y, shape, zone)
    (1, 2, 100, 100, "round", "main"),
    (2, 2, 250, 100, "round", "main"),
    (3, 4, 400, 100, "square", "main"),
    (4, 4, 100, 250, "square", "main"),
    (5, 6, 250, 250, "rectangle", "main"),
    (6, 4, 400, 250, "round", "terrace"),
    (7, 2, 550, 100, "round", "terrace"),
    (8, 8, 550, 250, "rectangle", "vip"),
    (9, 4, 100, 400, "square", "bar"),
    (10, 2, 250, 400, "round", "bar"),
]


async def seed():
    """Заполнение БД тестовыми данными."""
    engine = create_async_engine(settings.DATABASE_URL)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        # Создаём администратора
        admin = User(
            id=uuid.uuid4(),
            email="admin@restaurant-booking.ru",
            hashed_password=hash_password("admin123"),
            full_name="Администратор Системы",
            phone="+7 (900) 000-00-01",
            is_active=True,
            is_admin=True,
        )
        session.add(admin)

        # Создаём тестового пользователя
        user = User(
            id=uuid.uuid4(),
            email="user@example.com",
            hashed_password=hash_password("user123"),
            full_name="Иван Петров",
            phone="+7 (900) 123-45-67",
            is_active=True,
            is_admin=False,
        )
        session.add(user)

        # Создаём рестораны и столики
        for rest_data in RESTAURANTS_DATA:
            restaurant = Restaurant(id=uuid.uuid4(), **rest_data)
            session.add(restaurant)
            await session.flush()

            for num, cap, x, y, shape, zone in TABLES_CONFIG:
                table = Table(
                    id=uuid.uuid4(),
                    restaurant_id=restaurant.id,
                    number=num,
                    capacity=cap,
                    position_x=x,
                    position_y=y,
                    shape=shape,
                    zone=zone,
                )
                session.add(table)

        await session.commit()
        print("✅ Seed data created successfully!")
        print(f"   Admin: admin@restaurant-booking.ru / admin123")
        print(f"   User:  user@example.com / user123")
        print(f"   Restaurants: {len(RESTAURANTS_DATA)}")
        print(f"   Tables per restaurant: {len(TABLES_CONFIG)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
