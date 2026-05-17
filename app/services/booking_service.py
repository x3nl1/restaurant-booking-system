"""Сервис бронирования."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.booking import Booking, BookingStatus
from app.models.table import Table
from app.schemas.booking import BookingCreate, BookingListResponse, BookingResponse


class BookingService:
    """Сервис для управления бронированиями."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: uuid.UUID, data: BookingCreate) -> BookingResponse:
        """Создание бронирования."""
        table_result = await self.session.execute(
            select(Table).where(Table.id == data.table_id)
        )
        table = table_result.scalar_one_or_none()
        if not table:
            raise NotFoundException("Столик не найден")

        if data.guests_count > table.capacity:
            raise BadRequestException(
                f"Столик вмещает максимум {table.capacity} гостей"
            )

        # Нормализуем datetime к aware UTC
        booking_dt = data.booking_date
        if booking_dt.tzinfo is None:
            booking_dt = booking_dt.replace(tzinfo=UTC)

        if booking_dt <= datetime.now(UTC):
            raise BadRequestException("Дата бронирования должна быть в будущем")

        # Используем нормализованный booking_dt для проверки пересечений
        is_booked = await self._check_overlap(
            data.table_id, booking_dt, data.duration_minutes
        )
        if is_booked:
            raise BadRequestException("Столик уже забронирован на это время")

        booking = Booking(
            user_id=user_id,
            table_id=data.table_id,
            booking_date=booking_dt,
            duration_minutes=data.duration_minutes,
            guests_count=data.guests_count,
            comment=data.comment,
            guest_name=data.guest_name,
            guest_phone=data.guest_phone,
        )
        self.session.add(booking)
        await self.session.flush()
        await self.session.refresh(booking)

        return self._to_response(booking, table)

    async def get_user_bookings(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> BookingListResponse:
        """Получение бронирований пользователя с пагинацией."""
        from sqlalchemy import func

        # Общее количество бронирований пользователя
        count_result = await self.session.execute(
            select(func.count(Booking.id)).where(Booking.user_id == user_id)
        )
        total = count_result.scalar() or 0

        # Загружаем бронирования с join на table и restaurant (избегаем N+1)
        result = await self.session.execute(
            select(Booking)
            .options(selectinload(Booking.table).selectinload(Table.restaurant))
            .where(Booking.user_id == user_id)
            .order_by(Booking.booking_date.desc())
            .limit(limit)
            .offset(offset)
        )
        bookings = result.scalars().all()

        items = [self._to_response(b, b.table) for b in bookings]
        return BookingListResponse(items=items, total=total)

    async def cancel(self, booking_id: uuid.UUID, user_id: uuid.UUID) -> BookingResponse:
        """Отмена бронирования пользователем."""
        booking = await self._get_with_table(booking_id)

        if booking.user_id != user_id:
            raise ForbiddenException("Вы не можете отменить чужое бронирование")

        if booking.status == BookingStatus.CANCELLED:
            raise BadRequestException("Бронирование уже отменено")

        if booking.status == BookingStatus.COMPLETED:
            raise BadRequestException("Нельзя отменить завершённое бронирование")

        booking.status = BookingStatus.CANCELLED
        await self.session.flush()
        await self.session.refresh(booking)
        return self._to_response(booking, booking.table)

    async def confirm(self, booking_id: uuid.UUID) -> BookingResponse:
        """Подтверждение бронирования администратором."""
        booking = await self._get_with_table(booking_id)

        if booking.status != BookingStatus.PENDING:
            raise BadRequestException("Можно подтвердить только ожидающее бронирование")

        booking.status = BookingStatus.CONFIRMED
        await self.session.flush()
        await self.session.refresh(booking)
        return self._to_response(booking, booking.table)

    async def _check_overlap(
        self, table_id: uuid.UUID, date: datetime, duration: int
    ) -> bool:
        """Проверка пересечения бронирований."""
        end_time = date + timedelta(minutes=duration)

        result = await self.session.execute(
            select(Booking).where(
                and_(
                    Booking.table_id == table_id,
                    Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                    Booking.booking_date < end_time,
                )
            )
        )
        bookings = result.scalars().all()

        for booking in bookings:
            # Нормализуем к aware для корректного сравнения
            b_date = booking.booking_date
            if b_date.tzinfo is None:
                b_date = b_date.replace(tzinfo=UTC)
            booking_end = b_date + timedelta(minutes=booking.duration_minutes)
            if booking_end > date:
                return True
        return False

    async def _get_with_table(self, booking_id: uuid.UUID) -> Booking:
        """Получение бронирования с подгрузкой столика и ресторана."""
        result = await self.session.execute(
            select(Booking)
            .options(selectinload(Booking.table).selectinload(Table.restaurant))
            .where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        if not booking:
            raise NotFoundException("Бронирование не найдено")
        return booking

    def _to_response(self, booking: Booking, table: Table | None) -> BookingResponse:
        """Конвертация модели в ответ (синхронная, без доп. запросов)."""
        restaurant_name = None
        table_number = None
        if table:
            table_number = table.number
            if table.restaurant:
                restaurant_name = table.restaurant.name

        return BookingResponse(
            id=booking.id,
            user_id=booking.user_id,
            table_id=booking.table_id,
            booking_date=booking.booking_date,
            duration_minutes=booking.duration_minutes,
            guests_count=booking.guests_count,
            status=booking.status,
            comment=booking.comment,
            guest_name=booking.guest_name,
            guest_phone=booking.guest_phone,
            created_at=booking.created_at,
            updated_at=booking.updated_at,
            restaurant_name=restaurant_name,
            table_number=table_number,
        )
