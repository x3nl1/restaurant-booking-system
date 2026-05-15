# Архитектура системы бронирования столиков

## C4 — Контекстная диаграмма

```mermaid
C4Context
    title Система бронирования столиков — Контекст

    Person(user, "Пользователь", "Бронирует столики через мобильное приложение")
    Person(admin, "Администратор", "Управляет ресторанами, столиками, подтверждает брони")

    System(booking_system, "Restaurant Booking API", "REST API для бронирования столиков")

    System_Ext(email, "SMTP-сервер", "Отправка email-уведомлений")
    System_Ext(maps, "Картографический сервис", "Навигация к ресторану")

    Rel(user, booking_system, "Бронирует столики", "HTTPS/JSON")
    Rel(admin, booking_system, "Управляет данными", "HTTPS/JSON")
    Rel(booking_system, email, "Отправляет уведомления", "SMTP")
    Rel(user, maps, "Строит маршрут", "HTTPS")
```

## C4 — Контейнерная диаграмма

```mermaid
C4Container
    title Restaurant Booking System — Контейнеры

    Person(user, "Пользователь")
    Person(admin, "Администратор")

    Container_Boundary(system, "Restaurant Booking System") {
        Container(api, "FastAPI Application", "Python 3.12, FastAPI", "REST API, бизнес-логика")
        ContainerDb(db, "PostgreSQL 16", "SQL", "Хранение данных")
        Container(redis, "Redis 7", "Key-Value", "Кэширование")
        Container(mailhog, "MailHog", "SMTP", "Отправка email (dev)")
    }

    Rel(user, api, "HTTPS/JSON")
    Rel(admin, api, "HTTPS/JSON")
    Rel(api, db, "asyncpg", "TCP:5432")
    Rel(api, redis, "redis-py", "TCP:6379")
    Rel(api, mailhog, "aiosmtplib", "TCP:1025")
```

## Компонентная диаграмма

```mermaid
graph TB
    subgraph "API Layer"
        AUTH["/api/v1/auth"]
        REST["/api/v1/restaurants"]
        TABLES["/api/v1/tables"]
        BOOK["/api/v1/bookings"]
    end

    subgraph "Service Layer"
        AS[AuthService]
        RS[RestaurantService]
        TS[TableService]
        BS[BookingService]
        NS[NotificationService]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL)]
        MODELS[SQLAlchemy Models]
    end

    AUTH --> AS
    REST --> RS
    TABLES --> TS
    BOOK --> BS
    BOOK --> NS

    AS --> MODELS
    RS --> MODELS
    TS --> MODELS
    BS --> MODELS
    MODELS --> DB
```

## ER-диаграмма

```mermaid
erDiagram
    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        string phone
        boolean is_active
        boolean is_admin
        datetime created_at
    }

    RESTAURANTS {
        uuid id PK
        string name
        text description
        string address
        string phone
        string email
        float latitude
        float longitude
        string working_hours
        int average_check
        string cuisine_type
        string image_url
        int floor_plan_width
        int floor_plan_height
        datetime created_at
    }

    TABLES {
        uuid id PK
        uuid restaurant_id FK
        int number
        int capacity
        int position_x
        int position_y
        string shape
        string zone
    }

    BOOKINGS {
        uuid id PK
        uuid user_id FK
        uuid table_id FK
        datetime booking_date
        int duration_minutes
        int guests_count
        enum status
        text comment
        string guest_name
        string guest_phone
        datetime created_at
        datetime updated_at
    }

    USERS ||--o{ BOOKINGS : "создаёт"
    RESTAURANTS ||--o{ TABLES : "содержит"
    TABLES ||--o{ BOOKINGS : "бронируется"
```

## Sequence-диаграмма: Создание бронирования

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant API as FastAPI
    participant Auth as AuthService
    participant BS as BookingService
    participant DB as PostgreSQL
    participant NS as NotificationService
    participant SMTP as SMTP-сервер

    U->>API: POST /api/v1/bookings (JWT + body)
    API->>Auth: Проверка JWT-токена
    Auth-->>API: User object
    API->>BS: create(user_id, data)
    BS->>DB: SELECT table WHERE id = ?
    DB-->>BS: Table (capacity=4)
    BS->>BS: Проверка вместимости
    BS->>BS: Проверка даты (будущее)
    BS->>DB: SELECT bookings (overlap check)
    DB-->>BS: [] (нет пересечений)
    BS->>DB: INSERT booking
    DB-->>BS: Booking (status=pending)
    BS-->>API: BookingResponse
    API-->>U: 201 Created
    
    Note over API,SMTP: При подтверждении админом
    API->>NS: send_booking_confirmation()
    NS->>SMTP: Email
    SMTP-->>NS: OK
```

## Sequence-диаграмма: Получение карты зала

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant API as FastAPI
    participant TS as TableService
    participant DB as PostgreSQL

    U->>API: GET /api/v1/tables/floor-plan/{id}?date=...
    API->>TS: get_floor_plan(restaurant_id, date)
    TS->>DB: SELECT restaurant WHERE id = ?
    DB-->>TS: Restaurant (800x600)
    TS->>DB: SELECT tables WHERE restaurant_id = ?
    DB-->>TS: [Table1, Table2, ...]
    loop Для каждого столика
        TS->>DB: SELECT bookings (overlap)
        DB-->>TS: is_booked = true/false
    end
    TS-->>API: FloorPlanResponse
    API-->>U: 200 OK {tables: [{x, y, available}, ...]}
```
