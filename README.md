# 🍽️ Restaurant Booking System

Система бронирования столиков в ресторанах — бэкенд для мобильного приложения.

## Описание

REST API сервис для управления бронированием столиков в ресторанах с поддержкой:
- Управления ресторанами и залами
- Визуализации карты зала со свободными/занятыми столиками
- Бронирования столиков с проверкой доступности
- Уведомлений о подтверждении бронирования (email)
- Интеграции с картами для навигации к ресторану
- JWT-аутентификации и авторизации

## Технологический стек

- **Python 3.12+** — основной язык
- **FastAPI** — веб-фреймворк
- **PostgreSQL 16** — база данных
- **SQLAlchemy 2.0** — ORM (async)
- **Alembic** — миграции БД
- **Redis** — кэширование
- **Pydantic V2** — валидация данных
- **Docker & Docker Compose** — контейнеризация
- **pytest** — тестирование (coverage ≥ 90%)
- **Bandit + Safety** — SAST и проверка зависимостей

## Быстрый старт

### Требования
- Docker & Docker Compose
- Python 3.12+ (для локальной разработки)

### Запуск через Docker Compose

```bash
docker-compose up --build
```

API доступен: http://localhost:8000  
Swagger UI: http://localhost:8000/docs  
ReDoc: http://localhost:8000/redoc

### Локальная разработка

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Структура проекта

```
├── app/
│   ├── api/v1/            # Роутеры API
│   ├── core/              # Конфигурация, безопасность, БД
│   ├── models/            # SQLAlchemy модели
│   ├── schemas/           # Pydantic схемы
│   ├── services/          # Бизнес-логика
│   └── main.py            # Точка входа
├── alembic/               # Миграции БД
├── tests/                 # Тесты (pytest)
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| POST | /api/v1/auth/register | Регистрация |
| POST | /api/v1/auth/login | Авторизация |
| GET | /api/v1/restaurants | Список ресторанов |
| GET | /api/v1/restaurants/{id} | Детали ресторана |
| GET | /api/v1/restaurants/{id}/floor-plan | Карта зала |
| GET | /api/v1/tables/available | Доступные столики |
| POST | /api/v1/bookings | Создать бронирование |
| GET | /api/v1/bookings/my | Мои бронирования |
| PATCH | /api/v1/bookings/{id}/cancel | Отменить бронирование |
| PATCH | /api/v1/bookings/{id}/confirm | Подтвердить (админ) |

## Тестирование

```bash
pytest --cov=app --cov-report=html tests/
```

## Безопасность

```bash
bandit -r app/
safety check -r requirements.txt
```

## Git Flow

- `main` — стабильная версия
- `develop` — ветка разработки
- `feature/*` — ветки фич

Коммиты: [Conventional Commits](https://www.conventionalcommits.org/)

## Лицензия

MIT
