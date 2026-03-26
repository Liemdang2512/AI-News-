from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from config import settings
from services.auth_types import UserPublic

try:
    import asyncpg  # type: ignore
except Exception:  # pragma: no cover
    asyncpg = None


USER_TABLE_NAME = "users"
SESSION_TABLE_NAME = "sessions"


# ---------------------------------------------------------------------------
# In-memory fallback store (used for tests and dev)
# ---------------------------------------------------------------------------
@dataclass
class _UserRow:
    id: int
    email: str
    password_hash: str
    is_admin: bool
    created_at: datetime


@dataclass
class _SessionRow:
    session_id: str
    user_id: int
    expires_at: datetime
    revoked_at: Optional[datetime]


_mem_lock = asyncio.Lock()
_mem_users_by_email: dict[str, _UserRow] = {}
_mem_users_by_id: dict[int, _UserRow] = {}
_mem_sessions_by_id: dict[str, _SessionRow] = {}
_mem_user_id_seq: int = 1


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _storage_mode() -> str:
    return (getattr(settings, "AUTH_SESSION_STORAGE", "memory") or "memory").lower()


# Ensure auth store is initialized even when FastAPI lifespan/startup events
# don't run in unit tests (some test patterns instantiate TestClient directly).
_init_lock = asyncio.Lock()
_initialized = False


async def _ensure_store_initialized() -> None:
    global _initialized
    if _initialized:
        return
    async with _init_lock:
        if _initialized:
            return
        await ensure_tables()
        try:
            await seed_admin_if_missing(settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD_HASH)
        except Exception:
            # Never crash app flow due to auth bootstrap issues.
            pass
        _initialized = True


# ---------------------------------------------------------------------------
# Optional Postgres store (asyncpg)
# ---------------------------------------------------------------------------
_pool: Optional["asyncpg.Pool"] = None
_pool_lock = asyncio.Lock()


async def _get_pool() -> Optional["asyncpg.Pool"]:
    global _pool
    if _pool is not None:
        return _pool

    if asyncpg is None:
        return None

    dsn = getattr(settings, "AUTH_DB_DSN", "") or getattr(settings, "LOG_DB_DSN", "")
    if not dsn:
        return None

    async with _pool_lock:
        if _pool is not None:
            return _pool
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=5,
            command_timeout=10,
        )
    return _pool


def _user_public_from_row(u: _UserRow) -> UserPublic:
    return UserPublic(id=u.id, email=u.email, is_admin=u.is_admin)


