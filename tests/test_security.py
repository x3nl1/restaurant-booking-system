"""Тесты модуля безопасности."""

from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Тесты хеширования паролей."""

    def test_hash_password(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        hash1 = hash_password("mypassword")
        hash2 = hash_password("mypassword")
        # bcrypt генерирует разные хеши из-за соли
        assert hash1 != hash2


class TestJWT:
    """Тесты JWT-токенов."""

    def test_create_and_decode_token(self):
        data = {"sub": "user-123"}
        token = create_access_token(data)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_create_token_with_expiry(self):
        data = {"sub": "user-123"}
        token = create_access_token(data, expires_delta=timedelta(hours=1))
        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload

    def test_decode_invalid_token(self):
        result = decode_access_token("invalid.token.here")
        assert result is None

    def test_decode_empty_token(self):
        result = decode_access_token("")
        assert result is None
