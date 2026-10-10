# Handoff

## Last Updated
2026-10-10T20:19 (session 28 — chuẩn bị deploy backend lên Railway, CHƯA deploy)

## Current Goal (session 28)
Đẩy backend (FastAPI + Playwright) lên Railway bằng CLI.

## What Changed (session 28)
- **Thêm** `.railwayignore`: loại `.git`, `.harness`, `frontend`, `desktop`, `cloudflare-worker`, `docs`, `Users`, `@`, `.env`, `**/venv`, `**/__pycache__`, `*.log` khỏi bản upload. Lý do: `Dockerfile` có `COPY backend/ .` và repo không có `.dockerignore` → nếu không chặn thì `backend/venv` + `backend/.env` (secret) bị đóng vào image.
- Không sửa code nào khác. `railway.toml` + `Dockerfile` đã có sẵn từ trước; `config.py` đã đọc `PORT` của Railway (dòng 32) nên không cần đổi.

## Findings
- Production hiện tại: backend trên VPS `api-news.meetingminutes.ai.vn`, frontend Vercel hardcode URL đó trong `frontend/app/api/rss/fetch_stream/route.ts`. Deploy Railway = backend thứ hai, frontend chưa dùng nó.
- `railway` CLI 4.35.0 đã cài nhưng token hết hạn (`invalid_grant`).
- `.env.example` bị permission deny khi đọc → tên biến lấy từ `backend/config.py`: `OPENAI_API_KEY`/`GEMINI_API_KEY`, `AI_PROVIDER`, `FRONTEND_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH`, `AUTH_COOKIE_SECURE`, tùy chọn `LOG_DB_DSN`, `AUTH_SESSION_STORAGE`.
- Lần đầu `git status`/`ls -la` trong thư mục này bị treo; `ls` cấp 1 và đọc file thì nhanh → tránh `git status` và quét đệ quy ở đây.