# ---------------------------------------------------------------------------
# Public API (used by services/auth.py)
# ---------------------------------------------------------------------------
async def ensure_tables() -> None:
    """
    Ensure DB schema exists for auth store.

    For memory mode: no-op.
    For postgres mode: create tables via asyncpg.
    """

    if _storage_mode() != "postgres":
        return

    pool = await _get_pool()
    if pool is None:
        # If DSN isn't configured, fall back silently to memory store.
        return

    await pool.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {USER_TABLE_NAME} (
            id BIGSERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    await pool.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SESSION_TABLE_NAME} (
            session_id TEXT PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES {USER_TABLE_NAME}(id) ON DELETE CASCADE,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked_at TIMESTAMPTZ NULL
        );
        """
    )
    await pool.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{SESSION_TABLE_NAME}_user_id ON {SESSION_TABLE_NAME}(user_id);"
    )


async def seed_admin_if_missing(admin_email: str, admin_password_hash: str) -> None:
    """
    Seed admin user from env values (admin_password_hash is already hashed).

    Security: MUST NOT log plaintext password/hash.
    """

    admin_email = (admin_email or "").strip().lower()
    admin_password_hash = (admin_password_hash or "").strip()
    if not admin_email or not admin_password_hash:
        return

    global _mem_user_id_seq

    if _storage_mode() != "postgres":
        async with _mem_lock:
            if admin_email in _mem_users_by_email:
                return
            uid = _mem_user_id_seq
            _mem_user_id_seq += 1
            row = _UserRow(
                id=uid,
                email=admin_email,
                password_hash=admin_password_hash,
                is_admin=True,
                created_at=_now_utc(),
            )
            _mem_users_by_email[admin_email] = row
            _mem_users_by_id[uid] = row
        return

    pool = await _get_pool()
    if pool is None:
        # No DB configured => fall back to in-memory seed.
        async with _mem_lock:
            if admin_email in _mem_users_by_email:
                return
            uid = _mem_user_id_seq
            _mem_user_id_seq += 1
            row = _UserRow(
                id=uid,
                email=admin_email,
                password_hash=admin_password_hash,
                is_admin=True,
                created_at=_now_utc(),
            )
            _mem_users_by_email[admin_email] = row
            _mem_users_by_id[uid] = row
        return

    # Postgres: seed if missing.
    existing = await pool.fetchrow(
        f"SELECT id FROM {USER_TABLE_NAME} WHERE email=$1",
        admin_email,
    )
    if existing:
        return

    await pool.execute(
        f"""
        INSERT INTO {USER_TABLE_NAME} (email, password_hash, is_admin)
        VALUES ($1, $2, TRUE)
        """,
        admin_email,
        admin_password_hash,
    )


async def get_user_by_email(email: str) -> Optional[tuple[int, str, bool]]:
    """
    Return (user_id, password_hash, is_admin) for login.
    """

    await _ensure_store_initialized()

    email = (email or "").strip().lower()
    if not email:
        return None

    if _storage_mode() != "postgres":
        async with _mem_lock:
            row = _mem_users_by_email.get(email)
            if not row:
                return None
            return row.id, row.password_hash, row.is_admin

    pool = await _get_pool()
    if pool is None:
        return None

    row = await pool.fetchrow(
        f"SELECT id, password_hash, is_admin FROM {USER_TABLE_NAME} WHERE email=$1",
        email,
    )
    if not row:
        return None
    return row["id"], row["password_hash"], bool(row["is_admin"])


async def create_user(email: str, password_hash: str, *, is_admin: bool = False) -> UserPublic:
    """
    Create a user with already-hashed password.
    """

    await _ensure_store_initialized()

    email_norm = (email or "").strip().lower()
    if not email_norm:
        raise ValueError("email required")

    global _mem_user_id_seq

    if _storage_mode() != "postgres":
        async with _mem_lock:
            if email_norm in _mem_users_by_email:
                # Keep behavior simple: treat as already exists.
                return _user_public_from_row(_mem_users_by_email[email_norm])

            uid = _mem_user_id_seq
            _mem_user_id_seq += 1
            row = _UserRow(
                id=uid,
                email=email_norm,
                password_hash=password_hash,
                is_admin=is_admin,
                created_at=_now_utc(),
            )
            _mem_users_by_email[email_norm] = row
            _mem_users_by_id[uid] = row
            return _user_public_from_row(row)

    pool = await _get_pool()
    if pool is None:
        # If DB isn't available, fall back to memory.
        async with _mem_lock:
            if email_norm in _mem_users_by_email:
                return _user_public_from_row(_mem_users_by_email[email_norm])
            uid = _mem_user_id_seq
            _mem_user_id_seq += 1
            row = _UserRow(
                id=uid,
                email=email_norm,
                password_hash=password_hash,
                is_admin=is_admin,
                created_at=_now_utc(),
            )
            _mem_users_by_email[email_norm] = row
            _mem_users_by_id[uid] = row
            return _user_public_from_row(row)

    row = await pool.fetchrow(
        f"SELECT id, email, is_admin FROM {USER_TABLE_NAME} WHERE email=$1",
        email_norm,
    )
    if row:
        return UserPublic(id=row["id"], email=row["email"], is_admin=bool(row["is_admin"]))

    inserted = await pool.fetchrow(
        f"""
        INSERT INTO {USER_TABLE_NAME} (email, password_hash, is_admin)
        VALUES ($1, $2, $3)
        RETURNING id, email, is_admin
        """,
        email_norm,
        password_hash,
        is_admin,
    )
    return UserPublic(id=inserted["id"], email=inserted["email"], is_admin=bool(inserted["is_admin"]))


async def create_session(user_id: int, ttl_sec: int) -> str:
    """
    Create server-side session by session_id.
    """

    await _ensure_store_initialized()

    session_id = secrets.token_urlsafe(64)
    expires_at = _now_utc() + timedelta(seconds=int(ttl_sec))

    if _storage_mode() != "postgres":
        async with _mem_lock:
            _mem_sessions_by_id[session_id] = _SessionRow(
                session_id=session_id,
                user_id=user_id,
                expires_at=expires_at,
                revoked_at=None,
            )
        return session_id

    pool = await _get_pool()
    if pool is None:
        async with _mem_lock:
            _mem_sessions_by_id[session_id] = _SessionRow(
                session_id=session_id,
                user_id=user_id,
                expires_at=expires_at,
                revoked_at=None,
            )
        return session_id

    await pool.execute(
        f"""
        INSERT INTO {SESSION_TABLE_NAME} (session_id, user_id, expires_at, revoked_at)
        VALUES ($1, $2, $3, NULL)
        """,
        session_id,
        user_id,
        expires_at,
    )
    return session_id


async def get_user_by_session_id(session_id: str | None) -> Optional[UserPublic]:
    """
    Validate session and return user for protected endpoints.
    """

    await _ensure_store_initialized()

    if not session_id:
        return None

    if _storage_mode() != "postgres":
        async with _mem_lock:
            s = _mem_sessions_by_id.get(session_id)
            if not s:
                return None
            if s.revoked_at is not None:
                return None
            if s.expires_at <= _now_utc():
                return None
            u = _mem_users_by_id.get(s.user_id)
            if not u:
                return None
            return _user_public_from_row(u)

    pool = await _get_pool()
    if pool is None:
        return None

    row = await pool.fetchrow(
        f"""
        SELECT u.id, u.email, u.is_admin
        FROM {SESSION_TABLE_NAME} s
        JOIN {USER_TABLE_NAME} u ON s.user_id = u.id
        WHERE s.session_id=$1
          AND s.revoked_at IS NULL
          AND s.expires_at > NOW()
        """,
        session_id,
    )
    if not row:
        return None
    return UserPublic(id=row["id"], email=row["email"], is_admin=bool(row["is_admin"]))


async def revoke_session(session_id: str | None) -> None:
    """
    Revoke/expire current session.
    """

    await _ensure_store_initialized()

    if not session_id:
        return

    if _storage_mode() != "postgres":
        async with _mem_lock:
            s = _mem_sessions_by_id.get(session_id)
            if not s:
                return
            if s.revoked_at is None:
                s.revoked_at = _now_utc()
        return

    pool = await _get_pool()
    if pool is None:
        async with _mem_lock:
            s = _mem_sessions_by_id.get(session_id)
            if not s:
                return
            if s.revoked_at is None:
                s.revoked_at = _now_utc()
        return

    await pool.execute(
        f"""
        UPDATE {SESSION_TABLE_NAME}
        SET revoked_at = NOW()
        WHERE session_id=$1
          AND revoked_at IS NULL
        """,
        session_id,
    )

