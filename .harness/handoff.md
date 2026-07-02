# Handoff

## Last Updated
2026-07-02T18:15 (session 27 — HNM + VOV fixed end-to-end)

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
