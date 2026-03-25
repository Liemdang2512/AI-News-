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

## Active Phase
Phase 1: Quy trình đọc và tóm tắt bài viết

## Current Position
- **Phase:** 01-quy-trinh-doc-va-tom-tat
- **Completed Plan:** 01-00 (Test Scaffold)
- **Next Plan:** 01-01 (Content Extraction Implementation)
- **Last session:** 2026-03-25 — Completed 01-00-PLAN.md

## Recent Decisions
- Use try/except AttributeError + pytest.skip() for future-method tests so collection never fails
- HTML fixtures in backend/fixtures/ for unit testing without live HTTP
- Test scaffold (plan 00) runs RED at Wave 0 — expected by design, goes GREEN as plans 01-03 implement features
