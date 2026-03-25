# Phase 1: Quy trình đọc và tóm tắt bài viết - Research

**Researched:** 2026-03-24
**Domain:** Web content extraction + Gemini AI summarization pipeline (Python/FastAPI)
**Confidence:** HIGH (based on direct codebase inspection + verified library documentation)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-001 | Hệ thống phải đọc được nội dung đầy đủ (>= 200 chars cho >= 90% bài viết) từ 10 báo mục tiêu | Phân tích fetch pipeline hiện tại + trafilatura research |
| REQ-002 | Mọi bài viết trong output phải có ít nhất 1 dòng bắt đầu bằng "- " (không có header-only) | Bug analysis trong summarizer.py + validation logic review |
| REQ-003 | Tóm tắt đúng phong cách: 130-150 chữ, báo Nhân Dân, không có dấu ngoặc vuông | Prompt review trong prompts.py + Gemini behavior research |
</phase_requirements>

---

## Summary

Pipeline hiện tại đã có đủ 3 tầng fetch (Playwright → curl_cffi → httpx) và 2 tầng AI (URL context → nội dung fetch). Các bug đã được xác định và fix trong BUG_REPORT.md (validation "- ", meta tag mở rộng, threshold RSS). Tuy nhiên, vấn đề còn lại là content extraction chưa tối ưu: `_extract_content()` dùng BeautifulSoup với selector list tự viết — thiếu so với trafilatura (F1 0.945 vs 0.665 của BS4 theo benchmark).

Playwright dùng single shared browser instance với `asyncio.Semaphore(10)` — tốt về memory nhưng có bottleneck khi nhiều bài cùng chạy Playwright. Mỗi `fetch()` tạo mới BrowserContext, đóng sau khi dùng, đây là pattern đúng cho isolation. Tuy nhiên, `wait_for_selector` thử lần lượt từng selector trong `ARTICLE_SELECTORS` list (12 selector, mỗi cái timeout 5s nếu không tìm thấy) — đây là nguyên nhân chính khiến Playwright chậm (~3-5s/bài trong trường hợp xấu nhất là 12 x 5s = 60s nếu không tìm thấy selector).

Kết hợp trafilatura làm layer đầu tiên trong `_extract_content()` (thay cho BeautifulSoup selector list) sẽ giải quyết phần lớn vấn đề REQ-001 mà không cần thay đổi Playwright. Đây là thay đổi có impact cao nhất, ít rủi ro nhất.

**Primary recommendation:** Thêm trafilatura vào `_extract_content()` làm bước đầu tiên (trước JSON-LD và BS4 selectors), giảm timeout `wait_for_selector` xuống 2s, và tối ưu validation để tránh false-positive.

---

## Standard Stack

### Core (đã có trong project)
| Library | Version hiện tại | Purpose | Ghi chú |
|---------|---------|---------|--------------|
| playwright | 1.40.0 (system) / >=1.44.0 (requirements.txt) | Headless browser cho JS-heavy sites | Đã hoạt động, cần stealth upgrade |
| curl_cffi | 0.13.0 | Chrome TLS impersonation cho anti-bot bypass | Đã hoạt động tốt |
| beautifulsoup4 | 4.12.2 | HTML parsing + selector extraction | Vẫn giữ làm fallback |
| httpx | 0.26.0 | Async HTTP client fallback | Vẫn giữ |
| feedparser | 6.0.11 | RSS feed parsing | Không thay đổi |

### Thêm mới cần cân nhắc
| Library | Version | Purpose | Khi nào dùng |
|---------|---------|---------|-------------|
| trafilatura | 2.0.0 | Main text extraction từ HTML (F1: 0.945) | Thêm vào `_extract_content()` làm layer đầu tiên — HIGH priority |
| playwright-stealth | 2.0.2 | Bypass Cloudflare JS challenge cho Playwright | Nếu Cloudflare blocking vẫn xảy ra sau khi optimize — MEDIUM priority |
| lxml | latest | Required dependency của trafilatura | Tự cài theo trafilatura |

