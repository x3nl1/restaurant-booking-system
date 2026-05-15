"""Сервис бронирования."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

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

        if data.booking_date <= datetime.now(timezone.utc):
            raise BadRequestException("Дата бронирования должна быть в будущем")

        is_booked = await self._check_overlap(
            data.table_id, data.booking_date, data.duration_minutes
        )
        if is_booked:
            raise BadRequestException("Столик уже забронирован на это время")

        booking = Booking(
            user_id=user_id,
            table_id=data.table_id,
            booking_date=data.booking_date,
            duration_minutes=data.duration_minutes,
            guests_count=data.guests_count,
            comment=data.comment,
            guest_name=data.guest_name,
            guest_phone=data.guest_phone,
        )
        self.session.add(booking)
        await self.session.flush()
        await self.session.refresh(booking)

        return await self._to_response(booking)

    async def get_user_bookings(self, user_id: uuid.UUID) -> BookingListResponse:
        """Получение бронирований пользователя."""
        result = await self.session.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(Booking.booking_date.desc())
        )
        bookings = result.scalars().all()

        items = [await self._to_response(b) for b in bookings]
        return BookingListResponse(items=items, total=len(items))

    async def cancel(self, booking_id: uuid.UUID, user_id: uuid.UUID) -> BookingResponse:
        """Отмена бронирования пользователем."""
        booking = await self._get_or_404(booking_id)

        if booking.user_id != user_id:
            raise ForbiddenException("Вы не можете отменить чужое бронирование")

        if booking.status == BookingStatus.CANCELLED:
            raise BadRequestException("Бронирование уже отменено")

        if booking.status == BookingStatus.COMPLETED:
            raise BadRequestException("Нельзя отменить завершённое бронирование")

        booking.status = BookingStatus.CANCELLED
        await self.session.flush()
        await self.session.refresh(booking)
        return await self._to_response(booking)

    async def confirm(self, booking_id: uuid.UUID) -> BookingResponse:
        """Подтверждение бронирования администратором."""
        booking = await self._get_or_404(booking_id)

        if booking.status != BookingStatus.PENDING:
            raise BadRequestException("Можно подтвердить только ожидающее бронирование")

        booking.status = BookingStatus.CONFIRMED
        await self.session.flush()
        await self.session.refresh(booking)
        return await self._to_response(booking)

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
            booking_end = booking.booking_date + timedelta(minutes=booking.duration_minutes)
            if booking_end > date:
                return True
        return False

    async def _get_or_404(self, booking_id: uuid.UUID) -> Booking:
        result = await self.session.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        if not booking:
            raise NotFoundException("Бронирование не найдено")
        return booking

    async def _to_response(self, booking: Booking) -> BookingResponse:
        """Конвертация модели в ответ с дополнительными данными."""
        table_result = await self.session.execute(
            select(Table).where(Table.id == booking.table_id)
        )
        table = table_result.scalar_one_or_none()

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
