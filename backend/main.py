import asyncio
import time
import uuid
from typing import Optional

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from routes.news import router as news_router
from routes.auth import router as auth_router
from config import settings

from services.request_db_logger import init_db_pool, log_request_to_db, new_request_id
from services.request_context import set_request_id, get_request_id
from services.app_logger import logger
from services.auth_store import ensure_tables as ensure_auth_tables, seed_admin_if_missing

app = FastAPI(
    title="News Aggregator API",
    description="API for Vietnamese news aggregation and summarization",
    version="1.0.0",
)

# CORS Configuration
# - In production, keep a strict allow-list.
# - In local dev, allow localhost/127.0.0.1 on any port so Next.js can run on 3000/3002/etc.
frontend_urls = getattr(settings, "FRONTEND_URLS", [settings.FRONTEND_URL])
is_local_dev = any(
    u.startswith("http://localhost") or u.startswith("http://127.0.0.1")
    for u in frontend_urls
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[] if is_local_dev else frontend_urls,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$" if is_local_dev else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(news_router)
app.include_router(auth_router)


@app.on_event("startup")
async def _init_logging_db() -> None:
    # Initialize DB logging pool + ensure tables (no-op when disabled).
    try:
        await asyncio.wait_for(init_db_pool(), timeout=8)
    except Exception:
        pass

    # Initialize auth session store schema + seed admin (if env provided).
    # Must be safe even when auth env vars are missing.
    try:
        await asyncio.wait_for(ensure_auth_tables(), timeout=8)
    except Exception:
        pass
    try:
        await asyncio.wait_for(
            seed_admin_if_missing(settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD_HASH),
            timeout=8,
        )
    except Exception:
        # Do not crash the API startup if auth seeding fails.
        pass


@app.middleware("http")
async def request_db_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    start = time.perf_counter()

    # Set request id in ContextVar for correlation across async steps.
    ctx_token = set_request_id(request_id)

    # Prefer proxy-provided IP if present.
    xff = request.headers.get("x-forwarded-for")
    client_ip: Optional[str] = None
    if xff:
        client_ip = xff.split(",")[0].strip()[:128]
    elif request.client and request.client.host:
        client_ip = request.client.host[:128]

    user_agent = request.headers.get("user-agent", "")

    try:
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Ensure correlation id is visible to the client.
        response.headers["X-Request-ID"] = request_id

        # Log request summary at INFO level (does not read body — safe for streaming).
        logger.info(
            "%s %s %s %dms",
            request.method,
            str(request.url.path),
            response.status_code,
            latency_ms,
            extra={
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "client_ip": client_ip,
                "request_id": request_id,
            },
        )

        asyncio.create_task(
            log_request_to_db(
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                client_ip=client_ip,
                user_agent=user_agent,
                status_code=response.status_code,
                latency_ms=latency_ms,
                error_message=None,
            )
        )
        return response
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Log error with traceback + correlation fields.
        logger.error(
            "Unhandled exception: %s %s — %s",
            request.method,
            str(request.url.path),
            exc,
            exc_info=True,
            extra={
                "method": request.method,
                "path": str(request.url.path),
                "latency_ms": latency_ms,
                "client_ip": client_ip,
                "request_id": request_id,
            },
        )

        asyncio.create_task(
            log_request_to_db(
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                client_ip=client_ip,
                user_agent=user_agent,
                status_code=500,
                latency_ms=latency_ms,
                error_message=str(exc)[:1000],
            )
        )
        raise
    finally:
        # Reset ContextVar to avoid leak between requests in the same thread/task.
        from contextvars import copy_context  # noqa: F401 – just ensure reset happens
        try:
            from services.request_context import request_id_var
            request_id_var.reset(ctx_token)
        except Exception:
            pass


@app.get("/")
async def root():
    return {
        "message": "News Aggregator API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def run():
    """
    Start the FastAPI backend using configuration from settings.

    This function is used both for local development and when the backend is
    started as a bundled binary for the desktop app.
    """
    import uvicorn

    uvicorn.run(
        app,
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
    )


if __name__ == "__main__":
    run()
