"""
Unit tests for bullet validation and fallback logic covering REQ-002.

Tests are run from the backend/ directory:
    cd backend && python3 -m pytest test_summarizer.py -v

NOTE: Tests 3-5 (test_has_bullet_*) will SKIP before plan 03 adds _has_bullet_content.
Tests 1-2 (test_excerpt_only_fallback_*) PASS immediately as _excerpt_only_fallback exists.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import pytest
from services.summarizer import Summarizer


def test_excerpt_only_fallback_has_bullet():
    """REQ-002: _excerpt_only_fallback always produces a bullet '- ' line."""
    content = "Some content " * 10
    result = Summarizer._excerpt_only_fallback(
        "Title bài viết test",
        "http://x.com/path-to-article",
        "Nguồn test",
        content,
    )
    assert "- " in result, f"Expected '- ' bullet in result, got: {result!r}"
    assert result.startswith("### ["), (
        f"Expected result to start with '### [', got: {result[:30]!r}"
    )


def test_excerpt_only_fallback_empty_content():
    """REQ-002: _excerpt_only_fallback with empty content still produces '- ' bullet."""
    result = Summarizer._excerpt_only_fallback(
        "Tiêu đề bài viết",
        "http://example.com/bai-viet",
        "Nguồn báo",
        "",
    )
    assert "- " in result, (
        f"Expected '- ' bullet even with empty content, got: {result!r}"
    )


def test_has_bullet_valid():
    """REQ-002: _has_bullet_content returns True for summary with a real bullet line.
    WILL SKIP before plan 03 adds _has_bullet_content to Summarizer.
    """
    try:
        result = Summarizer._has_bullet_content(
            "### Title\n**Src**\n\n- Đây là nội dung tóm tắt bài viết dài hơn 20 chars đầy đủ"
        )
        assert result is True, f"Expected True for valid bullet, got: {result!r}"
    except AttributeError:
        pytest.skip("_has_bullet_content not yet implemented (plan 03)")


def test_has_bullet_url_dash_rejected():
    """REQ-002: _has_bullet_content returns False when the dash is followed by a URL path.
    WILL SKIP before plan 03 adds _has_bullet_content to Summarizer.
    """
    try:
        result = Summarizer._has_bullet_content(
            "### Title\nhttps://example.com/path-to-article"
        )
        assert result is False, (
            f"Expected False for URL-dash (not a real bullet), got: {result!r}"
        )
    except AttributeError:
        pytest.skip("_has_bullet_content not yet implemented (plan 03)")


def test_has_bullet_short_bullet_rejected():
    """REQ-002: _has_bullet_content returns False for bullets shorter than 20 chars.
    WILL SKIP before plan 03 adds _has_bullet_content to Summarizer.
    """
    try:
        result = Summarizer._has_bullet_content("- ok")
        assert result is False, (
            f"Expected False for short bullet (< 20 chars after '- '), got: {result!r}"
        )
    except AttributeError:
        pytest.skip("_has_bullet_content not yet implemented (plan 03)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
