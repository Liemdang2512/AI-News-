# Roadmap

## ✅ v1.0 MVP (Shipped: 2026-03-26)

### Phase 1: Quy trình đọc và tóm tắt bài viết
**Goal:** Đảm bảo 100% bài viết từ RSS feed đều được đọc nội dung đầy đủ và tóm tắt bởi AI — không còn bài nào chỉ hiện RSS description thô hoặc thiếu bullet tóm tắt.

**Scope:**
- Cải thiện pipeline fetch bài viết: Playwright (JS-heavy sites) → curl_cffi → httpx → fallback
- Tối ưu content extraction từ HTML (JSON-LD, meta tags, article selectors)
- Đảm bảo tất cả path đều sinh ra bullet "- " trong output
- Cải thiện prompt để Gemini luôn viết đúng format
- Giảm thời gian xử lý (load nhanh hơn)

**Deliverables:**
- Tất cả bài từ laodong.vn, dantri.com.vn, vtv.vn, tuoitre.vn được đọc đầy đủ
- Mỗi bài có tóm tắt AI 130-150 chữ với bullet "- "
- Thời gian tóm tắt mỗi batch giảm so với hiện tại

**Requirements:** REQ-001, REQ-002, REQ-003

**Plans:** 4/4 plans complete

Plans:
- [x] 01-00-PLAN.md — Test scaffold: HTML fixtures + pytest test files (Wave 0) ✓ 2026-03-25
- [x] 01-01-PLAN.md — Trafilatura layer 0 trong _extract_content() + requirements.txt (Wave 1)
- [x] 01-02-PLAN.md — Playwright wait_for_selector timeout 5000ms → 2000ms (Wave 1, parallel) ✓ 2026-03-25
- [x] 01-03-PLAN.md — Bullet validation regex + BATCH_SIZE 10 + prompt hardening (Wave 2)

### Phase 2: Logging request/response, AI calls, và streaming
**Goal:** Ghi log request/response và lỗi ở backend FastAPI, có correlation `X-Request-ID`, log riêng cho các lần gọi AI (OpenAI/Gemini) nhưng redacts API keys, log tiến trình cho SSE/NDJSON streaming, cấu hình qua env và cập nhật docs ngắn.

**Requirements:** LOG-001, LOG-002, LOG-003, LOG-004, LOG-005, LOG-006, LOG-007

**Plans:** 4/4 plans complete

**Success Criteria:**
1. Streaming endpoints vẫn giữ nguyên payload contract (SSE/NDJSON) và không crash khi bật/tắt logging.
2. Các log có correlation qua `X-Request-ID` giữa backend và frontend.
3. API keys/tokens bị redacts trong log (không lộ substrings nhạy).

Plans:
- [x] 02-00-PLAN.md — Logging test scaffold (Wave 0) (RED)
- [x] 02-01-PLAN.md — Logger foundation + middleware request-id logging (Wave 1)
- [x] 02-02-PLAN.md — AI call logging (OpenAI/Gemini) + redaction (Wave 2)
- [x] 02-03-PLAN.md — Streaming progress logging + frontend basic log + docs (Wave 2) ✓ 2026-03-26

---

## 🚧 v1.1 Login/Auth

### Phase 3: Cookie session Auth + User store
**Goal:** Thêm hệ thống đăng nhập/đăng xuất bằng cookie session (HttpOnly), lưu user + session ở backend (DB), và chuẩn hóa middleware nhận user cho các endpoint cần bảo vệ.

**Requirements:** AUTH-001, AUTH-002, AUTH-003, AUTH-004, SEC-001, SEC-002

**Success Criteria:**
1. `POST /api/auth/login` tạo session cookie HttpOnly và backend trả `X-Request-ID` đúng.
2. `POST /api/auth/logout` làm mất session; request sau đó vào endpoint protected trả `401`.
3. Password được hash (không có plaintext trong DB/log/response).

Plans:
- [x] 03-00-PLAN.md — DB schema user + session, endpoint register/admin-create, login/logout
- [x] 03-01-PLAN.md — Middleware kiểm tra session cookie, gắn user vào request state
- [x] 03-02-PLAN.md — Tests cho auth: login/logout + unauthorized behavior

### Phase 4: Frontend Auth UI + Gating
**Goal:** Thêm UI login/register hoặc admin-create user (theo v1) và bảo vệ trang UI: ẩn input API key/disable summarize khi chưa đăng nhập.

**Requirements:** UI-001, UI-002, UI-003, UX-001

**Success Criteria:**
1. Khi chưa login: UI không cho gọi streaming endpoints (hoặc chặn trước), hiển thị link login.
2. Khi login: UI hiển thị email user + nút logout, cho phép chạy tóm tắt.
3. Fetch gọi protected endpoints gửi cookie session (có `credentials: "include"`).

Plans:
- [ ] 04-00-PLAN.md — Auth forms + lưu state user, gọi backend login/logout
- [ ] 04-01-PLAN.md — Gating UI và cập nhật fetch streaming/options để gửi cookie

### Phase 5: Protect streaming endpoints + docs
**Goal:** Bảo vệ các endpoint streaming (`fetch_stream`, `summarize_stream`) và cập nhật docs/env cho auth + cookie settings + dev bootstrap admin.

**Requirements:** BACKEND-001, BACKEND-002, BACKEND-003, DOC-001

**Success Criteria:**
1. Khi không có session: SSE/NDJSON không phát dữ liệu payload, trả status 401.
2. Logs cho protected endpoints vẫn có `X-Request-ID` và có thể gắn user_id/email (không lộ secrets).
3. README có section auth: env keys + cách tạo admin ban đầu + cách bật cookie settings.

Plans:
- [ ] 05-00-PLAN.md — Protect endpoints, add correlation user info, update README/.env.example