## Railway + backup VPS (session 28, cập nhật sau)
- ĐÃ DEPLOY (2026-10-10T20:30): project Railway `app-crwal-backend` (production) + service `backend`, build Docker OK, `/health` = 200 `{"status":"healthy"}` tại https://backend-production-96b2.up.railway.app. Tài khoản Railway: Giang Hoang (Tan xác nhận là của Tan).
- CHƯA set biến nào trên service (OPENAI_API_KEY, AI_PROVIDER, FRONTEND_URL, ADMIN_EMAIL, ADMIN_PASSWORD_HASH, AUTH_COOKIE_SECURE) → tóm tắt AI + đăng nhập chưa dùng được.
- ✅ ĐÃ SỬA 3 file (CHƯA commit, CHƯA push, đang ở nhánh `main`): `frontend/app/api/rss/fetch_stream/route.ts`, `frontend/vercel.json`, `frontend/next.config.js` → `https://backend-production-96b2.up.railway.app`. Kiểm: JSON hợp lệ, `next.config.js` rewrites đúng, grep không còn URL cũ. Chưa chạy `npm run build`.
- ĐÃ LÀM tiếp (2026-10-10): commit `e9bdbc7` trên nhánh `fix/railway-backend-url` đã push (CHƯA merge main → Vercel production chưa redeploy). `BACKEND_URL` (Production) trên Vercel project `ai-news1` đã thay bằng `https://backend-production-96b2.up.railway.app` qua Vercel CLI (giá trị cũ ~ `ai-news-rosy.vercel.app`, không lưu lại; `VITE_API_URL` giữ nguyên). Railway service `backend` đã set: `AI_PROVIDER=openai`, `FRONTEND_URL=https://ai-news1.vercel.app`, `AUTH_COOKIE_SECURE=true`, `OPENAI_API_KEY=REPLACE_WITH_YOUR_OPENAI_KEY` (GIỮ CHỖ — Tan tự thay).
- KIỂM THỬ (2026-10-10): Railway direct `/health` 200, `/docs` 200, `/api/auth/me` 401; POST `/api/rss/fetch_stream` (VOV xa-hoi, 10/10/2026 0h00-20h00) → 30 bài, SSE `complete`. Preview Vercel `ai-news1-h8idfeh10-…vercel.app` (nhánh fix/railway-backend-url, bị Vercel Auth chặn → dùng `vercel curl`): route.ts → Railway OK (30 bài), rewrite `/api/auth/me` → `{"detail":"Unauthorized"}` 401 từ FastAPI OK, trang chủ 200. `vercel curl` đã tự tạo 1 deployment-protection bypass token cho project ai-news1 (có thể revoke). CHƯA kiểm: tóm tắt AI (key giữ chỗ), đăng nhập (thiếu ADMIN_*), Hà Nội Mới/Playwright, production (chưa merge).
- CẬP NHẬT (sau khi Tan thay key): `OPENAI_API_KEY` đã là key thật (164 ký tự). Kiểm AI: POST `/api/articles/summarize_stream` 1 bài VOV → HTTP 200, có `summary` (60s). PR #3 https://github.com/Liemdang2512/AI-News-/pull/3 đã tạo; merge bị classifier chặn ("Merge Without Review") → Tan tự merge. Frontend bắt đăng nhập (`app/page.tsx` → `/loginn` nếu `getMe` lỗi) nên `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH` là việc chắn đường: Tan chạy lệnh `!` copy từ `.env` trong backup VPS (không đưa secret vào chat).
- HOÀN TẤT NỐI (2026-10-10 ~20:50): PR #3 MERGED (commit 35358e7) → Vercel production `ai-news1-26wgkfadc…` Ready. Tan đã chạy lệnh copy `ADMIN_EMAIL/ADMIN_PASSWORD_HASH/USER_EMAIL/USER_PASSWORD_HASH` từ `.env` backup sang Railway (8 tham số; hash 60 ký tự). DOMAIN THẬT của project Vercel `ai-news1`: `ai-new.meetingminutes.ai.vn`, `ai-lay-bao-chinh-thong.vercel.app` (KHÔNG phải `ai-news1.vercel.app` — domain đó 404, tài liệu cũ sai). Đã sửa `FRONTEND_URL` trên Railway = hai domain thật. Kiểm production: `/loginn` 200, `/api/auth/me` 401 `{"detail":"Unauthorized"}` (FastAPI), `fetch_stream` VOV → 29 bài, dedup AI 2 nhóm (AI chạy thật). CHƯA kiểm: đăng nhập bằng mật khẩu thật (Tan thử), tóm tắt trên production, Hà Nội Mới/Playwright, tải nhiều bài (timeout 60s/bài).
- KIỂM THÊM (2026-10-10 ~20:55): Tan xác nhận ĐĂNG NHẬP ĐƯỢC trên production. Tóm tắt 2 bài VOV qua `ai-new.meetingminutes.ai.vn/api/articles/summarize_stream` → HTTP 200, 63s, có `summary` đủ 2 bài (key OpenAI thật hoạt động). Quan sát: 1 bài ~60s, 2 bài ~63s (chủ yếu độ trễ cố định); model gõ nhầm "Triệu cường đang cao" thay "Triều cường dâng cao" (lỗi chất lượng model, không phải lỗi hạ tầng). CHƯA kiểm: Hà Nội Mới/Playwright, tải nhiều bài (≥12).
- HÀ NỘI MỚI ✅ (2026-10-10 ~21:00): production `ai-new.meetingminutes.ai.vn/api/rss/fetch_stream` (`hanoimoi.vn/rss/xa-hoi`, cả ngày) → HTTP 200, 25s, 26 bài, các bước fetch_rss→dedup→verification→complete đủ. Log Railway: curl_cffi + httpx bị Cloudflare chặn, rss2json lỗi, ScrapingAnt thử, rồi `Playwright: got RSS … 52 entries` (Playwright cứu). Không thấy OOM/killed. CHƯA kiểm: nhiều request đồng thời (RAM), tóm tắt ≥12 bài, và việc Cloudflare có chặn cả Playwright từ IP Railway theo thời gian.
- POSTGRES + AUTH FIX (2026-10-10 ~21:25): thêm service Railway `Postgres` (project app-crwal-backend). Backend set `AUTH_SESSION_STORAGE=postgres`, `AUTH_DB_DSN=${{Postgres.DATABASE_URL}}`. PHÁT HIỆN BUG: `_seed_user_if_missing` (USER_EMAIL) luôn seed vào RAM kể cả mode postgres → user thường không đăng nhập được. Đã sửa `backend/services/auth_store.py` (seed vào Postgres, `ON CONFLICT (email) DO NOTHING`) + thêm `backend/test_auth_seed_postgres.py` (2 test; import lazy vì test_auth_cookie_session set env trước khi import config). Tests: 8 passed cả 2 thứ tự. ĐÃ DEPLOY bằng `railway up` (CHƯA commit/push git — code deploy khác git). Kiểm trong container (`railway ssh`): bảng `sessions`,`users`; users tổng 2 = 1 admin + 1 thường; sessions 0 (mọi người bị đăng xuất 1 lần). Postgres KHÔNG có TCP proxy công khai (đúng ý, an toàn).
- "network error" (Tan chụp ảnh 21:08): kết quả vẫn hiển thị (91 bài, lọc còn 48) nhưng có banner lỗi. Log Railway: backend xong yêu cầu trong ~47s, không restart; có nhiều `Page crashed` của Playwright khi tải bài viết. Tái hiện bằng curl (production, đúng 10 nguồn + 6h00–8h00): 57s, exit 0, complete OK; tái hiện trong Chrome (tab riêng, JS fetch+reader): 51s, 90 bài, STREAM DONE ok. → lỗi CHẬP CHỜN, chưa tái hiện được. Giả thuyết: stream bị cắt SAU sự kiện complete, hoặc banner từ lần tìm khác. Đề xuất: ở `frontend/app/page.tsx` catch (dòng ~213) không hiện lỗi nếu đã nhận `complete`; tự thử lại 1 lần nếu stream đứt trước `complete`. CHƯA làm.
- CHƯA đo: tóm tắt lô 12 bài (CHUNK_SIZE=12, tuần tự; `summarizer` batch 4 song song, mỗi bài timeout 120s; 1 bài ≈ 60s do Playwright fallback). Bước đo bị classifier chặn ("Production Reads").
- (cũ) Còn lại: (1) Tan thay `OPENAI_API_KEY` thật; (2) set `ADMIN_EMAIL` + `ADMIN_PASSWORD_HASH` (chưa có, không đọc được .env); (3) merge nhánh vào main để Vercel redeploy; (4) kiểm end-to-end tìm kiếm/tóm tắt/đăng nhập.
- (Trước khi sửa) Frontend (Vercel) CHƯA nối backend Railway mới: `frontend/app/api/rss/fetch_stream/route.ts` hardcode `api-news.meetingminutes.ai.vn` (VPS); `frontend/vercel.json` rewrite `/api/:path*` → VPS; `frontend/next.config.js` mặc định `ai-news-backend-production-6e96.up.railway.app` (service Railway cũ, trả 404 "Application not found" = đã chết). Chưa biết `NEXT_PUBLIC_API_URL`/`BACKEND_URL` trên Vercel dashboard.
- VPS `222.255.119.32`: DNS vẫn trỏ về, nhưng cổng 443/80/22 không phản hồi từ máy Tan lúc 20:30 → frontend production có thể đang gọi backend chết.
- Backup VPS: `/Users/tanliem/vps-backup-222.255.119.32-20261001` (db/ + files/opt.tar.gz + volumes/). `/opt/ai-news` = chính codebase này.
- App này cần 3 bảng (`backend/db/init.sql`): `users`, `sessions`, `request_logs`. KHÔNG dump nào trong `db/` có `sessions`/`request_logs` → backend VPS chạy `AUTH_SESSION_STORAGE=memory`, `LOG_DB_ENABLED=false`, không có DB để migrate.
- DB `ainews` (dump `app-postgres-1.sql.gz`: raw_articles 2015, processed_articles 894, daily_briefs 41...) thuộc app khác (nhiều khả năng `/opt/ainew`), backend này không đọc các bảng đó. Chưa xác minh 100% container ↔ thư mục.
- Chưa giải nén `.env` trong backup (chứa secret); Tan tự set `OPENAI_API_KEY` (vẫn dùng OpenAI).

