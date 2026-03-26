---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Ready to execute
last_updated: "2026-03-26T04:17:52.950Z"
progress:
  total_phases: 2
  completed_phases: 1
  total_plans: 8
  completed_plans: 7
---

# Project State

## Project

**Name:** AI News Assistant
**Description:** Ứng dụng tổng hợp và tóm tắt tin tức từ RSS feeds sử dụng Gemini AI
**Stack:** Python FastAPI backend, Playwright, curl_cffi, Gemini API (gemini-3-flash-preview)

## Current Milestone

Milestone 1: Quy trình đọc và tóm tắt bài viết ổn định

## Decisions

- Dùng Gemini gemini-3-flash-preview qua v1beta endpoint
- Playwright là browser headless để bypass anti-bot cho các site JS-heavy
- curl_cffi dùng Chrome impersonation cho các site thông thường
- Tóm tắt theo phong cách báo Nhân Dân, 130-150 chữ
- Output luôn có bullet "- " để đảm bảo consistency
- [Phase 01-quy-trinh-doc-va-tom-tat]: Add trafilatura as layer 0 in _extract_content() with try/except ImportError guard for graceful degradation
- [Phase 01-quy-trinh-doc-va-tom-tat]: Use regex r'^- .{20,}' with MULTILINE flag in _has_bullet_content to detect real bullet lines, avoiding false-positives from URL paths with dashes
- [Phase 02-00]: Test scaffold runs with 3/4 tests GREEN at Wave 0 because X-Request-ID middleware was already in main.py; only redact_secrets test stays RED
- [Phase 02-01]: Use contextvars.Token to reset ContextVar in finally block — prevents request_id leak between concurrent requests
- [Phase 02-01]: app_logger uses propagate=False to prevent double-logging with uvicorn root logger
- [Phase 02-logging-request-response]: Log api_key_present as bool, never log key string — prevents accidental secret leak in structured log fields
- [Phase 02-logging-request-response]: safe_url computed via redact_secrets(url) before log statement — sanitisation enforced at point of use for Gemini API key in query param

## Active Phase

Phase 1: Quy trình đọc và tóm tắt bài viết

## Current Position

Phase: 02 (logging-request-response) — EXECUTING
Plan: 4 of 4

- **Phase:** 01
- **Completed Plan:** 01-03 (Bullet Validation + BATCH_SIZE + Prompt Hardening)
- **Next Plan:** Phase Complete — all 4 plans done
- **Last session:** 2026-03-26T04:17:52.947Z

## Recent Decisions

- Use try/except AttributeError + pytest.skip() for future-method tests so collection never fails
- HTML fixtures in backend/fixtures/ for unit testing without live HTTP
- Test scaffold (plan 00) runs RED at Wave 0 — expected by design, goes GREEN as plans 01-03 implement features
- Reduce wait_for_selector timeout from 5000ms to 2000ms — Vietnamese news sites render in 1-2s; worst-case per-article time drops from 60s to 24s
- Add trafilatura as layer 0 in _extract_content() with try/except ImportError guard for graceful degradation
- Add lxml_html_clean as explicit dep due to lxml 6.x split of lxml.html.clean module
