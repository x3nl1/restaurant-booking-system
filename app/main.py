"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.restaurants import router as restaurants_router
from app.api.v1.tables import router as tables_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="API для бронирования столиков в ресторанах",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow_credentials=True несовместим с allow_origins=["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(auth_router, prefix="/api/v1")
app.include_router(restaurants_router, prefix="/api/v1")
app.include_router(tables_router, prefix="/api/v1")
app.include_router(bookings_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "service": settings.APP_NAME}
