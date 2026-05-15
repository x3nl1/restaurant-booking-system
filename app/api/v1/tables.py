"""Роутер столиков."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.table import FloorPlanResponse, TableCreate, TableResponse, TableUpdate
from app.services.table_service import TableService

router = APIRouter(prefix="/tables", tags=["Столики"])


@router.get("/available", response_model=list[TableResponse])
async def get_available_tables(
    restaurant_id: uuid.UUID = Query(...),
    date: datetime = Query(...),
    guests: int = Query(..., ge=1),
    duration: int = Query(default=120, ge=30, le=480),
    session: AsyncSession = Depends(get_session),
) -> list[TableResponse]:
    """Получение доступных столиков на указанную дату."""
    service = TableService(session)
    return await service.get_available(restaurant_id, date, guests, duration)


@router.get("/floor-plan/{restaurant_id}", response_model=FloorPlanResponse)
async def get_floor_plan(
    restaurant_id: uuid.UUID,
    date: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> FloorPlanResponse:
    """Получение карты зала с расположением столиков."""
    service = TableService(session)
    return await service.get_floor_plan(restaurant_id, date)


@router.post("", response_model=TableResponse, status_code=201)
async def create_table(
    data: TableCreate,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_admin_user),
) -> TableResponse:
    """Создание столика (только админ)."""
    service = TableService(session)
    return await service.create(data)


@router.patch("/{table_id}", response_model=TableResponse)
async def update_table(
    table_id: uuid.UUID,
    data: TableUpdate,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_admin_user),
) -> TableResponse:
    """Обновление столика (только админ)."""
    service = TableService(session)
    return await service.update(table_id, data)


@router.delete("/{table_id}", status_code=204)
async def delete_table(
    table_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_admin_user),
) -> None:
    """Удаление столика (только админ)."""
    service = TableService(session)
    await service.delete(table_id)
