"""Роутер бронирований."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingListResponse, BookingResponse
from app.services.auth_service import AuthService
from app.services.booking_service import BookingService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/bookings", tags=["Бронирования"])


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(
    data: BookingCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BookingResponse:
    """Создание бронирования."""
    service = BookingService(session)
    return await service.create(current_user.id, data)


@router.get("/my", response_model=BookingListResponse)
async def get_my_bookings(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BookingListResponse:
    """Получение бронирований текущего пользователя."""
    service = BookingService(session)
    return await service.get_user_bookings(current_user.id, limit=limit, offset=offset)


@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BookingResponse:
    """Отмена бронирования."""
    service = BookingService(session)
    result = await service.cancel(booking_id, current_user.id)

    await NotificationService.send_booking_cancellation(
        to_email=current_user.email,
        guest_name=current_user.full_name,
        restaurant_name=result.restaurant_name or "Ресторан",
        booking_date=result.booking_date.strftime("%d.%m.%Y %H:%M"),
    )
    return result


@router.patch("/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(get_admin_user),
) -> BookingResponse:
    """Подтверждение бронирования (только админ)."""
    service = BookingService(session)
    result = await service.confirm(booking_id)

    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(result.user_id)
    if user:
        await NotificationService.send_booking_confirmation(
            to_email=user.email,
            guest_name=user.full_name,
            restaurant_name=result.restaurant_name or "Ресторан",
            booking_date=result.booking_date.strftime("%d.%m.%Y %H:%M"),
        )
    return result
