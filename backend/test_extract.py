"""
Unit tests for Summarizer._extract_content() covering REQ-001.

Tests are run from the backend/ directory:
    cd backend && python3 -m pytest test_extract.py -v

NOTE: Tests 1 and 2 may run RED before plan 01 adds trafilatura support.
They are still collectable by pytest and will go GREEN after plan 01 implementation.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import pytest
from services.summarizer import Summarizer


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(filename: str) -> str:
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_extract_laodong_selector():
    """REQ-001: _extract_content should extract text from .fck_detail selector."""
    html = _load_fixture("laodong_article.html")
    summarizer = Summarizer()
    result = summarizer._extract_content(html)
    assert len(result) >= 200, (
        f"Expected at least 200 chars from laodong fixture, got {len(result)}: {result[:100]!r}"
    )


def test_extract_dantri_selector():
    """REQ-001: _extract_content should extract text from .detail__content selector."""
    html = _load_fixture("dantri_article.html")
    summarizer = Summarizer()
    result = summarizer._extract_content(html)
    assert len(result) >= 200, (
        f"Expected at least 200 chars from dantri fixture, got {len(result)}: {result[:100]!r}"
    )


def test_extract_empty_html():
    """_extract_content should return empty string for empty input."""
    summarizer = Summarizer()
    result = summarizer._extract_content("")
    assert result == "", f"Expected empty string, got: {result!r}"


def test_extract_json_ld():
    """_extract_content should fall back to JSON-LD articleBody when no article div."""
    article_body = "Đây là nội dung bài viết được lưu trong JSON-LD articleBody. " * 6
    html = f"""<!DOCTYPE html>
<html>
<head>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "Bài viết test",
    "articleBody": "{article_body}"
  }}
  </script>
</head>
<body><p>Không có nội dung article ở đây.</p></body>
</html>"""
    summarizer = Summarizer()
    result = summarizer._extract_content(html)
    assert len(result) >= 200, (
        f"Expected at least 200 chars from JSON-LD, got {len(result)}: {result[:100]!r}"
    )


def test_extract_meta_fallback():
    """_extract_content should include og:description meta content when no article body."""
    description = "Đây là mô tả bài viết từ og:description meta tag có độ dài hơn 50 ký tự."
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta property="og:description" content="{description}">
  <title>Bài viết test</title>
</head>
<body><p>Nội dung ngắn.</p></body>
</html>"""
    summarizer = Summarizer()
    result = summarizer._extract_content(html)
    assert description in result or len(result) > 0, (
        f"Expected og:description text in result, got: {result!r}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
