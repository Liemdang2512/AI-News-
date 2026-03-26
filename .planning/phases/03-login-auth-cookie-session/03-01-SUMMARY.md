---
phase: 03-login-auth-cookie-session
plan: "01"
subsystem: api
tags: [auth, cookie-session, dependency, request-state]
depends_on: ["03-00"]
provides:
  - "get_current_user dependency: validate cookie session_id + set request.state.user"
  - "Protected behavior for /api/admin/users: missing/invalid cookie -> 401 Unauthorized"
  - "Logout invalidation: revoked session -> protected returns 401"
affects: [phase:03-02, backend/test_auth_cookie_session.py]
key-files:
  modified:
    - backend/services/auth.py
requirements-completed: [AUTH-003, AUTH-004, SEC-001]
---

## Phase 03: login-auth-cookie-session Plan 01 Summary

**Triển khai `get_current_user` dependency đọc cookie `session_id`, validate qua store và gắn `request.state.user`; endpoint protected chuẩn hóa về `401 Unauthorized` khi thiếu/invalid session.**

## Task Commits

1. **Task 00: Implement get_current_user dependency** - `8c1dd98`

## Decisions Made
- `get_current_user` trả `None` (không throw) khi cookie thiếu/invalid để route quyết định `401` nhất quán.

