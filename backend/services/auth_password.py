from __future__ import annotations

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using a safe algorithm (bcrypt via passlib).

    Security: this function MUST NOT log plaintext password.
    """

    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify plaintext password against stored password_hash.

    Security: this function MUST NOT log plaintext password or password_hash.
    """

    return _pwd_context.verify(password, password_hash)

