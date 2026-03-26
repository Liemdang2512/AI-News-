# Requirements

## AUTH-001: Admin-create user (v1)
V1 không có public register flow. Admin tạo user mới bằng email/password.
Acceptance: có endpoint tạo user cho admin và lưu password ở dạng hash.

## AUTH-002: Login bằng email/password
`POST /api/auth/login` nhận email/password và nếu hợp lệ tạo session cookie.
Acceptance: server set `session_id` cookie với thuộc tính `HttpOnly`.

## AUTH-003: Logout và invalidate session
`POST /api/auth/logout` xóa session hiện tại.
Acceptance: request sau logout vào endpoint protected trả `401`.

## AUTH-004: Session cookie server-side (session_id)
Session được lưu server-side theo `session_id` trong cookie.
Acceptance: session không bị giả mạo và có model/tables tương ứng.

## SEC-001: Không lộ password/session trong storage & logs
Không log plaintext password hoặc password hash; không trả password hash trong response.
Acceptance: test/validation không thấy substring nhạy trong log/response.

## SEC-002: Cookie security + CORS cho credentials
Cookie phải có ít nhất: `HttpOnly`, `Secure` (khi bật), `SameSite` phù hợp.
Acceptance: frontend dùng `credentials: "include"` và CORS credentials hoạt động.

## UI-001: UI login/logout + trạng thái user
Trang chính hiển thị email user + nút logout khi đã đăng nhập.
Acceptance: logout đổi trạng thái về chưa login.

## UI-002: Gating UI với streaming & API key config
Khi chưa login: ẩn/disable nhập API key và chặn gọi streaming endpoints.
Acceptance: không phát stream khi chưa login.

## UI-003: Fetch protected endpoints gửi cookie session
Các request tới endpoint protected phải gửi cookie session.
Acceptance: backend nhận cookie và xử lý đúng.

## UX-001: Admin-create user flow
Có UI hoặc trang admin để admin tạo user mới bằng email/password.
Acceptance: tạo user thành công và user mới login được.

## BACKEND-001: Protected streaming endpoints cho SSE/NDJSON
Bảo vệ endpoint streaming hiện có: `/api/rss/fetch_stream` và `/api/articles/summarize_stream`.
Acceptance: unauthorized không phát payload SSE/NDJSON.

## BACKEND-002: Unauthorized behavior chuẩn
Các endpoint protected trả `401` khi không có session hợp lệ.
Acceptance: frontend hiển thị lỗi phù hợp/không crash.

## BACKEND-003: Correlation user info trong logs
Khi log protected endpoints có thể gắn `user_id/email` (không lộ secrets) và vẫn có `X-Request-ID`.
Acceptance: log không rò rỉ secrets.

## DOC-001: Document env + cách bootstrap admin
Cập nhật `README.md` và `backend/.env.example`:
- cookie/session settings
- cách tạo admin ban đầu từ env
Acceptance: README có section auth + checklist env keys.
