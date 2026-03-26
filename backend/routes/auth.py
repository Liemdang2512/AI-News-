from __future__ import annotations

import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from services.auth import get_current_user, login as auth_login, logout as auth_logout, SESSION_COOKIE_NAME
from services.auth_password import hash_password
from services.auth_store import create_user
from services.auth_types import (
    AdminCreateUserRequest,
    AdminCreateUserResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    UserPublic,
)

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/auth/me", response_model=UserPublic)
async def me_endpoint(current_user: Optional[UserPublic] = Depends(get_current_user)):
    """
    Return the currently authenticated user based on session cookie.
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return current_user


@router.post("/auth/login", response_model=LoginResponse)
async def login_endpoint(payload: LoginRequest, response: Response):
    """
    Wave 1 Task 00: endpoint skeleton.

    Wave 1 Task 02 will complete the full implementation:
    - verify password
    - create server-side session
    - set HttpOnly cookie `session_id`
    """

    # Delegate to auth service (implemented in Wave 1 Task 02)
    user, cookie = await auth_login(payload.email, payload.password)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=str(cookie.get("value", "")),
        httponly=cookie.get("httponly", True),
        secure=cookie.get("secure", False),
        samesite=cookie.get("samesite", "lax"),
        max_age=cookie.get("max_age"),
        expires=cookie.get("expires"),
        path=cookie.get("path", "/"),
    )
    return LoginResponse(ok=True, user=user)


@router.post("/auth/logout", response_model=LogoutResponse)
async def logout_endpoint(request: Request, response: Response):
    """
    Wave 1 Task 00: endpoint skeleton.

    Wave 1 Task 02 will complete the full implementation:
    - revoke/delete session in the store
    - clear cookie on the client
    """

    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    cookie_clear = await auth_logout(session_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=str(cookie_clear.get("value", "")),
        httponly=cookie_clear.get("httponly", True),
        secure=cookie_clear.get("secure", False),
        samesite=cookie_clear.get("samesite", "lax"),
        max_age=cookie_clear.get("max_age", 0),
        expires=cookie_clear.get("expires"),
        path=cookie_clear.get("path", "/"),
    )
    return LogoutResponse(ok=True)


@router.post("/admin/users", response_model=AdminCreateUserResponse)
async def admin_create_user_endpoint(
    payload: AdminCreateUserRequest,
    response: Response,  # kept for future cookie/session updates
    current_user: Optional[UserPublic] = Depends(get_current_user),
    bootstrap_token: Optional[str] = Header(None),
):
    """
    Wave 1 Task 00: protected endpoint skeleton.

    Wave 1 Task 02 will add:
    - consistent 401/403 errors
    - admin checks and password hashing
    - optional bootstrap token skeleton
    """

    # Dependency currently returns None (Wave 2 Task 00 replaces it).
    if current_user is None:
        expected_bootstrap = os.getenv("ADMIN_BOOTSTRAP_TOKEN", "").strip()
        if expected_bootstrap and bootstrap_token and bootstrap_token == expected_bootstrap and payload.is_admin:
            # Bootstrap path (very first setup). Do not log/store/display the token.
            password_hash = hash_password(payload.password)
            user = await create_user(payload.email, password_hash, is_admin=True)
            return AdminCreateUserResponse(ok=True, user=user)

        raise HTTPException(status_code=401, detail="Unauthorized")

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    password_hash = hash_password(payload.password)
    user = await create_user(payload.email, password_hash, is_admin=bool(payload.is_admin))
    return AdminCreateUserResponse(ok=True, user=user)

