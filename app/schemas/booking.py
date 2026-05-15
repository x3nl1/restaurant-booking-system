"""Схемы бронирования."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    table_id: uuid.UUID
    booking_date: datetime
    duration_minutes: int = Field(default=120, ge=30, le=480)
    guests_count: int = Field(ge=1, le=20)
    comment: str | None = None
    guest_name: str | None = None
    guest_phone: str | None = None


class BookingUpdate(BaseModel):
    booking_date: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=30, le=480)
    guests_count: int | None = Field(default=None, ge=1, le=20)
    comment: str | None = None


class BookingResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    table_id: uuid.UUID
    booking_date: datetime
    duration_minutes: int
    guests_count: int
    status: BookingStatus
    comment: str | None
    guest_name: str | None
    guest_phone: str | None
    created_at: datetime
    updated_at: datetime
    restaurant_name: str | None = None
    table_number: int | None = None

    model_config = {"from_attributes": True}


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
