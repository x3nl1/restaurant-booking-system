"""Сервис ресторанов."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.restaurant import Restaurant
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantListResponse,
    RestaurantResponse,
    RestaurantUpdate,
)


class RestaurantService:
    """Сервис для управления ресторанами."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(
        self, page: int = 1, size: int = 20, cuisine: str | None = None
    ) -> RestaurantListResponse:
        """Получение списка ресторанов с пагинацией."""
        query = select(Restaurant)
        count_query = select(func.count(Restaurant.id))

        if cuisine:
            query = query.where(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
            count_query = count_query.where(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))

        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(Restaurant.name)
        result = await self.session.execute(query)
        restaurants = result.scalars().all()

        return RestaurantListResponse(
            items=[RestaurantResponse.model_validate(r) for r in restaurants],
            total=total,
            page=page,
            size=size,
        )

    async def get_by_id(self, restaurant_id: uuid.UUID) -> RestaurantResponse:
        """Получение ресторана по ID."""
        restaurant = await self._get_or_404(restaurant_id)
        return RestaurantResponse.model_validate(restaurant)

    async def create(self, data: RestaurantCreate) -> RestaurantResponse:
        """Создание ресторана."""
        restaurant = Restaurant(**data.model_dump())
        self.session.add(restaurant)
        await self.session.flush()
        await self.session.refresh(restaurant)
        return RestaurantResponse.model_validate(restaurant)

    async def update(
        self, restaurant_id: uuid.UUID, data: RestaurantUpdate
    ) -> RestaurantResponse:
        """Обновление ресторана."""
        restaurant = await self._get_or_404(restaurant_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(restaurant, key, value)
        await self.session.flush()
        await self.session.refresh(restaurant)
        return RestaurantResponse.model_validate(restaurant)

    async def delete(self, restaurant_id: uuid.UUID) -> None:
        """Удаление ресторана."""
        restaurant = await self._get_or_404(restaurant_id)
        await self.session.delete(restaurant)

    async def _get_or_404(self, restaurant_id: uuid.UUID) -> Restaurant:
        result = await self.session.execute(
            select(Restaurant).where(Restaurant.id == restaurant_id)
        )
        restaurant = result.scalar_one_or_none()
        if not restaurant:
            raise NotFoundException("Ресторан не найден")
        return restaurant