### Alternatives Considered
| Thay vì | Có thể dùng | Khi nào nên dùng thay thế |
|------------|-----------|----------|
| trafilatura | newspaper3k | newspaper3k hỗ trợ tốt hơn cho tiếng Anh, trafilatura tổng quát hơn và không có async issue |
| playwright-stealth | Có thể skip nếu trafilatura + existing fetch đủ mạnh | Các báo Việt Nam thường không dùng Cloudflare Enterprise |

**Installation (chỉ những thư viện mới):**
```bash
pip install trafilatura
pip install playwright-stealth  # chỉ nếu cần
```

**Version verification:**
- trafilatura: 2.0.0 (verified 2026-03-24 via `pip3 index versions trafilatura`)
- playwright-stealth: 2.0.2 (verified 2026-03-24 via `pip3 index versions playwright-stealth`)
- playwright hiện tại trên system: 1.40.0 — requirements.txt yêu cầu >=1.44.0, cần verify trong venv

---

## Architecture Patterns

### Cấu trúc pipeline hiện tại (đã verified từ code)

```
_process_single_article(url)
    │
    ├─ Step 1: fast_gemini.generate_content_with_url()   ← Gemini URL context (v1beta)
    │         Nếu len > 150 AND "- " in summary → return
    │
    ├─ Step 2: _fetch_article_html(url)                  ← Fetch tự động
    │   ├─ JS-heavy domain? → Playwright trước
    │   ├─ secure_fetcher (curl_cffi)
    │   ├─ httpx fallback
    │   └─ Non-JS-heavy? → Playwright lần cuối
    │
    ├─ Step 3: _extract_content(html)                    ← Extract nội dung
    │   ├─ JSON-LD articleBody
    │   ├─ BS4 selector list (20 selectors)
    │   └─ meta tags (og/twitter/description)
    │
    ├─ _merge_page_and_feed()                            ← Ghép page + RSS
    │
    ├─ Step 4: gemini_client.async_generate_content()    ← AI summarize
    │         Retry 5 lần với giảm dần body_limits
    │
    └─ get_fallback_summary()                            ← Fallback với bullet "- "
```

### Pattern 1: trafilatura làm layer extraction đầu tiên

**What:** Gọi `trafilatura.extract(html, ...)` trước JSON-LD và BS4 selectors trong `_extract_content()`. trafilatura là synchronous — gọi trong `asyncio.to_thread()` nếu lo ngại blocking.

**When to use:** Khi BeautifulSoup selector list không tìm thấy content (selector miss) — đây là nguyên nhân chính khiến REQ-001 fail.

**Example:**
```python
# Source: trafilatura docs (https://trafilatura.readthedocs.io/en/latest/usage-python.html)
import trafilatura

def _extract_content(self, html: str, limit: int = 8000) -> str:
    try:
        # Layer 0: trafilatura (highest precision — F1: 0.945)
        traf_text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,   # cho phép fallback nội bộ trafilatura
            output_format="txt",
        )
        if traf_text and len(traf_text.strip()) > 200:
            return traf_text.strip()[:limit]

        # Layer 1: JSON-LD (existing logic)
        soup = BeautifulSoup(html, "html.parser")
        ld_text = self._extract_json_ld_text(soup)
        # ... rest of existing BS4 logic ...
```

### Pattern 2: Tối ưu wait_for_selector timeout trong Playwright

**What:** Giảm timeout `wait_for_selector` từ 5000ms xuống 2000ms cho mỗi selector. Với 12 selectors trong ARTICLE_SELECTORS, trường hợp xấu nhất giảm từ 60s xuống 24s.

**When to use:** Luôn áp dụng. Báo Việt Nam render content trong 1-2s sau DOMContentLoaded.

**Example:**
```python
# Source: playwright_fetcher.py (hiện tại là 5000)
for selector in ARTICLE_SELECTORS:
    try:
        await page.wait_for_selector(selector, timeout=2000)  # giảm từ 5000
        break
    except Exception:
        continue
```

