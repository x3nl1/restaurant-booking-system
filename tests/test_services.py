"""Прямые unit-тесты сервисов."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.models.booking import Booking, BookingStatus
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.models.user import User
from app.schemas.booking import BookingCreate
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate
from app.schemas.table import TableCreate, TableUpdate
from app.schemas.user import UserCreate, UserLogin
from app.services.auth_service import AuthService
from app.services.booking_service import BookingService
from app.services.restaurant_service import RestaurantService
from app.services.table_service import TableService


class TestAuthServiceDirect:
    """Прямые тесты AuthService."""

    async def test_register_success(self, session: AsyncSession):
        service = AuthService(session)
        data = UserCreate(
            email="direct@example.com",
            password="password123",
            full_name="Direct User",
            phone="+79001112233",
        )
        result = await service.register(data)
        assert result.user.email == "direct@example.com"
        assert result.access_token

    async def test_register_duplicate(self, session: AsyncSession, test_user: User):
        service = AuthService(session)
        data = UserCreate(
            email=test_user.email,
            password="password123",
            full_name="Dup User",
        )
        with pytest.raises(ConflictException):
            await service.register(data)

    async def test_login_success(self, session: AsyncSession, test_user: User):
        service = AuthService(session)
        data = UserLogin(email="test@example.com", password="password123")
        result = await service.login(data)
        assert result.user.email == "test@example.com"
        assert result.access_token

    async def test_login_wrong_password(self, session: AsyncSession, test_user: User):
        service = AuthService(session)
        data = UserLogin(email="test@example.com", password="wrong")
        with pytest.raises(UnauthorizedException):
            await service.login(data)

    async def test_login_nonexistent(self, session: AsyncSession):
        service = AuthService(session)
        data = UserLogin(email="nobody@example.com", password="pass")
        with pytest.raises(UnauthorizedException):
            await service.login(data)

    async def test_login_inactive(self, session: AsyncSession, test_user: User):
        test_user.is_active = False
        session.add(test_user)
        await session.commit()

        service = AuthService(session)
        data = UserLogin(email="test@example.com", password="password123")
        with pytest.raises(UnauthorizedException):
            await service.login(data)

    async def test_get_user_by_id(self, session: AsyncSession, test_user: User):
        service = AuthService(session)
        user = await service.get_user_by_id(test_user.id)
        assert user is not None
        assert user.email == test_user.email

    async def test_get_user_by_id_not_found(self, session: AsyncSession):
        service = AuthService(session)
        user = await service.get_user_by_id(uuid.uuid4())
        assert user is None


class TestRestaurantServiceDirect:
    """Прямые тесты RestaurantService."""

    async def test_create(self, session: AsyncSession):
        service = RestaurantService(session)
        data = RestaurantCreate(
            name="Сервис Ресторан",
            address="ул. Сервисная, д. 10",
            cuisine_type="Русская",
        )
        result = await service.create(data)
        assert result.name == "Сервис Ресторан"

    async def test_get_list_empty(self, session: AsyncSession):
        service = RestaurantService(session)
        result = await service.get_list()
        assert result.total == 0

    async def test_get_list_with_data(
        self, session: AsyncSession, test_restaurant: Restaurant
    ):
        service = RestaurantService(session)
        result = await service.get_list()
        assert result.total == 1

    async def test_get_list_filter_cuisine(
        self, session: AsyncSession, test_restaurant: Restaurant
    ):
        service = RestaurantService(session)
        result = await service.get_list(cuisine="Итальянская")
        assert result.total == 1
        result2 = await service.get_list(cuisine="Японская")
        assert result2.total == 0

    async def test_get_by_id(self, session: AsyncSession, test_restaurant: Restaurant):
        service = RestaurantService(session)
        result = await service.get_by_id(test_restaurant.id)
        assert result.name == test_restaurant.name

    async def test_get_by_id_not_found(self, session: AsyncSession):
        service = RestaurantService(session)
        with pytest.raises(NotFoundException):
            await service.get_by_id(uuid.uuid4())

    async def test_update(self, session: AsyncSession, test_restaurant: Restaurant):
        service = RestaurantService(session)
        data = RestaurantUpdate(name="Обновлённый")
        result = await service.update(test_restaurant.id, data)
        assert result.name == "Обновлённый"

    async def test_update_not_found(self, session: AsyncSession):
        service = RestaurantService(session)
        data = RestaurantUpdate(name="Нет")
        with pytest.raises(NotFoundException):
            await service.update(uuid.uuid4(), data)

    async def test_delete(self, session: AsyncSession, test_restaurant: Restaurant):
        service = RestaurantService(session)
        await service.delete(test_restaurant.id)
        with pytest.raises(NotFoundException):
            await service.get_by_id(test_restaurant.id)

    async def test_delete_not_found(self, session: AsyncSession):
        service = RestaurantService(session)
        with pytest.raises(NotFoundException):
            await service.delete(uuid.uuid4())


class TestTableServiceDirect:
    """Прямые тесты TableService."""

    async def test_create(self, session: AsyncSession, test_restaurant: Restaurant):
        service = TableService(session)
        data = TableCreate(
            restaurant_id=test_restaurant.id,
            number=10,
            capacity=6,
            position_x=50,
            position_y=50,
            shape="square",
            zone="terrace",
        )
        result = await service.create(data)
        assert result.number == 10
        assert result.capacity == 6

    async def test_create_restaurant_not_found(self, session: AsyncSession):
        service = TableService(session)
        data = TableCreate(
            restaurant_id=uuid.uuid4(),
            number=1,
            capacity=4,
        )
        with pytest.raises(NotFoundException):
            await service.create(data)

    async def test_get_available(
        self, session: AsyncSession, test_restaurant: Restaurant, test_table: Table
    ):
        service = TableService(session)
        future = datetime.now(timezone.utc) + timedelta(days=5)
        result = await service.get_available(test_restaurant.id, future, 2)
        assert len(result) == 1

    async def test_get_available_booked(
        self,
        session: AsyncSession,
        test_restaurant: Restaurant,
        test_table: Table,
        test_booking: Booking,
    ):
        service = TableService(session)
        result = await service.get_available(
            test_restaurant.id, test_booking.booking_date, 2
        )
        assert len(result) == 0

    async def test_get_floor_plan(
        self, session: AsyncSession, test_restaurant: Restaurant, test_table: Table
    ):
        service = TableService(session)
        result = await service.get_floor_plan(test_restaurant.id)
        assert result.restaurant_name == test_restaurant.name
        assert len(result.tables) == 1

    async def test_get_floor_plan_with_date(
        self,
        session: AsyncSession,
        test_restaurant: Restaurant,
        test_table: Table,
        test_booking: Booking,
    ):
        service = TableService(session)
        result = await service.get_floor_plan(
            test_restaurant.id, test_booking.booking_date
        )
        assert result.tables[0].is_available is False

    async def test_get_floor_plan_not_found(self, session: AsyncSession):
        service = TableService(session)
        with pytest.raises(NotFoundException):
            await service.get_floor_plan(uuid.uuid4())

    async def test_update(self, session: AsyncSession, test_table: Table):
        service = TableService(session)
        data = TableUpdate(capacity=8, zone="vip")
        result = await service.update(test_table.id, data)
        assert result.capacity == 8
        assert result.zone == "vip"

    async def test_update_not_found(self, session: AsyncSession):
        service = TableService(session)
        data = TableUpdate(capacity=8)
        with pytest.raises(NotFoundException):
            await service.update(uuid.uuid4(), data)

    async def test_delete(self, session: AsyncSession, test_table: Table):
        service = TableService(session)
        await service.delete(test_table.id)
        with pytest.raises(NotFoundException):
            await service.update(test_table.id, TableUpdate(capacity=2))

    async def test_delete_not_found(self, session: AsyncSession):
        service = TableService(session)
        with pytest.raises(NotFoundException):
            await service.delete(uuid.uuid4())


class TestBookingServiceDirect:
    """Прямые тесты BookingService."""

    async def test_create_success(
        self, session: AsyncSession, test_user: User, test_table: Table
    ):
        service = BookingService(session)
        future = datetime.now(timezone.utc) + timedelta(days=7)
        data = BookingCreate(
            table_id=test_table.id,
            booking_date=future,
            duration_minutes=90,
            guests_count=3,
            comment="Тест",
        )
        result = await service.create(test_user.id, data)
        assert result.guests_count == 3
        assert result.status == BookingStatus.PENDING

    async def test_create_table_not_found(self, session: AsyncSession, test_user: User):
        service = BookingService(session)
        future = datetime.now(timezone.utc) + timedelta(days=7)
        data = BookingCreate(
            table_id=uuid.uuid4(),
            booking_date=future,
            guests_count=2,
        )
        with pytest.raises(NotFoundException):
            await service.create(test_user.id, data)

    async def test_create_too_many_guests(
        self, session: AsyncSession, test_user: User, test_table: Table
    ):
        service = BookingService(session)
        future = datetime.now(timezone.utc) + timedelta(days=7)
        data = BookingCreate(
            table_id=test_table.id,
            booking_date=future,
            guests_count=10,
        )
        with pytest.raises(BadRequestException):
            await service.create(test_user.id, data)

    async def test_create_past_date(
        self, session: AsyncSession, test_user: User, test_table: Table
    ):
        service = BookingService(session)
        past = datetime.now(timezone.utc) - timedelta(days=1)
        data = BookingCreate(
            table_id=test_table.id,
            booking_date=past,
            guests_count=2,
        )
        with pytest.raises(BadRequestException):
            await service.create(test_user.id, data)

    async def test_create_overlap(
        self,
        session: AsyncSession,
        test_user: User,
        test_table: Table,
        test_booking: Booking,
    ):
        service = BookingService(session)
        data = BookingCreate(
            table_id=test_table.id,
            booking_date=test_booking.booking_date,
            guests_count=2,
        )
        with pytest.raises(BadRequestException):
            await service.create(test_user.id, data)

    async def test_get_user_bookings(
        self, session: AsyncSession, test_user: User, test_booking: Booking
    ):
        service = BookingService(session)
        result = await service.get_user_bookings(test_user.id)
        assert result.total == 1

    async def test_get_user_bookings_empty(self, session: AsyncSession, test_user: User):
        service = BookingService(session)
        result = await service.get_user_bookings(test_user.id)
        assert result.total == 0

    async def test_cancel_success(
        self, session: AsyncSession, test_user: User, test_booking: Booking
    ):
        service = BookingService(session)
        result = await service.cancel(test_booking.id, test_user.id)
        assert result.status == BookingStatus.CANCELLED

    async def test_cancel_not_owner(
        self, session: AsyncSession, admin_user: User, test_booking: Booking
    ):
        service = BookingService(session)
        with pytest.raises(ForbiddenException):
            await service.cancel(test_booking.id, admin_user.id)

    async def test_cancel_already_cancelled(
        self, session: AsyncSession, test_user: User, test_booking: Booking
    ):
        test_booking.status = BookingStatus.CANCELLED
        session.add(test_booking)
        await session.commit()

        service = BookingService(session)
        with pytest.raises(BadRequestException):
            await service.cancel(test_booking.id, test_user.id)

    async def test_cancel_completed(
        self, session: AsyncSession, test_user: User, test_booking: Booking
    ):
        test_booking.status = BookingStatus.COMPLETED
        session.add(test_booking)
        await session.commit()

        service = BookingService(session)
        with pytest.raises(BadRequestException):
            await service.cancel(test_booking.id, test_user.id)

    async def test_cancel_not_found(self, session: AsyncSession, test_user: User):
        service = BookingService(session)
        with pytest.raises(NotFoundException):
            await service.cancel(uuid.uuid4(), test_user.id)

    async def test_confirm_success(
        self, session: AsyncSession, test_booking: Booking
    ):
        service = BookingService(session)
        result = await service.confirm(test_booking.id)
        assert result.status == BookingStatus.CONFIRMED

    async def test_confirm_not_pending(
        self, session: AsyncSession, test_booking: Booking
    ):
        test_booking.status = BookingStatus.CONFIRMED
        session.add(test_booking)
        await session.commit()

        service = BookingService(session)
        with pytest.raises(BadRequestException):
            await service.confirm(test_booking.id)

    async def test_confirm_not_found(self, session: AsyncSession):
        service = BookingService(session)
        with pytest.raises(NotFoundException):
            await service.confirm(uuid.uuid4())
