from typing import Literal, Union

from pydantic import BaseModel

UserId = Union[int, str]


class UserPublic(BaseModel):
    """
    Public user view used in auth responses and request.state.user.

    IMPORTANT: Never include password_hash, password, or secrets here.
    """

    id: UserId
    email: str
    is_admin: bool


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    ok: bool
    user: UserPublic


class LogoutResponse(BaseModel):
    ok: bool


class AdminCreateUserRequest(BaseModel):
    """
    Admin-only create user request (no public register flow).

    Note: No secrets/token fields are included here to avoid leaking them.
    """

    email: str
    password: str
    is_admin: bool = False


class AdminCreateUserResponse(BaseModel):
    ok: bool
    user: UserPublic