### Pattern 3: playwright-stealth cho Cloudflare bypass

**What:** Áp dụng `stealth_async(page)` sau khi tạo page, trước khi `page.goto()`.

**When to use:** Chỉ khi phát hiện Cloudflare JS challenge response (đã có `_looks_like_block_page()` detection).

**Example:**
```python
# Source: playwright-stealth PyPI (https://pypi.org/project/playwright-stealth/)
from playwright_stealth import stealth_async

async def fetch(self, url: str, timeout: int = 30) -> str:
    # ... existing context setup ...
    page = await context.new_page()
    await stealth_async(page)  # thêm dòng này
    # ... existing goto logic ...
```

### Pattern 4: Per-domain semaphore cho Playwright

**What:** Dùng semaphore riêng cho Playwright (chỉ cho Playwright, không dùng chung với curl_cffi/httpx).

**When to use:** Khi muốn giới hạn concurrent Playwright contexts mà không block các fetch khác.

**Example:**
```python
# Current: self.semaphore = asyncio.Semaphore(10)  — dùng chung cho tất cả
# Better: Playwright-specific semaphore
self._playwright_sem = asyncio.Semaphore(3)  # tối đa 3 browser contexts đồng thời

async def _fetch_playwright_safe(self, url, timeout):
    async with self._playwright_sem:
        return await playwright_fetcher.fetch(url, timeout=timeout)
```

### Anti-Patterns to Avoid

- **wait_for_selector với timeout lớn cho toàn bộ selector list:** Dừng ở selector đầu tiên tìm thấy (đã làm đúng với `break`), nhưng timeout 5000ms mỗi selector quá lớn. Giảm xuống 2000ms.
- **Validation chỉ dựa vào `len > 200` mà không check "- ":** Đã fix. Header (title + source + URL) có thể dài hơn 200 chars mà không có bullet.
- **Gọi trafilatura trong async context mà không wrap trong `asyncio.to_thread`:** trafilatura là sync library, gọi trực tiếp sẽ block event loop nếu có parse nặng. Tuy nhiên, do HTML đã được fetch về (không có I/O), blocking thường < 100ms — chấp nhận được hoặc wrap `to_thread` nếu cần.
- **BS4 selector list quá dài không có priority:** 20 selectors hiện tại thử từ trên xuống dưới — các selector chung như `#content`, `.content` ở cuối nhưng có thể match false positive. trafilatura giải quyết vấn đề này tốt hơn.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Main content extraction từ HTML | Custom BS4 selector list đầy đủ | trafilatura | Benchmark F1: 0.945 vs 0.665; handles boilerplate, ads, sidebars tự động |
| Cloudflare JS challenge bypass | Custom webdriver flag patch | playwright-stealth | Patches nhiều signals (canvas, WebGL, navigator, timezone) không thể manual |
| TLS fingerprint spoofing | Custom HTTP headers | curl_cffi Chrome impersonation | TLS JA3/JA4 fingerprint cần libcurl — không thể replicate bằng Python HTTPx |

**Key insight:** Vấn đề content extraction của báo Việt Nam là "main content vs boilerplate" — đây chính xác là problem trafilatura được thiết kế để giải quyết, không phải CSS selectors.

---

## Common Pitfalls

### Pitfall 1: trafilatura trả về None trên trang cần JS
**What goes wrong:** trafilatura gọi trên HTML trước khi JS chạy (fetch bằng httpx/curl_cffi) → JS-rendered content chưa có → trafilatura extract rỗng → fallback lại BS4 nhưng cũng rỗng
**Why it happens:** trafilatura là pure HTML parser, không execute JS
**How to avoid:** Dùng trafilatura sau Playwright fetch (Playwright đã render JS trước rồi trả HTML), hoặc kết hợp: Playwright fetch → trafilatura extract
**Warning signs:** trafilatura return None hoặc < 100 chars trên JS-heavy sites mà Playwright đã fetch thành công