## Verification (session 28)
- ✅ env-health: node v24.13.0, npm 11.6.2
- ⏭ tests / build / lint / review / knowledge-graph: skipped — lý do ghi trong `quality-gates.json`
- ❌ Chưa chạy: Docker build, `railway up`, kiểm `/health` trên Railway

## Risks / Skipped Gates
- Playwright cào Hà Nội Mới ~36s + tốn RAM → gói Railway free có thể OOM/timeout.
- `AUTH_SESSION_STORAGE=memory` → session mất mỗi lần redeploy (cần Postgres nếu muốn giữ).
- Chưa kiểm image build được.
- Đẩy biến môi trường lên Railway = gửi secret ra ngoài → cần Tan duyệt danh sách tên biến trước.

## Next Action (session 28)
1. Tan chạy `railway login`.
2. Tan chọn A (chạy thử song song VPS) hoặc B (chuyển hẳn sang Railway).
3. Duyệt danh sách biến → `railway init` → `railway variables` → `railway up` → kiểm `/health`.
4. Nếu B: đổi URL trong `route.ts` + push frontend (cần Tan confirm).

---
# Lịch sử session trước

## Current Goal (session 27)
Fix Hà Nội Mới và VOV không lấy được bài trên production.

## What Changed (session 27)

### Root Cause Chain (đã tìm ra và fix)
1. **Playwright deps thiếu trên VPS** → `libatk-1.0.so.0: No such file` → chạy `playwright install-deps chromium` trên VPS → fixed
2. **`fetch_stream` Edge Route dùng sai backend** → `BACKEND_URL` env var trên Vercel trỏ sang `ai-news-rosy.vercel.app` (backend cũ, không có Playwright) → hardcode VPS URL trong route.ts → commit `3a699bf`

