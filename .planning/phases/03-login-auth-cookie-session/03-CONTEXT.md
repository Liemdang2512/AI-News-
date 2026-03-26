# Phase 3: login-auth-cookie-session - Context

**Gathered:** 2026-03-26T06:12:49Z
**Status:** Ready for planning

<domain>
## Phase Boundary

Thêm hệ thống đăng nhập/đăng xuất bằng cookie session (HttpOnly), lưu user + session ở backend (DB), và chuẩn hóa middleware nhận user cho các endpoint cần bảo vệ. Phase này cũng chốt cách bootstrap admin + cơ chế admin-create user (không có public register).

</domain>

<decisions>
## Implementation Decisions

### Bootstrap admin + Admin-create user (v1)
- **D-01:** Seed admin từ env khi startup: `ADMIN_EMAIL` + `ADMIN_PASSWORD_HASH` (chỉ tạo nếu chưa tồn tại admin trong DB).
- **D-02:** Sau lần đầu seed, admin quản trị user thông qua UI + API (API là nguồn sự thật; UI chỉ là client).
- **D-03:** Admin-create user cho phép 2 cơ chế:
  - **One-time bootstrap token** chỉ để mở khóa thiết lập ban đầu (khuyến nghị: chỉ hợp lệ khi chưa có admin / hoặc chỉ dùng 1 lần).
  - **Admin session** sau khi login (cơ chế mặc định lâu dài).
- **D-04:** Không có public register flow trong v1 (user tự đăng ký bị tắt).

### Claude's Discretion
- Cụ thể hóa endpoint path/naming (ví dụ `/api/admin/users` vs `/api/admin/create_user`) miễn nhất quán và dễ hiểu.
- Chi tiết UX của trang admin-create user ở frontend (layout, validation messages) miễn không lộ secrets.

</decisions>

<specifics>
## Specific Ideas

- Admin-create user nằm trong chính app (UI), nhưng luôn có API tương ứng để test/automation.
- Ưu tiên an toàn: không để bootstrap token hoạt động vĩnh viễn.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project planning
- `.planning/ROADMAP.md` — Phase 3 scope + success criteria
- `.planning/REQUIREMENTS.md` — AUTH-001..AUTH-004, SEC-001..SEC-002 (acceptance)
- `.planning/PROJECT.md` — milestone goal + constraints/security

### Existing code that affects auth
- `backend/main.py` — CORSMiddleware + request-id logging middleware (will matter for cookie+credentials)
- `frontend/app/page.tsx` — current gating points + how streaming calls are made today
- `frontend/lib/api.ts` — API base URL logic for web/desktop

No external specs/ADRs — requirements được capture trong planning docs ở trên.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/main.py`: đã có middleware set `X-Request-ID` + structured logging; có thể tái dùng pattern `extra={...}` để gắn `user_id/email` (nhưng phải tránh secrets).
- `backend/services/request_db_logger.py`: đã có asyncpg pool init; có thể mở rộng để lưu auth/session nếu chọn Postgres (hoặc tạo pool riêng).

### Established Patterns
- Backend: FastAPI + middleware; đang bật CORS `allow_credentials=True` (nhưng `allow_origins=["*"]` sẽ cần sửa khi dùng cookie).
- Frontend: hiện lưu `gemini_api_key` ở localStorage và gọi streaming endpoints bằng `fetch`.

### Integration Points
- Backend router: sẽ thêm `routes/auth.py` (hoặc tương đương) và include vào `backend/main.py`.
- Frontend: sẽ thêm auth state + gating (Phase 4), nhưng Phase 3 cần chốt contract login/logout + admin-create user.

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-login-auth-cookie-session*
*Context gathered: 2026-03-26T06:12:49Z*

