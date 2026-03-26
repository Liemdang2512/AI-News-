import os
import sys

# Ensure the backend package is on the path when pytest is run from anywhere.
sys.path.insert(0, os.path.dirname(__file__))

import logging

import pytest
from fastapi.testclient import TestClient

from services.auth_password import hash_password


# ---------------------------------------------------------------------------
# Test env (must be set before importing `main`)
# ---------------------------------------------------------------------------
os.environ["AUTH_SESSION_STORAGE"] = "memory"
os.environ["FRONTEND_URL"] = "http://localhost:3000"

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin-pass"
ADMIN_PASSWORD_HASH = hash_password(ADMIN_PASSWORD)

os.environ["ADMIN_EMAIL"] = ADMIN_EMAIL
os.environ["ADMIN_PASSWORD_HASH"] = ADMIN_PASSWORD_HASH
os.environ["ADMIN_BOOTSTRAP_TOKEN"] = "boot-token"


from main import app  # noqa: E402


client = TestClient(app, raise_server_exceptions=False)


def extract_cookie_value(response, cookie_name: str = "session_id") -> str:
    set_cookie = response.headers.get("set-cookie", "") or ""
    # Example: session_id=abc...; Path=/; HttpOnly; ...
    prefix = f"{cookie_name}="
    if prefix not in set_cookie:
        return ""
    tail = set_cookie.split(prefix, 1)[1]
    return tail.split(";", 1)[0]


def assert_no_secret_in_text(text: str, secret_substrings: list[str]) -> None:
    for s in secret_substrings:
        assert s not in (text or ""), f"Unexpected secret substring found: {s!r}"


def test_health_has_x_request_id():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("x-request-id") or resp.headers.get("X-Request-ID")


def test_login_sets_session_cookie_httpOnly_and_no_password_leak():
    resp = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200

    set_cookie = resp.headers.get("set-cookie", "") or ""
    assert "session_id=" in set_cookie
    assert "HttpOnly" in set_cookie

    # Response body must not include plaintext password or password hash.
    assert resp.text
    assert_no_secret_in_text(resp.text, [ADMIN_PASSWORD, ADMIN_PASSWORD_HASH])

    assert resp.headers.get("x-request-id") or resp.headers.get("X-Request-ID")


def test_logout_invalidate_session_returns_401_for_protected():
    client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    resp_logout = client.post("/api/auth/logout")
    assert resp_logout.status_code in (200, 204)

    resp = client.post(
        "/api/admin/users",
        json={"email": "u2@example.com", "password": "u2-pass", "is_admin": False},
    )
    assert resp.status_code in (401, 403)


def test_admin_requires_auth_401_when_missing_cookie():
    resp = client.post(
        "/api/admin/users",
        json={"email": "u1@example.com", "password": "u1-pass", "is_admin": False},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body.get("detail") == "Unauthorized"


def test_no_secret_leak_in_logs(caplog):
    caplog.set_level(logging.INFO, logger="app-logger")

    client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )

    # Logger should not contain plaintext password, password hash, or bootstrap token.
    assert_no_secret_in_text(caplog.text, [ADMIN_PASSWORD, ADMIN_PASSWORD_HASH, "boot-token"])


def test_cors_credentials_no_wildcard_origin():
    origin = "http://localhost:3000"
    resp = client.get("/health", headers={"Origin": origin})

    # CORSMiddleware should set credentials headers for explicit origin.
    assert resp.headers.get("access-control-allow-credentials") == "true"
    assert resp.headers.get("access-control-allow-origin") == origin
    assert resp.headers.get("access-control-allow-origin") != "*"