### Files Changed (committed + pushed)
- `frontend/app/api/rss/fetch_stream/route.ts`: hardcode `BACKEND_URL = 'https://api-news.meetingminutes.ai.vn'`
- VPS: `playwright install-deps chromium` (manual)

### Verification ✅
- Browser JS test: `elapsed=36707ms articles=6` — HNM trả 6 bài sau ~36s (Playwright)
- VPS logs: `✅ Playwright: got RSS for hanoimoi/rss/xa-hoi`, 60 entries mỗi feed
- VOV: 11 bài (10h-12h), 18 bài (12h-17h) — fetch qua secure_fetcher ~1.3s
- VOV 0 bài (6h-8h) là đúng — VOV publish muộn, không có bài sáng sớm

## Verification (session 27)
- ✅ Hà Nội Mới: hoạt động, Playwright ~36s, 6 bài (6h-8h)
- ✅ VOV: hoạt động, secure_fetcher ~1.3s, 11-18 bài (10h-17h)
- ✅ Dân Trí + VTV: vẫn bình thường
- ✅ VPS backend: healthy, fetch_stream đã tới đúng VPS

## Risks / Open Issues
- HNM Playwright ~36s → gần timeout limit; monitor nếu bị cắt
- VOV ít bài 6h-8h → user nên chọn khung 10h-17h
- `BACKEND_URL` env var trên Vercel còn tồn tại (trỏ sai) — nên xóa trong Vercel dashboard
- `AUTH_SESSION_STORAGE=memory` → session reset khi restart VPS

## Next Action
- Recommend: xóa `BACKEND_URL` env var trong Vercel dashboard (Settings → Environment Variables)
- Monitor HNM timeout trong production
- Project stable — chờ bug report mới nếu có

## Current Goal (session 25)
Deploy backend FastAPI lên VPS (222.255.119.32) và fix summarizer stalling trên Vercel Hobby.

## What Changed (session 25)

