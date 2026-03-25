"""
Playwright fetcher - dùng browser headless để đọc các trang chặn bot mạnh.
Chỉ được gọi khi curl_cffi và httpx đều thất bại.
"""
import asyncio
from typing import Optional

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ playwright không khả dụng. Cài: pip install playwright && playwright install chromium")

# Selector bài báo phổ biến của báo Việt Nam
ARTICLE_SELECTORS = [
    ".fck_detail", ".detail__content", ".cms-body", ".article-body",
    ".content-detail", ".detail-content", ".post-content", ".entry-content",
    "#article-body", "article", '[role="main"]', ".sapo",
]


class PlaywrightFetcher:
    _browser: Optional["Browser"] = None
    _pw = None
    _lock = asyncio.Lock()

    async def _get_browser(self) -> Optional["Browser"]:
        if not PLAYWRIGHT_AVAILABLE:
            return None
        async with self._lock:
            if self._browser is None or not self._browser.is_connected():
                self._pw = await async_playwright().start()
                self._browser = await self._pw.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
        return self._browser

    async def fetch(self, url: str, timeout: int = 30) -> str:
        """
        Fetch HTML bằng Playwright với browser behavior thực tế.
        Trả về HTML string, hoặc "" nếu lỗi.
        """
        if not PLAYWRIGHT_AVAILABLE:
            return ""

        context: Optional["BrowserContext"] = None
        try:
            browser = await self._get_browser()
            if browser is None:
                return ""

            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="vi-VN",
                viewport={"width": 1280, "height": 900},
                # Ẩn dấu hiệu automation
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Upgrade-Insecure-Requests": "1",
                },
            )

            # Ẩn webdriver flag
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            page = await context.new_page()

            # Chặn tài nguyên nặng nhưng GIỮ stylesheet (cần cho một số site render content)
            await page.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type in ("image", "media", "font")
                else route.continue_(),
            )

            # Load trang, chờ đến khi network ổn định
            try:
                await page.goto(
                    url,
                    timeout=timeout * 1000,
                    wait_until="domcontentloaded",
                )
            except Exception:
                # Nếu timeout khi load, vẫn thử lấy content hiện có
                pass

            # Thử chờ selector bài báo xuất hiện (tối đa 2s)
            for selector in ARTICLE_SELECTORS:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    break  # Tìm thấy, dừng
                except Exception:
                    continue

            # Scroll nhẹ để trigger lazy-load content
            await page.evaluate("window.scrollBy(0, 400)")
            await page.wait_for_timeout(800)

            html = await page.content()
            return html or ""

        except Exception as e:
            print(f"❌ Playwright fetch lỗi ({url[:60]}): {e}")
            return ""
        finally:
            if context:
                await context.close()

    async def close(self):
        if self._browser and self._browser.is_connected():
            await self._browser.close()
            self._browser = None


playwright_fetcher = PlaywrightFetcher()