### Pitfall 2: wait_for_selector timeout cộng dồn
**What goes wrong:** PlaywrightFetcher thử 12 selectors với timeout 5000ms mỗi cái → nếu page không có selector nào trong list → tổng thời gian là 12 * 5s = 60s (timeout vượt quá `timeout` tham số)
**Why it happens:** `page.wait_for_selector` không raise ngay mà chờ hết timeout mới raise exception
**How to avoid:** Giảm timeout xuống 2000ms, hoặc thêm `any_of` để wait cho 1 trong nhiều selectors cùng lúc — Playwright hỗ trợ `page.locator("css1, css2")`
**Warning signs:** Log "❌ Playwright fetch lỗi" với "Timeout" message; thời gian xử lý > 30s/bài

### Pitfall 3: Gemini URL context trả về header-only pass validation
**What goes wrong:** Gemini URL context trả về chỉ title + Nguồn + URL (header) — nếu title dài, tổng len > 150 chars → pass check `len > 150 AND "- " in summary`
**Why it happens:** "- " xuất hiện trong URL (path có gạch ngang) hoặc trong nguồn nếu format có gạch
**How to avoid:** Check có ít nhất 1 dòng bắt đầu bằng "- " (regex: `r'^- .{20,}'` multiline) thay vì chỉ check `"- " in summary`
**Warning signs:** Bài có output ngắn, không có nội dung tóm tắt thực sự dù pass validation

### Pitfall 4: asyncio.Semaphore(10) quá cao cho Playwright
**What goes wrong:** 10 browser contexts đồng thời dùng ~500-1000MB RAM → OOM trên máy thấp config hoặc server
**Why it happens:** Semaphore(10) áp dụng cho tất cả, Playwright contexts nặng hơn curl_cffi nhiều
**How to avoid:** Dùng semaphore riêng cho Playwright (`asyncio.Semaphore(3)`)
**Warning signs:** Server RAM spike khi tóm tắt batch lớn (>= 15 bài)

### Pitfall 5: trafilatura và lxml cần cài cùng nhau
**What goes wrong:** `import trafilatura` thành công nhưng extraction quality kém khi thiếu lxml
**Why it happens:** trafilatura dùng lxml làm parser chính — không có lxml thì dùng html.parser (kém chính xác hơn)
**How to avoid:** `pip install trafilatura[all]` hoặc `pip install trafilatura lxml`
**Warning signs:** trafilatura extract được text nhưng ngắn hơn expected

---

## Code Examples

### trafilatura extract từ HTML string đã có
```python
# Source: trafilatura docs (https://trafilatura.readthedocs.io/en/latest/usage-python.html)
import trafilatura

html = "<html>...</html>"  # HTML đã fetch về

text = trafilatura.extract(
    html,
    include_comments=False,
    include_tables=False,
    output_format="txt",  # hoặc "markdown"
    no_fallback=False,
)
# text là str hoặc None nếu không tìm được content
```

### playwright-stealth async integration
```python
# Source: playwright-stealth PyPI (https://pypi.org/project/playwright-stealth/)
from playwright_stealth import stealth_async

# Thêm vào sau page = await context.new_page()
page = await context.new_page()
await stealth_async(page)
# Sau đó goto như bình thường
await page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
```

### Playwright wait_for_selector với timeout tối ưu
```python
# Cách hiện tại (chậm): mỗi selector timeout 5000ms riêng lẻ
for selector in ARTICLE_SELECTORS:
    try:
        await page.wait_for_selector(selector, timeout=2000)  # giảm từ 5000
        break
    except Exception:
        continue

# Cách tối ưu hơn: dùng CSS selector combined
combined = ", ".join(ARTICLE_SELECTORS[:6])  # top 6 selectors ưu tiên
try:
    await page.wait_for_selector(combined, timeout=3000)  # 1 lần wait, tổng 3s
except Exception:
    pass  # tiếp tục lấy content dù không tìm thấy selector
```

