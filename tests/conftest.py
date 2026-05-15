"""Фикстуры для тестов."""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.booking import Booking, BookingStatus
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.models.user import User

# SQLite для тестов (in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    """Создание и удаление таблиц для каждого теста."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Тестовая сессия БД."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент для тестирования API."""

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Тестовый пользователь."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("password123"),
        full_name="Test User",
        phone="+79001234567",
        is_active=True,
        is_admin=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def admin_user(session: AsyncSession) -> User:
    """Тестовый администратор."""
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        full_name="Admin User",
        phone="+79009876543",
        is_active=True,
        is_admin=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: User) -> str:
    """JWT-токен обычного пользователя."""
    return create_access_token({"sub": str(test_user.id)})


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """JWT-токен администратора."""
    return create_access_token({"sub": str(admin_user.id)})


@pytest.fixture
async def test_restaurant(session: AsyncSession) -> Restaurant:
    """Тестовый ресторан."""
    restaurant = Restaurant(
        id=uuid.uuid4(),
        name="Тестовый ресторан",
        description="Описание тестового ресторана",
        address="ул. Тестовая, д. 1",
        phone="+79001111111",
        email="rest@example.com",
        latitude=55.7558,
        longitude=37.6173,
        working_hours="10:00-23:00",
        average_check=1500,
        cuisine_type="Итальянская",
        floor_plan_width=800,
        floor_plan_height=600,
    )
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)
    return restaurant


@pytest.fixture
async def test_table(session: AsyncSession, test_restaurant: Restaurant) -> Table:
    """Тестовый столик."""
    table = Table(
        id=uuid.uuid4(),
        restaurant_id=test_restaurant.id,
        number=1,
        capacity=4,
        position_x=100,
        position_y=200,
        shape="round",
        zone="main",
    )
    session.add(table)
    await session.commit()
    await session.refresh(table)
    return table


@pytest.fixture
async def test_booking(
    session: AsyncSession, test_user: User, test_table: Table
) -> Booking:
    """Тестовое бронирование."""
    booking = Booking(
        id=uuid.uuid4(),
        user_id=test_user.id,
        table_id=test_table.id,
        booking_date=datetime.now(timezone.utc) + timedelta(days=1),
        duration_minutes=120,
        guests_count=2,
        status=BookingStatus.PENDING,
        comment="Тестовое бронирование",
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking
