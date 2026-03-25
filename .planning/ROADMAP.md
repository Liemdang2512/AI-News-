# Roadmap

## Milestone 1: Quy trình đọc và tóm tắt bài viết ổn định

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

**Plans:** 4 plans

Plans:
- [x] 01-00-PLAN.md — Test scaffold: HTML fixtures + pytest test files (Wave 0) ✓ 2026-03-25
- [ ] 01-01-PLAN.md — Trafilatura layer 0 trong _extract_content() + requirements.txt (Wave 1)
- [ ] 01-02-PLAN.md — Playwright wait_for_selector timeout 5000ms → 2000ms (Wave 1, parallel)
- [ ] 01-03-PLAN.md — Bullet validation regex + BATCH_SIZE 10 + prompt hardening (Wave 2)
