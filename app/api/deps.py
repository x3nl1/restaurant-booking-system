"""Зависимости для Dependency Injection в роутерах."""

import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.models.user import User
from app.services.auth_service import AuthService


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Получение текущего пользователя из JWT-токена."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Токен не предоставлен")

    token = authorization.removeprefix("Bearer ")
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Невалидный токен")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Невалидный токен")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Невалидный токен")

    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise UnauthorizedException("Пользователь не найден")

    if not user.is_active:
        raise UnauthorizedException("Аккаунт деактивирован")

    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверка, что пользователь — администратор."""
    if not current_user.is_admin:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("Требуются права администратора")
    return current_user
