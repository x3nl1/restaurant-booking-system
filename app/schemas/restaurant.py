"""Схемы ресторана."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    address: str = Field(min_length=5, max_length=500)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    working_hours: str | None = None
    average_check: int | None = Field(default=None, ge=0)
    cuisine_type: str | None = None
    image_url: str | None = None
    floor_plan_width: int = Field(default=800, ge=100, le=2000)
    floor_plan_height: int = Field(default=600, ge=100, le=2000)


class RestaurantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    address: str | None = Field(default=None, min_length=5, max_length=500)
    phone: str | None = None
    email: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    working_hours: str | None = None
    average_check: int | None = None
    cuisine_type: str | None = None
    image_url: str | None = None


class RestaurantResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    address: str
    phone: str | None
    email: str | None
    latitude: float | None
    longitude: float | None
    working_hours: str | None
    average_check: int | None
    cuisine_type: str | None
    image_url: str | None
    floor_plan_width: int
    floor_plan_height: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RestaurantListResponse(BaseModel):
    items: list[RestaurantResponse]
    total: int
    page: int
    size: int
