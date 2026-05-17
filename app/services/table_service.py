"""Сервис столиков."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.booking import Booking, BookingStatus
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.schemas.table import (
    FloorPlanResponse,
    TableCreate,
    TableResponse,
    TableUpdate,
)


class TableService:
    """Сервис для управления столиками."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: TableCreate) -> TableResponse:
        """Создание столика."""
        rest_result = await self.session.execute(
            select(Restaurant).where(Restaurant.id == data.restaurant_id)
        )
        if not rest_result.scalar_one_or_none():
            raise NotFoundException("Ресторан не найден")

        table = Table(**data.model_dump())
        self.session.add(table)
        await self.session.flush()
        await self.session.refresh(table)
        return TableResponse.model_validate(table)

    async def get_available(
        self,
        restaurant_id: uuid.UUID,
        date: datetime,
        guests: int,
        duration: int = 120,
    ) -> list[TableResponse]:
        """Получение доступных столиков на указанную дату."""
        tables_result = await self.session.execute(
            select(Table).where(
                and_(
                    Table.restaurant_id == restaurant_id,
                    Table.capacity >= guests,
                )
            )
        )
        tables = tables_result.scalars().all()

        if not tables:
            return []

        # Получаем все активные бронирования для этих столиков одним запросом
        table_ids = [t.id for t in tables]
        booked_ids = await self._get_booked_table_ids(table_ids, date, duration)

        available = []
        for table in tables:
            if table.id not in booked_ids:
                response = TableResponse.model_validate(table)
                response.is_available = True
                available.append(response)

        return available

    async def get_floor_plan(
        self, restaurant_id: uuid.UUID, date: datetime | None = None
    ) -> FloorPlanResponse:
        """Получение карты зала с информацией о доступности."""
        rest_result = await self.session.execute(
            select(Restaurant).where(Restaurant.id == restaurant_id)
        )
        restaurant = rest_result.scalar_one_or_none()
        if not restaurant:
            raise NotFoundException("Ресторан не найден")

        tables_result = await self.session.execute(
            select(Table).where(Table.restaurant_id == restaurant_id)
        )
        tables = tables_result.scalars().all()

        # Если указана дата — проверяем доступность одним запросом
        booked_ids: set[uuid.UUID] = set()
        if date and tables:
            table_ids = [t.id for t in tables]
            booked_ids = await self._get_booked_table_ids(table_ids, date, 120)

        table_responses = []
        for table in tables:
            response = TableResponse.model_validate(table)
            if date:
                response.is_available = table.id not in booked_ids
            table_responses.append(response)

        return FloorPlanResponse(
            restaurant_id=restaurant.id,
            restaurant_name=restaurant.name,
            width=restaurant.floor_plan_width,
            height=restaurant.floor_plan_height,
            tables=table_responses,
        )

    async def update(self, table_id: uuid.UUID, data: TableUpdate) -> TableResponse:
        """Обновление столика."""
        table = await self._get_or_404(table_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(table, key, value)
        await self.session.flush()
        await self.session.refresh(table)
        return TableResponse.model_validate(table)

    async def delete(self, table_id: uuid.UUID) -> None:
        """Удаление столика."""
        table = await self._get_or_404(table_id)
        await self.session.delete(table)

    async def _get_booked_table_ids(
        self, table_ids: list[uuid.UUID], date: datetime, duration: int
    ) -> set[uuid.UUID]:
        """Получение ID занятых столиков одним запросом (решение N+1)."""
        end_time = date + timedelta(minutes=duration)

        result = await self.session.execute(
            select(Booking).where(
                and_(
                    Booking.table_id.in_(table_ids),
                    Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                    Booking.booking_date < end_time,
                )
            )
        )
        bookings = result.scalars().all()

        booked: set[uuid.UUID] = set()
        for booking in bookings:
            booking_end = booking.booking_date + timedelta(minutes=booking.duration_minutes)
            if booking_end > date:
                booked.add(booking.table_id)
        return booked

    async def _get_or_404(self, table_id: uuid.UUID) -> Table:
        result = await self.session.execute(select(Table).where(Table.id == table_id))
        table = result.scalar_one_or_none()
        if not table:
            raise NotFoundException("Столик не найден")
        return table
