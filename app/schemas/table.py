"""Схемы столика."""

import uuid

from pydantic import BaseModel, Field


class TableCreate(BaseModel):
    restaurant_id: uuid.UUID
    number: int = Field(ge=1)
    capacity: int = Field(ge=1, le=20)
    position_x: int = Field(default=0, ge=0)
    position_y: int = Field(default=0, ge=0)
    shape: str = Field(default="round", pattern=r"^(round|square|rectangle)$")
    zone: str = Field(default="main", pattern=r"^(main|terrace|vip|bar)$")


class TableUpdate(BaseModel):
    capacity: int | None = Field(default=None, ge=1, le=20)
    position_x: int | None = Field(default=None, ge=0)
    position_y: int | None = Field(default=None, ge=0)
    shape: str | None = Field(default=None, pattern=r"^(round|square|rectangle)$")
    zone: str | None = Field(default=None, pattern=r"^(main|terrace|vip|bar)$")


class TableResponse(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    number: int
    capacity: int
    position_x: int
    position_y: int
    shape: str
    zone: str
    is_available: bool = True

    model_config = {"from_attributes": True}


class FloorPlanResponse(BaseModel):
    restaurant_id: uuid.UUID
    restaurant_name: str
    width: int
    height: int
    tables: list[TableResponse]