### Validation bullet "- " chặt hơn
```python
import re

def _has_bullet_content(summary: str) -> bool:
    """Kiểm tra có ít nhất 1 dòng bullet thực sự (không phải chỉ URL có gạch)."""
    if not summary:
        return False
    return bool(re.search(r'^- .{20,}', summary, re.MULTILINE))

# Dùng thay cho: "- " in summary
if summary and len(summary.strip()) > 150 and _has_bullet_content(summary):
    return {"category": ..., "text": summary.strip()}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| BeautifulSoup selector-only extraction | JSON-LD + meta tags + BS4 selectors | Current session | Tốt hơn nhưng vẫn thiếu trafilatura |
| httpx-only fetch | Playwright + curl_cffi + httpx | Current session | Tăng đáng kể success rate cho JS-heavy sites |
| Validation `len > 200` | `len > 150 AND "- " in summary` | Current session (BUG_REPORT.md) | Fix false-positive nhưng vẫn có edge case với URL có "-" |
| `og:description` only | `og:description + twitter:description + article:description + name=description` | Current session | Tăng meta text extraction rate |
| gemini-2.0-flash-lite | gemini-3-flash-preview (v1beta) | Current session | URL context tool khả dụng |

**Deprecated/outdated:**
- `google-generativeai` SDK: đã thay bằng direct REST API qua httpx (FastGeminiClient) — nhẹ hơn, không phụ thuộc SDK nặng
- `_excerpt_only_fallback()`: vẫn còn trong code nhưng không được gọi từ main path — cần verify không còn path nào gọi nó ngoài ý muốn

---

## Open Questions

1. **Gemini URL context reliability**
   - What we know: `generate_content_with_url()` dùng `url_context` tool — Gemini tự fetch URL
   - What's unclear: Tỷ lệ thành công thực tế với báo Việt Nam (Gemini server có thể bị block bởi một số báo)
   - Recommendation: Log tỷ lệ "URL context thành công" vs "fallback sang fetch thủ công" để đo — nếu < 50% thì không đáng là Step 1

2. **trafilatura với tiếng Việt**
   - What we know: Benchmark của trafilatura chủ yếu trên tiếng Anh/Pháp/Đức; Vietnamese không được mention trong evaluation
   - What's unclear: F1 score trên báo Việt Nam cụ thể có thể thấp hơn 0.945
   - Recommendation: Test trafilatura trên 5-10 bài từ laodong.vn, dantri.com.vn trước khi deploy; nếu quality tốt thì proceed

3. **Playwright browser version mismatch**
   - What we know: System có playwright 1.40.0 nhưng requirements.txt yêu cầu >=1.44.0; trong venv có thể khác
   - What's unclear: Version trong venv hiện tại là bao nhiêu
   - Recommendation: Verify `pip show playwright` trong venv trước khi plan bước cài playwright-stealth

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | Backend runtime | ✓ | 3.12.12 | — |
| playwright | JS-heavy site fetch | ✓ (system) | 1.40.0 | curl_cffi + httpx |
| curl_cffi | Anti-bot fetch | ✓ | 0.13.0 | httpx |
| beautifulsoup4 | HTML parsing | ✓ | 4.12.2 | — |
| trafilatura | Content extraction (proposed) | ✗ (not installed) | — (2.0.0 available on PyPI) | Existing BS4 logic |
| playwright-stealth | Cloudflare bypass (proposed) | ✗ (not installed) | — (2.0.2 available on PyPI) | Existing stealth script trong PlaywrightFetcher |
| lxml | trafilatura dependency | ✗ (not verified) | — | html.parser (quality giảm) |

**Missing dependencies with no fallback:**
- Không có dependency nào blocking execution — tất cả proposed additions có fallback là existing code.

**Missing dependencies with fallback:**
- trafilatura: không có → existing BS4 selector list vẫn chạy được (quality thấp hơn)
- playwright-stealth: không có → existing `add_init_script` webdriver patch trong PlaywrightFetcher vẫn hoạt động cho hầu hết báo Việt Nam

---

## Validation Architecture

> Không có config.json trong .planning/ — treat nyquist_validation as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (không thấy config trong project) |
| Config file | Không có pytest.ini / pyproject.toml — Wave 0 cần tạo |
| Quick run command | `pytest backend/test_api_v2.py -x -q` |
| Full suite command | `pytest backend/ -x -q` |

File `backend/test_api_v2.py` tồn tại trong project (thấy từ `ls backend/`).

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-001 | Content extract >= 200 chars từ HTML của laodong.vn/dantri | unit | `pytest backend/test_api_v2.py -k "extract" -x` | Cần verify nội dung test |
| REQ-001 | `_extract_content()` trả về text từ HTML fixture của báo Việt Nam | unit | `pytest backend/test_extract.py -x` | ❌ Wave 0 |
| REQ-002 | Mọi output của `_process_single_article` có "- " | unit | `pytest backend/test_summarizer.py::test_bullet_in_output -x` | ❌ Wave 0 |
| REQ-002 | `get_fallback_summary()` luôn có bullet dù excerpt rỗng | unit | `pytest backend/test_summarizer.py::test_fallback_has_bullet -x` | ❌ Wave 0 |
| REQ-003 | Prompt không chứa `[...]` placeholders trong output | integration | `pytest backend/test_prompts.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest backend/test_api_v2.py -x -q`
- **Per wave merge:** `pytest backend/ -x -q`
- **Phase gate:** Full suite green trước khi verify kết quả thực

### Wave 0 Gaps
- [ ] `backend/test_extract.py` — unit tests cho `_extract_content()` với HTML fixtures của báo Việt Nam (covers REQ-001)
- [ ] `backend/test_summarizer.py` — unit tests cho bullet validation, fallback logic (covers REQ-002)
- [ ] `backend/test_prompts.py` — kiểm tra prompt format không có placeholder brackets (covers REQ-003)
- [ ] HTML fixtures: `backend/fixtures/laodong_article.html`, `backend/fixtures/dantri_article.html` — dùng làm input cho unit tests REQ-001

---

## Sources

### Primary (HIGH confidence)
- Codebase trực tiếp: `backend/services/summarizer.py`, `playwright_fetcher.py`, `fast_gemini.py`, `secure_fetcher.py`, `prompts.py`, `config.py` — đọc toàn bộ
- `BUG_REPORT.md` — phân tích root cause đã verified
- `pip3 index versions trafilatura` — version 2.0.0 verified 2026-03-24
- `pip3 index versions playwright-stealth` — version 2.0.2 verified 2026-03-24

### Secondary (MEDIUM confidence)
- [Trafilatura 2.0.0 docs](https://trafilatura.readthedocs.io/en/latest/usage-python.html) — API usage patterns, extract() parameters
- [trafilatura evaluation benchmark](https://trafilatura.readthedocs.io/en/latest/evaluation.html) — F1 0.945 score claim
- [playwright-stealth PyPI](https://pypi.org/project/playwright-stealth/) — stealth_async usage pattern
- [Kameleo: How to Bypass Cloudflare with Playwright 2025](https://kameleo.io/blog/how-to-bypass-cloudflare-with-playwright)

### Tertiary (LOW confidence — WebSearch, cần validate)
- Benchmark F1 numbers: "BeautifulSoup F1 0.665" — từ article-extraction-benchmark repo, chưa verify trực tiếp trên Vietnamese content
- Playwright concurrent contexts RAM estimate "50-100MB each" — từ WebSearch community articles

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified từ requirements.txt, pip install status, và codebase
- Architecture patterns: HIGH — dựa trực tiếp trên code analysis
- Pitfalls: HIGH (bugs 1-3) / MEDIUM (pitfall 4-5) — bugs 1-3 documented trong BUG_REPORT.md, pitfall 4-5 từ code analysis + WebSearch
- trafilatura quality on Vietnamese: MEDIUM — benchmark chung tốt nhưng chưa test Vietnamese specifically

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (libraries stable; Gemini model naming có thể thay đổi nhanh hơn)
