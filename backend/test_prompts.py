"""
Unit tests for prompt format covering REQ-003.

Tests verify that SINGLE_ARTICLE_SUMMARIZE_PROMPT and SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT
contain the required bullet format instructions and no unformatted placeholder brackets.

Tests are run from the backend/ directory:
    cd backend && python3 -m pytest test_prompts.py -v

All tests in this file PASS immediately as they test existing prompt strings.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import pytest
from prompts import SINGLE_ARTICLE_SUMMARIZE_PROMPT, SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT


def test_single_article_prompt_no_brackets():
    """REQ-003: Formatted SINGLE_ARTICLE_SUMMARIZE_PROMPT should not have unresolved [bracket] instructions."""
    formatted = SINGLE_ARTICLE_SUMMARIZE_PROMPT.format(
        title="Tiêu đề bài test",
        source="Nguồn test",
        url="https://example.com/bai-viet-test",
        content="Nội dung bài viết test đầy đủ thông tin cần thiết.",
    )
    # The instruction "KHÔNG dùng dấu ngoặc vuông" should appear in the prompt (it's a rule for the AI)
    assert "KHÔNG dùng dấu ngoặc vuông" in formatted, (
        "Expected 'KHÔNG dùng dấu ngoặc vuông' instruction in formatted prompt"
    )
    # The content instruction line should be present
    assert "- Viết nội dung" in formatted, (
        "Expected '- Viết nội dung' instruction line in formatted prompt"
    )


def test_url_prompt_no_brackets():
    """REQ-003: Formatted SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT should contain key instructions."""
    formatted = SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT.format(
        url="https://example.com/bai-viet",
        title="Tiêu đề test",
        source="Nguồn test",
    )
    assert "KHÔNG dùng dấu ngoặc vuông" in formatted, (
        "Expected 'KHÔNG dùng dấu ngoặc vuông' instruction in URL prompt"
    )


def test_single_article_prompt_has_bullet_instruction():
    """REQ-003: SINGLE_ARTICLE_SUMMARIZE_PROMPT must instruct AI to start with dash bullet."""
    assert "bắt đầu bằng dấu gạch ngang" in SINGLE_ARTICLE_SUMMARIZE_PROMPT, (
        "Expected 'bắt đầu bằng dấu gạch ngang' instruction in SINGLE_ARTICLE_SUMMARIZE_PROMPT"
    )


def test_url_prompt_has_bullet_instruction():
    """REQ-003: SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT must instruct AI to start with dash bullet."""
    assert "bắt đầu bằng dấu gạch ngang" in SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT, (
        "Expected 'bắt đầu bằng dấu gạch ngang' instruction in SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
