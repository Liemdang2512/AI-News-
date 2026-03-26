"""
Application logger singleton with JSON / plain-text formatting, file output,
and secret redaction.

Usage:
    from services.app_logger import logger, get_logger, redact_secrets

    logger.info("Request received", extra={"request_id": get_request_id()})

Environment variables (read from settings):
    LOG_LEVEL   – Python logging level name (default: INFO)
    LOG_JSON    – if truthy, emit JSON-lines; otherwise human-readable text
    LOG_FILE    – if non-empty, also write to this file (append mode)
"""
import json
import logging
import os
import re
import sys
from logging import Handler, LogRecord
from typing import Optional

from config import settings
from services.request_context import get_request_id

# ---------------------------------------------------------------------------
# Secret redaction
# ---------------------------------------------------------------------------

_REDACT_PATTERNS = [
    # Bearer <token>  (any token after "Bearer ")
    (re.compile(r"(Bearer\s+)\S+", re.IGNORECASE), r"\1***REDACTED***"),
    # key= or api_key= query-param value
    (re.compile(r"([?&](?:api_?key|key)=)[^&\s]+", re.IGNORECASE), r"\1***REDACTED***"),
    # OpenAI-style keys: sk-...
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}"), "***REDACTED***"),
    # Google/Gemini API keys: AIza...
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{8,}"), "***REDACTED***"),
]


def redact_secrets(value: str) -> str:
    """
    Replace well-known secret patterns in *value* with ***REDACTED***.

    Always returns a str; never raises.
    """
    if not isinstance(value, str):
        try:
            value = str(value)
        except Exception:
            return ""
    try:
        out = value
        for pattern, replacement in _REDACT_PATTERNS:
            out = pattern.sub(replacement, out)
        return out
    except Exception:
        return value


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

class _PlainFormatter(logging.Formatter):
    """Human-readable formatter that injects request_id when present."""

    _FMT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    def __init__(self) -> None:
        super().__init__(fmt=self._FMT, datefmt="%Y-%m-%dT%H:%M:%S")

    def format(self, record: LogRecord) -> str:
        rid = get_request_id()
        if rid:
            record.__dict__.setdefault("request_id", rid)
            # Append request_id to the rendered line.
            base = super().format(record)
            return f"{base} [req={rid}]"
        return super().format(record)


class _JsonFormatter(logging.Formatter):
    """JSON-line formatter — one JSON object per log record."""

    def format(self, record: LogRecord) -> str:
        rid = get_request_id()
        payload: dict = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if rid:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Include any extra fields attached to the record.
        skip = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        for key, val in record.__dict__.items():
            if key not in skip and not key.startswith("_"):
                payload[key] = val
        try:
            return json.dumps(payload, ensure_ascii=False)
        except Exception:
            return json.dumps({"level": "ERROR", "message": "log serialization failed"})


# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

def _build_logger() -> logging.Logger:
    log = logging.getLogger("app-logger")

    level_name = (settings.LOG_LEVEL or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log.setLevel(level)

    # Avoid duplicate handlers on hot-reload.
    if log.handlers:
        return log

    formatter: logging.Formatter = (
        _JsonFormatter() if settings.LOG_JSON else _PlainFormatter()
    )

    # Stdout handler (always present).
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    log.addHandler(stdout_handler)

    # Optional file handler.
    log_file = settings.LOG_FILE or ""
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)

    # Do not propagate to root logger to avoid double-logging.
    log.propagate = False

    return log


logger: logging.Logger = _build_logger()


def get_logger() -> logging.Logger:
    """Return the shared application logger singleton."""
    return logger
