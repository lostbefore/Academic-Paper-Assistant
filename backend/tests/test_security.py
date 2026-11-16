"""Password hashing and JWT behaviour."""

from __future__ import annotations

import time

import jwt
import pytest

from app.config import get_settings
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_is_salted_and_verifiable():
    first = hash_password("correct horse battery")
    second = hash_password("correct horse battery")
    assert first != second, "bcrypt must produce a different salt each time"
    assert first.startswith("$2")
    assert verify_password("correct horse battery", first)
    assert not verify_password("wrong password", first)


def test_short_password_is_rejected():
    with pytest.raises(ValueError):
        hash_password("short")


def test_verify_handles_corrupt_hash():
    assert verify_password("anything", "not-a-bcrypt-hash") is False


def test_token_roundtrip():
    token = create_access_token("user-1", "a@b.c", "user")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["email"] == "a@b.c"
    assert payload["exp"] > time.time()


def test_token_signed_with_wrong_secret_is_rejected():
    forged = jwt.encode({"sub": "x"}, "another-secret", algorithm="HS256")
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(forged)


def test_expired_token_is_rejected():
    settings = get_settings()
    expired = jwt.encode(
        {"sub": "user-1", "exp": int(time.time()) - 10},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired)
