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
