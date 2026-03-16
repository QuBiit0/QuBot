"""
Unit tests for security utilities — JWT, password hashing, token lifecycle
"""

import time
from uuid import uuid4

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = get_password_hash("mysecret")
        assert hashed != "mysecret"

    def test_correct_password_verifies(self):
        hashed = get_password_hash("correcthorsebatterystaple")
        assert verify_password("correcthorsebatterystaple", hashed) is True

    def test_wrong_password_rejected(self):
        hashed = get_password_hash("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_password_hashes(self):
        hashed = get_password_hash("")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_two_hashes_differ(self):
        """bcrypt includes salt — same plaintext yields different hashes"""
        h1 = get_password_hash("samepassword")
        h2 = get_password_hash("samepassword")
        assert h1 != h2


class TestAccessToken:
    def test_create_and_decode(self):
        user_id = str(uuid4())
        token, jti = create_access_token(user_id=user_id, role="user")

        assert token
        assert jti

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["role"] == "user"
        assert payload["type"] == "access"
        assert payload["jti"] == jti

    def test_admin_role_preserved(self):
        user_id = str(uuid4())
        token, _ = create_access_token(user_id=user_id, role="admin")
        payload = decode_token(token)
        assert payload["role"] == "admin"

    def test_unique_jti_each_call(self):
        user_id = str(uuid4())
        _, jti1 = create_access_token(user_id=user_id, role="user")
        _, jti2 = create_access_token(user_id=user_id, role="user")
        assert jti1 != jti2

    def test_invalid_token_returns_none(self):
        assert decode_token("not.a.token") is None

    def test_tampered_token_returns_none(self):
        user_id = str(uuid4())
        token, _ = create_access_token(user_id=user_id, role="user")
        # Flip last character
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        assert decode_token(tampered) is None


class TestRefreshToken:
    def test_create_and_decode_refresh(self):
        user_id = str(uuid4())
        token, jti, expires_at = create_refresh_token(user_id=user_id)

        assert token
        assert jti
        assert expires_at is not None

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_refresh_token_has_longer_expiry(self):
        """Refresh tokens should expire further in the future than access tokens"""
        user_id = str(uuid4())
        access_token, _ = create_access_token(user_id=user_id, role="user")
        refresh_token, _, _ = create_refresh_token(user_id=user_id)

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        assert refresh_payload["exp"] > access_payload["exp"]
