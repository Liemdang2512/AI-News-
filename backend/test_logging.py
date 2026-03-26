"""
Test scaffold for logging middleware (Phase 02 - Wave 00).

These tests verify:
  - X-Request-ID header propagation (Wave 01 middleware)
  - SSE streaming endpoint accessible + correct media_type
  - NDJSON streaming endpoint accessible + correct media_type + empty-input error line
  - redact_secrets helper redacts Bearer tokens and key= query params (Wave 01)

Tests for X-Request-ID and redact_secrets are expected to run RED until
Wave 01 implements the middleware and app_logger service.
"""
import sys
import os

# Ensure the backend package is on the path when pytest is run from anywhere.
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app, raise_server_exceptions=False)

TODAY = "26/03/2026"


# ---------------------------------------------------------------------------
# 1. X-Request-ID round-trip on /health
# ---------------------------------------------------------------------------

def test_request_has_x_request_id_health():
    """
    GET /health must return X-Request-ID header.
    When the client provides X-Request-ID the server must echo it back.
    """
    # Without client header: server should generate one.
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in {k.lower() for k in response.headers}, (
        "Response is missing X-Request-ID header"
    )
    assert response.headers.get("x-request-id") or response.headers.get("X-Request-ID"), (
        "X-Request-ID header must be a non-empty string"
    )

    # With client header: server must echo the same value.
    sent_id = "test-123"
    response2 = client.get("/health", headers={"X-Request-ID": sent_id})
    echoed = (
        response2.headers.get("x-request-id")
        or response2.headers.get("X-Request-ID")
        or ""
    )
    assert echoed == sent_id, (
        f"Expected echoed X-Request-ID '{sent_id}', got '{echoed}'"
    )


# ---------------------------------------------------------------------------
# 2. SSE stream: /api/rss/fetch_stream
# ---------------------------------------------------------------------------

def test_sse_stream_has_x_request_id_and_event_format():
    """
    POST /api/rss/fetch_stream with empty rss_urls should:
    - Return Content-Type: text/event-stream
    - Include X-Request-ID header
    - First stream line starts with 'data: '
    """
    payload = {
        "rss_urls": [],
        "date": TODAY,
        "time_range": "0h00 đến 23h59",
    }

    with client.stream("POST", "/api/rss/fetch_stream", json=payload) as response:
        assert "text/event-stream" in response.headers.get("content-type", ""), (
            f"Expected text/event-stream content-type, got {response.headers.get('content-type')}"
        )

        # X-Request-ID must be present.
        rid = (
            response.headers.get("x-request-id")
            or response.headers.get("X-Request-ID")
        )
        assert rid, "SSE response missing X-Request-ID header"

        # Read at least one chunk from the stream.
        first_line = ""
        for chunk in response.iter_lines():
            stripped = chunk.strip()
            if stripped:
                first_line = stripped
                break

    assert first_line.startswith("data: "), (
        f"Expected first non-empty SSE line to start with 'data: ', got: {first_line!r}"
    )


# ---------------------------------------------------------------------------
# 3. NDJSON stream: /api/articles/summarize_stream
# ---------------------------------------------------------------------------

def test_ndjson_stream_has_x_request_id_and_error_line():
    """
    POST /api/articles/summarize_stream with empty urls/articles should:
    - Return Content-Type: application/x-ndjson
    - Include X-Request-ID header
    - First JSON line: {"type": "error", ...} with message containing 'No articles selected'
    """
    import json

    payload = {"urls": [], "articles": []}

    with client.stream("POST", "/api/articles/summarize_stream", json=payload) as response:
        ct = response.headers.get("content-type", "")
        assert "application/x-ndjson" in ct, (
            f"Expected application/x-ndjson content-type, got {ct}"
        )

        rid = (
            response.headers.get("x-request-id")
            or response.headers.get("X-Request-ID")
        )
        assert rid, "NDJSON response missing X-Request-ID header"

        first_json_line = None
        for chunk in response.iter_lines():
            stripped = chunk.strip()
            if stripped:
                first_json_line = stripped
                break

    assert first_json_line is not None, "No data received from NDJSON stream"

    parsed = json.loads(first_json_line)
    assert parsed.get("type") == "error", (
        f"Expected first NDJSON line to have type='error', got: {parsed}"
    )
    assert "No articles selected" in parsed.get("message", ""), (
        f"Expected message to contain 'No articles selected', got: {parsed.get('message')}"
    )


# ---------------------------------------------------------------------------
# 4. redact_secrets helper
# ---------------------------------------------------------------------------

def test_redact_secrets_removes_api_key_tokens():
    """
    services.app_logger.redact_secrets must scrub:
    - Bearer tokens  (e.g., 'Bearer sk-test-123')
    - key= query params  (e.g., '?key=AIza-test-456')
    """
    try:
        from services.app_logger import redact_secrets
    except ImportError:
        pytest.fail(
            "services.app_logger.redact_secrets not found — "
            "implement app_logger.py in Wave 01 to make this test GREEN"
        )

    bearer_token = "Bearer sk-test-123"
    key_param = "?key=AIza-test-456"
    sample = f"Authorization: {bearer_token} and url https://api.example.com/v1{key_param}"

    result = redact_secrets(sample)

    assert bearer_token not in result, (
        f"redact_secrets did not remove Bearer token from output: {result!r}"
    )
    assert "AIza-test-456" not in result, (
        f"redact_secrets did not remove key= param value from output: {result!r}"
    )
