"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import db
from .security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def _user_from_credentials(creds: Optional[HTTPAuthorizationCredentials]) -> Optional[dict]:
    if not creds or not creds.credentials:
        return None
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please sign in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    row = db.fetch_one("SELECT * FROM users WHERE id = ?", (payload.get("sub"),))
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return dict(row)


def current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> dict:
    user = _user_from_credentials(creds)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def optional_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> Optional[dict]:
    return _user_from_credentials(creds)


def owned_paper(paper_id: str, user: dict) -> dict:
    row = db.fetch_one("SELECT * FROM papers WHERE id = ?", (paper_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Paper not found")
    if row["user_id"] != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You do not have access to this paper")
    return dict(row)
