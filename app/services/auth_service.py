"""Сервис аутентификации."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse


class AuthService:
    """Сервис для регистрации и авторизации пользователей."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, data: UserCreate) -> TokenResponse:
        """Регистрация нового пользователя."""
        existing = await self.session.execute(
            select(User).where(User.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Пользователь с таким email уже существует")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    async def login(self, data: UserLogin) -> TokenResponse:
        """Авторизация пользователя."""
        result = await self.session.execute(
            select(User).where(User.email == data.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedException("Неверный email или пароль")

        if not user.is_active:
            raise UnauthorizedException("Аккаунт деактивирован")

        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Получение пользователя по ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