### Code changes (đã commit + push)
- `backend/services/summarizer.py`: wrap batch gather với `asyncio.wait_for(timeout=120)` + `return_exceptions=True`
- `backend/vercel.json` + `vercel.json`: thêm `maxDuration: 300`
- `frontend/components/ArticleList.tsx`: bỏ giới hạn 20 bài (revert), giữ UI bình thường
- `frontend/app/page.tsx`: thêm chunking logic — tự chia URLs thành lô 12, gọi API nhiều lần, merge markdown theo category

### VPS deploy (manual — chưa hoàn thành)
- Clone repo về `/opt/ai-news/`
- Tạo venv, `pip install -r requirements.txt` ✅
- Tạo `.env` tại `/opt/ai-news/backend/.env` ✅
- Tạo systemd service `ai-news-backend.service` ✅
- Backend đang chạy tại `127.0.0.1:8002` ✅ (port 8001 bị Docker chiếm)
- **CHƯA XONG:** Nginx config chưa tạo — đang chờ Tan cung cấp subdomain

## Verification
- Backend VPS: `systemctl status ai-news-backend` → active (running) ✅
- Frontend chunking: chưa test trên production
- Nginx: chưa setup → backend chưa accessible từ ngoài

## Risks / Skipped Gates
- Chưa có Nginx config → backend chưa dùng được từ frontend
- Cần Tan chọn subdomain (vd: `api-news.meetingminutes.ai.vn`) và trỏ DNS A record về `222.255.119.32`
- `AUTH_SESSION_STORAGE=memory` → session mất khi restart service (OK cho MVP, cần Postgres sau)
- `ADMIN_PASSWORD_HASH` trong `.env` có ký tự `$` — đã escape đúng trong heredoc

## Next Action
1. Tan chọn subdomain cho backend API (vd: `api-news.meetingminutes.ai.vn`)
2. Trỏ DNS A record về `222.255.119.32`
3. Tôi tạo Nginx config + SSL (certbot)
4. Update `frontend/vercel.json` rewrite destination → subdomain mới
5. Commit + push → Vercel redeploy → test end-to-end

## Migration Plan (session 23)
Target Railway project: `b673ce41-4629-4a7b-923c-e1ffa06c2450`
Target service ID: `aed7d52a-18e7-4aa8-82fb-3d8f09a9dd3d`

Steps Tan cần làm:
1. Railway dashboard → service mới → Source → connect GitHub repo, Root Directory: `/`
2. Copy tất cả env vars từ service cũ (`GEMINI_API_KEY`, `WEBSHARE_PROXY_URL`, `CF_PROXY_URL`, `FLARESOLVERR_URL`, ...) sang service mới
3. Chờ deploy xong → lấy URL mới (`xxx.up.railway.app`)
4. Báo URL mới → tôi update `frontend/vercel.json` + push → Vercel redeploy

## Infrastructure (hiện tại — chưa đổi)
- **Backend (FastAPI):** `ai-news-backend-production-6e96.up.railway.app` (Railway — sẽ migrate)
- **FlareSolverr:** `flaresolverr-production-2614.up.railway.app` (Railway, cùng project cũ)
- **Frontend (Next.js):** Vercel — `ai-new.meetingminutes.ai.vn`
- **Cloudflare Worker:** `hanoimoi-proxy.dangtanliem37.workers.dev`

## Next Action
Chờ Tan cung cấp URL backend mới từ Railway project mới → update `frontend/vercel.json` destination URL → commit + push → verify Vercel rewrite hoạt động.

---

## Last Updated (session 21)
2026-06-23T10:30 (session 21 — fix Vercel rewrite URL)

## Current Goal (session 21)
Fix lỗi "Đăng nhập thất bại" trên `ai-new.meetingminutes.ai.vn/loginn`.

## What Changed (session 21)
- `frontend/vercel.json`: đổi rewrite destination từ `ai-news-backend-staging.up.railway.app` → `ai-news-backend-production-6e96.up.railway.app`
- Commit `ab4f081`, đã push + deploy lên Vercel

## Verification (session 21)
Login thành công sau deploy ✅

