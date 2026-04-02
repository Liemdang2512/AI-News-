import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    # Timeout HTTP cho generateContent (giây) — bài dài / mạng chậm
    GEMINI_REQUEST_TIMEOUT: float = float(os.getenv("GEMINI_REQUEST_TIMEOUT", "120"))

    # OpenAI / GPT
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # AI provider đang dùng: "gemini" hoặc "openai"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")
    # Frontend origins allowed for CORS. Supports comma-separated list.
    # Examples:
    #   FRONTEND_URL=http://localhost:3000
    #   FRONTEND_URL=http://localhost:3000,http://localhost:3002
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    FRONTEND_URLS: list[str] = [u.strip() for u in FRONTEND_URL.split(",") if u.strip()]
    # Backend server configuration
    # Default host is 0.0.0.0 to preserve existing behaviour where the service
    # is reachable from other network interfaces (e.g. Docker, LAN).
    # Desktop/Electron builds can override this via BACKEND_HOST=127.0.0.1
    # if they only need local access.
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    # Railway sets PORT; BACKEND_PORT takes precedence for local/Docker use.
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT") or os.getenv("PORT", "8000"))

    # Structured logging settings
    # - LOG_LEVEL: logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL); default INFO
    # - LOG_JSON: if "true" (case-insensitive), emit logs as JSON lines; default false (plain text)
    # - LOG_FILE: if non-empty, also write logs to this file path (append mode); default "" (stdout only)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_JSON: bool = os.getenv("LOG_JSON", "false").lower() in ("1", "true", "yes", "on")
    LOG_FILE: str = os.getenv("LOG_FILE", "")

    # DB logging (Postgres on Railway)
    # - LOG_DB_ENABLED=false: keep current behaviour (no DB)
    # - LOG_DB_DSN: set to Railway Postgres DSN (e.g. postgresql://user:pass@host:5432/dbname?sslmode=require)
    LOG_DB_ENABLED: bool = os.getenv("LOG_DB_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    LOG_DB_DSN: str = os.getenv("LOG_DB_DSN", "")
    LOG_DB_REQUEST_TIMEOUT_SEC: float = float(os.getenv("LOG_DB_REQUEST_TIMEOUT_SEC", "10"))

    # Crawl/summarizer concurrency tuning (important for server RAM)
    SUMMARIZER_MAX_CONCURRENCY: int = int(os.getenv("SUMMARIZER_MAX_CONCURRENCY", "4"))
    SUMMARIZER_BATCH_SIZE: int = int(os.getenv("SUMMARIZER_BATCH_SIZE", "4"))

    # -----------------------------------------------------------------------
    # Auth (cookie session)
    # -----------------------------------------------------------------------
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "")
    # Expected to already be a hashed password (seeded from CI/.env).
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")

    # Choose storage backend for session/user auth.
    # - "memory": in-process store (good for tests/dev)
    # - "postgres": asyncpg store (requires LOG_DB_DSN or AUTH_DB_DSN reuse)
    AUTH_DB_DSN: str = os.getenv("AUTH_DB_DSN", "")
    AUTH_SESSION_STORAGE: str = os.getenv("AUTH_SESSION_STORAGE", "memory").lower()

    AUTH_SESSION_TTL_SEC: int = int(os.getenv("AUTH_SESSION_TTL_SEC", str(60 * 60 * 24 * 7)))  # 7 days
    AUTH_COOKIE_SECURE: bool = os.getenv("AUTH_COOKIE_SECURE", "false").lower() in ("1", "true", "yes", "on")
    AUTH_COOKIE_SAMESITE: str = os.getenv("AUTH_COOKIE_SAMESITE", "lax").lower()
    AUTH_SESSION_COOKIE_NAME: str = os.getenv("AUTH_SESSION_COOKIE_NAME", "session_id")
    
    # RSS Feed Database (from JSON workflow)
    RSS_DATABASE = [
        "https://laodong.vn/rss/thoi-su.rss",
        "https://laodong.vn/rss/the-gioi.rss",
        "https://laodong.vn/rss/xa-hoi.rss",
        "https://laodong.vn/rss/kinh-doanh.rss",
        "https://laodong.vn/rss/phap-luat.rss",
        "https://dantri.com.vn/rss/phap-luat.rss",
        "https://dantri.com.vn/rss/kinh-doanh.rss",
        "https://dantri.com.vn/rss/doi-song.rss",
        "https://dantri.com.vn/rss/the-gioi.rss",
        "https://vtv.vn/rss/xa-hoi.rss",
        "https://vtv.vn/rss/phap-luat.rss",
        "https://vtv.vn/rss/the-gioi.rss",
        "https://vtv.vn/rss/kinh-te.rss",
        "https://hanoimoi.vn/rss/xa-hoi",
        "https://hanoimoi.vn/rss/the-gioi",
        "https://hanoimoi.vn/rss/phap-luat",
        "https://hanoimoi.vn/rss/kinh-te",
        "https://www.sggp.org.vn/rss/xahoi-199.rss",
        "https://www.sggp.org.vn/rss/phapluat-112.rss",
        "https://www.sggp.org.vn/rss/kinhte-89.rss",
        "https://www.sggp.org.vn/rss/thegioi-143.rss",
        "https://www.vietnamplus.vn/rss/kinhte-311.rss",
        "https://www.vietnamplus.vn/rss/thegioi-209.rss",
        "https://www.vietnamplus.vn/rss/xahoi/phapluat-327.rss",
        "https://www.vietnamplus.vn/rss/xahoi-314.rss",
        "https://tienphong.vn/rss/xa-hoi-2.rss",
        "https://tienphong.vn/rss/kinh-te-3.rss",
        "https://tienphong.vn/rss/the-gioi-5.rss",
        "https://tienphong.vn/rss/phap-luat-12.rss",
        "https://vov.vn/rss/the-gioi.rss",
        "https://vov.vn/rss/kinh-te.rss",
        "https://vov.vn/rss/xa-hoi.rss",
        "https://vov.vn/rss/phap-luat.rss",
        "https://baotintuc.vn/the-gioi.rss",
        "https://baotintuc.vn/kinh-te.rss",
        "https://baotintuc.vn/xa-hoi.rss",
        "https://baotintuc.vn/phap-luat.rss",
        "https://tuoitre.vn/rss/phap-luat.rss",
        "https://tuoitre.vn/rss/the-gioi.rss",
        "https://tuoitre.vn/rss/kinh-doanh.rss",
        "https://tuoitre.vn/rss/thoi-su.rss",
        # Báo Nhân Dân (Official source for verification)
        "https://nhandan.vn/rss/kinhte-1185.rss",
        "https://nhandan.vn/rss/phapluat-1287.rss",
        "https://nhandan.vn/rss/xahoi-1211.rss",
        "https://nhandan.vn/rss/thegioi-1231.rss",
    ]


settings = Settings()
