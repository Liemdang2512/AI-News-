"""
ContextVar-based request-id storage for correlation across async tasks.

Usage:
    from services.request_context import get_request_id, set_request_id

    # In middleware (before calling next):
    token = set_request_id(request_id)

    # Later in any async handler / service:
    rid = get_request_id()  # returns the request id or None
"""
from contextvars import ContextVar, Token
from typing import Optional

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id_var", default=None)


def get_request_id() -> Optional[str]:
    """Return the current request id, or None if not set."""
    return request_id_var.get()


def set_request_id(value: str) -> Token:
    """
    Set the request id for the current context.

    Returns the ContextVar token so callers can reset it if needed:
        token = set_request_id(rid)
        ...
        request_id_var.reset(token)
    """
    return request_id_var.set(value)