---

## Last Updated (session 19)
2026-06-18T22:30 (session 19 — FlareSolverr integrated)

## Current Goal (session 19)
Bypass Cloudflare Managed Challenge trên hanoimoi.vn để lấy tin ổn định.

## Analysis Done (session 19)

### Tình trạng hiện tại
- hanoimoi RSS URLs (`/rss/xa-hoi`, `/rss/the-gioi`, `/rss/phap-luat`, `/rss/kinh-te`) được fetch qua `WEBSHARE_PROXY_URL` residential proxy → fallback `secure_fetcher` (curl_cffi → rss2json → Playwright)
- `CF_PROXY_URL` (Cloudflare Worker) đã được build tại `cloudflare-worker/hanoimoi-proxy.js` và hỗ trợ cả `hanoimoi.vn` + `vov.vn` — **nhưng KHÔNG được dùng trong hanoimoi RSS path** (chỉ dùng cho VOV HTML)
- Gap chính: `_fetch_hnm_rss` trong `rss_fetcher.py` bỏ qua `CF_PROXY_URL` hoàn toàn

### Bypass design đã thiết kế (chưa implement)
Layer stack cho hanoimoi RSS:
1. **CF Worker proxy** (`CF_PROXY_URL`) — Cloudflare edge-to-edge trust, bypass JS challenge
2. **Residential proxy** (`WEBSHARE_PROXY_URL`) — IP dân cư, đã hoạt động
3. **curl_cffi** TLS impersonation (trong secure_fetcher)
4. **rss2json.com** public proxy (trong secure_fetcher)
5. **ScrapingAnt** (nếu có key)
6. **Playwright** headless (last resort)

### Files đã thay đổi (session 19)
- `backend/services/rss_fetcher.py`:
  - `_fetch_hnm_rss`: thêm FlareSolverr làm Layer 1, CF Worker Layer 2, residential Layer 3, secure_fetcher Layer 4
  - `_scrape_hanoimoi_html`: thêm `fetch_html_via_flaresolverr()`, wire vào `fetch_one()` làm Layer 1
- `cloudflare-worker/hanoimoi-proxy.js`: thêm `RSS_HEADERS`, detect `/rss/` URL, skip JS redirect cho RSS, deploy lên `hanoimoi-proxy.dangtanliem37.workers.dev`

### CF Worker test result
CF Worker bị CF Managed Challenge block (`cType: 'managed'`) — không bypass được. Cần FlareSolverr.

### FlareSolverr — DONE ✅
- Service: `https://flaresolverr-production-2614.up.railway.app` (Railway project: ai-news-backend)
- Backend env: `FLARESOLVERR_URL=https://flaresolverr-production-2614.up.railway.app`
- Verified: 26 bài từ hanoimoi.vn/rss/xa-hoi, log xác nhận `✅ FlareSolverr: hanoimoi RSS OK`

## Previous Goal (session 18 — DONE)
Fix GitHub CI build failure để Railway auto-deploy từ GitHub hoạt động.

### Fix Applied (session 18)
- `Dockerfile` (repo root): copy từ `backend/` subdir với explicit paths
- `railway.toml` (repo root): `builder = "dockerfile"` + deploy config

### Verification (session 18)
- ✅ `railway up` từ repo root: deploy `9d3f7709` — SUCCESS
- ✅ `/health` → `{"status":"healthy"}`
- ⏳ GitHub auto-deploy webhook chưa được xác nhận (cần 1 push mới)

## Risks / Open Issues
- GitHub webhook có thể vẫn chưa trigger → cần push 1 commit để verify
- hanoimoi bypass chưa implement — tin hanoimoi vẫn có thể fail khi không có residential proxy

## Next Action
1. Implement hanoimoi bypass: sửa `_fetch_hnm_rss` để thêm `CF_PROXY_URL` làm Layer 1
2. Sửa `hanoimoi-proxy.js` để gửi đúng `Accept: application/rss+xml` khi URL chứa `/rss/`
3. Push commit để xác nhận GitHub → Railway webhook
