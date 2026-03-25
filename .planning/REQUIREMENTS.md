# Requirements

## REQ-001: Đọc nội dung đầy đủ từ bài viết
Hệ thống phải đọc được nội dung đầy đủ của bài viết (không chỉ RSS description) cho các site:
- laodong.vn, dantri.com.vn, vtv.vn, tuoitre.vn, vnexpress.net
- thanhnien.vn, tienphong.vn, vietnamplus.vn, vov.vn, nhandan.vn

Acceptance: Content extract >= 200 chars cho ít nhất 90% bài viết.

## REQ-002: Output luôn có bullet tóm tắt
Mọi bài viết trong output phải có ít nhất 1 dòng bắt đầu bằng "- " (bullet).
Không được hiện header-only (tiêu đề + nguồn + URL mà không có nội dung).

Acceptance: 100% bài viết trong output có "- " trong nội dung.

## REQ-003: Tóm tắt đúng phong cách
Nội dung tóm tắt phải:
- 130-150 chữ
- Phong cách báo Nhân Dân (chuẩn mực, trang trọng)
- Có đủ thông tin: Ai, cái gì, ở đâu, khi nào, tại sao

Acceptance: Gemini không trả về placeholder text hay dấu ngoặc vuông trong output.
