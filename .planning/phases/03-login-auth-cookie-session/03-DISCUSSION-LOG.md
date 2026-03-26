# Phase 3: login-auth-cookie-session - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26T06:12:49Z
**Phase:** 03-login-auth-cookie-session
**Areas discussed:** Bootstrap admin + Admin-create user

---

## Bootstrap admin + Admin-create user

| Option | Description | Selected |
|--------|-------------|----------|
| Seed admin từ env | Startup sẽ seed admin nếu chưa có (ADMIN_EMAIL + ADMIN_PASSWORD_HASH) | ✓ |
| One-time bootstrap token | Token env để gọi endpoint tạo admin lần đầu | |
| Manual DB | Tạo trực tiếp trong DB, không có flow bootstrap | |

**User's choice:** Seed admin từ env khi startup.
**Notes:** Admin-create user có UI + API; cơ chế mở khóa gồm bootstrap token (chỉ dùng setup ban đầu) và admin session (dùng lâu dài).

---

## Claude's Discretion

- Endpoint naming/path cụ thể cho admin-create user (miễn nhất quán và rõ ràng).
- UX chi tiết trang admin-create user (validation, layout) miễn không lộ secrets.

## Deferred Ideas

None.

