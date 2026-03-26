from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, Request

from config import settings
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

    raise NotImplementedError("auth.login is implemented in the next task")


async def logout(session_id: str | None) -> CookieDict:
    """
    Auth service contract.

    Implementation will be completed in Wave 1 Task 02.
    """

    raise NotImplementedError("auth.logout is implemented in the next task")


async def get_current_user(request: Request) -> UserPublic | None:
    """
    Dependency stub: returns None for now.

    Wave 2 Task 00 will replace this with real cookie->session validation.
    """

    _ = (request, HTTPException)  # keep lint happy for unused imports in stub
    return None

