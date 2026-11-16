"""Authentication endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from .. import db
from ..deps import current_user
from ..schemas import LoginRequest, RegisterRequest, TokenOut, UserOut
from ..security import create_access_token, hash_password, verify_password
from ..config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _public(row: dict) -> UserOut:
    return UserOut(
        id=row["id"],
        email=row["email"],
        name=row["name"] or row["email"].split("@")[0],
        role=row["role"],
        created_at=row["created_at"],
    )


def _issue(row: dict) -> TokenOut:
    token = create_access_token(row["id"], row["email"], row["role"])
    return TokenOut(access_token=token, user=_public(row))


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterRequest) -> TokenOut:
    settings = get_settings()
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(status_code=403, detail="Registration is disabled on this instance")
    if db.fetch_one("SELECT id FROM users WHERE email = ?", (payload.email,)):
        raise HTTPException(status_code=409, detail="This email is already registered")
    user_id = uuid.uuid4().hex
    db.execute(
        "INSERT INTO users (id, email, name, password_hash, role, created_at) VALUES (?,?,?,?,?,?)",
        (user_id, payload.email, payload.name.strip(), hash_password(payload.password), "user", db.utcnow()),
    )
    row = dict(db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,)))
    return _issue(row)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest) -> TokenOut:
    email = payload.email.strip().lower()
    row = db.fetch_one("SELECT * FROM users WHERE email = ?", (email,))
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    db.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (db.utcnow(), row["id"]))
    return _issue(dict(row))


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(current_user)) -> UserOut:
    return _public(user)
