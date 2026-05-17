# Архитектура системы бронирования столиков

## Контекстная диаграмма

```mermaid
graph TD
    User["Пользователь"]
    Admin["Администратор"]
    System["Система бронирования столиков<br/>REST API"]
    Email["SMTP-сервер"]
    Maps["Картографический сервис"]

    User -->|"Бронирование<br/>HTTPS/JSON"| System
    Admin -->|"Управление<br/>HTTPS/JSON"| System
    System -->|"Уведомления<br/>SMTP"| Email
    User -->|"Навигация<br/>HTTPS"| Maps
```

## Контейнерная диаграмма

```mermaid
graph TD
    User["Пользователь"]
    Admin["Администратор"]

    subgraph boundary["Система бронирования столиков"]
        API["FastAPI Application<br/>Python 3.12"]
        DB[("PostgreSQL 16")]
        Redis["Redis 7"]
        Mail["Почтовый сервер<br/>SMTP"]
    end

    User -->|"HTTPS/JSON"| API
    Admin -->|"HTTPS/JSON"| API
    API -->|"asyncpg<br/>TCP:5432"| DB
    API -->|"redis-py<br/>TCP:6379"| Redis
    API -->|"aiosmtplib<br/>TCP:1025"| Mail
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

    subgraph "External"
        SMTP[SMTP-сервер]
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
    NS --> SMTP
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
