from __future__ import annotations

import bcrypt

def hash_password(password: str) -> str:
    """
    Hash a plaintext password using a safe algorithm (bcrypt via passlib).

    Security: this function MUST NOT log plaintext password.
    """

    # bcrypt works on bytes; never log plaintext password.
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify plaintext password against stored password_hash.

    Security: this function MUST NOT log plaintext password or password_hash.
    """

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False

