"""Роутер ресторанов."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantListResponse,
    RestaurantResponse,
    RestaurantUpdate,
)
from app.services.restaurant_service import RestaurantService

router = APIRouter(prefix="/restaurants", tags=["Рестораны"])


@router.get("", response_model=RestaurantListResponse)
async def get_restaurants(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    cuisine: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> RestaurantListResponse:
    """Получение списка ресторанов."""
    service = RestaurantService(session)
    return await service.get_list(page=page, size=size, cuisine=cuisine)


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(
    restaurant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> RestaurantResponse:
    """Получение ресторана по ID."""
    service = RestaurantService(session)
    return await service.get_by_id(restaurant_id)


@router.post("", response_model=RestaurantResponse, status_code=201)
async def create_restaurant(
    data: RestaurantCreate,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_admin_user),
) -> RestaurantResponse:
    """Создание ресторана (только админ)."""
    service = RestaurantService(session)
    return await service.create(data)


@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: uuid.UUID,
    data: RestaurantUpdate,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_admin_user),
) -> RestaurantResponse:
    """Обновление ресторана (только админ)."""
    service = RestaurantService(session)
    return await service.update(restaurant_id, data)


@router.delete("/{restaurant_id}", status_code=204)
async def delete_restaurant(
    restaurant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_admin_user),
) -> None:
    """Удаление ресторана (только админ)."""
    service = RestaurantService(session)
    await service.delete(restaurant_id)
