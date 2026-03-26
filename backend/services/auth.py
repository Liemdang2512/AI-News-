from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, Request

from config import settings
from services.auth_password import verify_password
from services.auth_store import create_session, get_user_by_email, revoke_session
from services.auth_types import UserPublic

# Cookie/session contract constants
SESSION_COOKIE_NAME: str = getattr(settings, "AUTH_SESSION_COOKIE_NAME", "session_id")


class CookieDict(dict[str, Any]):
    """
    Minimal cookie options dict used by routes to call `response.set_cookie(...)`.
    """


async def login(email: str, password: str) -> tuple[UserPublic, CookieDict]:
    """
    Auth service contract.

    Implementation will be completed in Wave 1 Task 02.
    """

    email_norm = (email or "").strip().lower()
    if not email_norm:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_row = await get_user_by_email(email_norm)
    if not user_row:
        # Generic error to avoid leaking whether email exists.
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id, password_hash, is_admin = user_row
    try:
        ok = verify_password(password, password_hash)
    except Exception:
        ok = False

    if not ok:
        raise HTTPException(status_code=401, detail="Unauthorized")

    ttl_sec = int(getattr(settings, "AUTH_SESSION_TTL_SEC", 60 * 60 * 24 * 7))
    session_id = await create_session(user_id=user_id, ttl_sec=ttl_sec)

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_sec)
    cookie: CookieDict = CookieDict(
        value=session_id,
        httponly=True,
        secure=bool(getattr(settings, "AUTH_COOKIE_SECURE", False)),
        samesite=getattr(settings, "AUTH_COOKIE_SAMESITE", "lax"),
        max_age=ttl_sec,
        expires=expires_at,
        path="/",
    )

    return UserPublic(id=user_id, email=email_norm, is_admin=is_admin), cookie


async def logout(session_id: str | None) -> CookieDict:
    """
    Auth service contract.

    Implementation will be completed in Wave 1 Task 02.
    """

    await revoke_session(session_id)

    # Expire cookie on client side.
    expires_at = datetime.fromtimestamp(0, tz=timezone.utc)
    cookie: CookieDict = CookieDict(
        value="",
        httponly=True,
        secure=bool(getattr(settings, "AUTH_COOKIE_SECURE", False)),
        samesite=getattr(settings, "AUTH_COOKIE_SAMESITE", "lax"),
        max_age=0,
        expires=expires_at,
        path="/",
    )
    return cookie


async def get_current_user(request: Request) -> UserPublic | None:
    """
    Dependency stub: returns None for now.

    Wave 2 Task 00 will replace this with real cookie->session validation.
    """

    _ = (request, HTTPException)  # keep lint happy for unused imports in stub
    return None

