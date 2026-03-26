import asyncio
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from config import settings

try:
    import asyncpg
except Exception:  # pragma: no cover
    asyncpg = None


_pool: Optional["asyncpg.Pool"] = None
_pool_lock = asyncio.Lock()


_SECRET_PATTERNS = [
    # OpenAI API keys (common prefix)
    r"sk-[A-Za-z0-9]{20,}",
    # Gemini / Google API keys (common prefix)
    r"AIza[0-9A-Za-z\-_]{20,}",
]


def _redact_secrets(value: str) -> str:
    if not value:
        return value
    out = value
    for pat in _SECRET_PATTERNS:
        out = re.sub(pat, "[REDACTED]", out)
    return out


def new_request_id() -> str:
    return str(uuid.uuid4())


async def init_db_pool() -> None:
    """
    Init DB pool if enabled.
    Safe to call multiple times.
    """
    global _pool
    if not settings.LOG_DB_ENABLED or not settings.LOG_DB_DSN:
        return

    if asyncpg is None:
        # Dependency not installed yet; keep app working.
        return

    async with _pool_lock:
        if _pool is not None:
            return
        _pool = await asyncpg.create_pool(
            dsn=settings.LOG_DB_DSN,
            min_size=1,
            max_size=5,
            command_timeout=10,
        )

        await ensure_tables()


async def ensure_tables() -> None:
    if asyncpg is None or _pool is None:
        return

    await _pool.execute(
        """
        CREATE TABLE IF NOT EXISTS request_logs (
            id BIGSERIAL PRIMARY KEY,
            request_id TEXT NOT NULL,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            client_ip TEXT,
            user_agent TEXT,
            status_code SMALLINT,
            latency_ms INTEGER,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    await _pool.execute(
        "CREATE INDEX IF NOT EXISTS idx_request_logs_request_id ON request_logs (request_id);"
    )
    await _pool.execute(
        "CREATE INDEX IF NOT EXISTS idx_request_logs_created_at ON request_logs (created_at DESC);"
    )


async def log_request_to_db(
    *,
    request_id: str,
    method: str,
    path: str,
    client_ip: Optional[str],
    user_agent: Optional[str],
    status_code: int,
    latency_ms: int,
    error_message: Optional[str],
) -> None:
    """
    Insert a request log row.
    This should be called in a background task so it doesn't block responses.
    """
    if asyncpg is None or _pool is None:
        return

    # Guard rails: avoid storing overly large strings.
    path = (path or "")[:1024]
    ua = (user_agent or "")[:300]
    err = (error_message or "")[:1000] if error_message else None

    # Redact secrets from error messages.
    if err:
        err = _redact_secrets(err)

    try:
        await _pool.execute(
            """
            INSERT INTO request_logs (
                request_id, method, path, client_ip, user_agent, status_code, latency_ms, error_message
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            request_id,
            method,
            path,
            client_ip,
            ua or None,
            status_code,
            latency_ms,
            err,
        )
    except Exception:
        # Never break the main API flow if logging fails.
        return

