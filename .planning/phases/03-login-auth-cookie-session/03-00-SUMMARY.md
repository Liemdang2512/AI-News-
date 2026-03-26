---
phase: 03-login-auth-cookie-session
plan: "00"
subsystem: api
tags: [auth, cookie-session, fastapi, admin-create, hashing, cors, bcrypt]
requires: []
provides:
  - "Auth cookie contracts + router skeleton"
  - "Password hashing helpers + auth store (memory + optional postgres)"
  - "Seed admin from env (ADMIN_EMAIL + ADMIN_PASSWORD_HASH)"
  - "CORS credentials compatibility fix (SEC-002)"
  - "Login/logout endpoints with HttpOnly `session_id` cookie contract"
affects: [phase:03-01, phase:03-02, protected endpoints]

key-files:
  created:
    - backend/routes/auth.py
    - backend/services/auth.py
    - backend/services/auth_types.py
    - backend/services/auth_password.py
    - backend/services/auth_store.py
  modified:
    - backend/main.py
    - backend/config.py
    - backend/requirements.txt
    - backend/.env.example
patterns-established:
  - "Cookie-based session_id + server-side validation (revoked_at/expires_at)"
  - "Never log plaintext password/password_hash; generic error details"

requirements-completed: [AUTH-001, AUTH-002, AUTH-004, SEC-002]

---

## Phase 03: login-auth-cookie-session Summary

**Bổ sung auth cookie session nền tảng: bcrypt-based hashing, server-side session store, login/logout/admin-create endpoints set/clear `HttpOnly session_id` cookie và fix CORS credentials.**

## Task Commits

1. **Task 1: Define auth contracts + cookie constants (no logic)** - `47de4a1`
2. **Task 2: Users/sessions store + schema init + password hashing + seed admin (D-01)** - `8e63c7e`
3. **Task 3: Implement login/logout + admin-create endpoints** - `c4b9c9d`

## Decisions Made
- Seed admin từ env (`ADMIN_EMAIL` + `ADMIN_PASSWORD_HASH`) và đảm bảo login hoạt động ngay cả khi lifespan startup không chạy trong `TestClient` (lazy init trong `auth_store`).
- Dùng `bcrypt` trực tiếp thay vì `passlib[bcrypt]` do lỗi tương thích trong môi trường dev.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] passlib[bcrypt] không hoạt động trong môi trường**
- Found during: Task 02 verify login
- Issue: `passlib.hash.bcrypt.hash()` lỗi
- Fix: Chuyển hashing sang thư viện `bcrypt` trực tiếp + cập nhật `backend/requirements.txt`
- Files modified: `backend/requirements.txt`, `backend/services/auth_password.py`
- Verification: `/api/auth/login` set `HttpOnly session_id` cookie PASS
- Committed in: `c4b9c9d`

**2. [Rule 2 - Missing critical testability] Admin seed không chạy khi TestClient không dùng context manager**
- Found during: Task 02 verify login (HTTP 401)
- Issue: FastAPI lifespan startup event không chạy trong pattern `TestClient(app)` không dùng `with`
- Fix: Thêm lazy initialization trong `backend/services/auth_store.py`
- Files modified: `backend/services/auth_store.py`
- Verification: rerun verify login PASS
- Committed in: `c4b9c9d`


