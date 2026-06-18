import asyncio
import feedparser
import html
import httpx
from typing import List, Dict, Optional
from datetime import datetime, time
from dateutil import parser as date_parser
import re
from zoneinfo import ZoneInfo
from services.secure_fetcher import secure_fetcher

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def _normalize_gmt_offset(pub_str: str) -> str:
    """
    Fix dateutil misparse of 'GMT+N' timezone strings.

    dateutil follows POSIX convention where GMT+7 means UTC-7 (west of UTC).
    But RSS feeds (RFC 2822) intend GMT+7 to mean UTC+7 (east of UTC, i.e. Vietnam).

    This function replaces 'GMT+7' -> '+0700' and 'GMT-5' -> '-0500' so that
    dateutil parses them with the correct sign.
    """
    def fix_gmt(m: re.Match) -> str:
        sign = m.group(1)
        hours = int(m.group(2))
        return f"{sign}{hours:02d}00"

    return re.sub(r"GMT([+-])(\d+)", fix_gmt, pub_str)

class RSSFetcher:
    """
    Fetches RSS feeds and filters articles by date and time range
    Replaces the ai_browser + extract + second ai_llm nodes
    Uses Python datetime for accurate filtering instead of AI
    """
    
    # Map RSS feed URLs to newspaper display names
    NEWSPAPER_SOURCES = {
        "laodong.vn": "LAO ĐỘNG",
        "dantri.com.vn": "DÂN TRÍ",
        "vtv.vn": "VTV NEWS",
        "hanoimoi.vn": "HÀ NỘI MỚI",
        "sggp.org.vn": "SGGP",
        "vietnamplus.vn": "VIETNAMPLUS",
        "tienphong.vn": "TIỀN PHONG",
        "vnexpress.net": "VNS EXPRESS",
        "tuoitre.vn": "TUỔI TRẺ",
        "cafef.vn": "CAFEF",
        "vov.vn": "VOV",
        "baotintuc.vn": "BÁO TIN TỨC",
        "thanhnien.vn": "THANH NIÊN",
    }

    @staticmethod
    def _clean_description(raw_description: str) -> str:
        """
        Chuẩn hóa mô tả lấy từ RSS:
        - Bỏ HTML tags
        - Chuẩn hóa whitespace
        - Tránh trường hợp dấu ba chấm bị lặp (....)
        """
        if not raw_description:
            return ""

        text = re.sub(r"<[^>]+>", " ", raw_description)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()

        # Chuẩn hóa phần kết thúc nếu RSS đã cắt ngắn
        text = re.sub(r"\.{4,}$", "…", text)
        text = re.sub(r"…{2,}$", "…", text)
        return text
    
    async def fetch_and_filter(
        self,
        rss_urls: List[str],
        target_date: str,
        time_range: str
    ) -> List[Dict]:
        """
        Fetch RSS feeds and filter articles by date and time
        
        Args:
            rss_urls: List of RSS feed URLs
            target_date: Date in DD/MM/YYYY format
            time_range: Time range like "6h00 đến 8h00"
            
        Returns:
            List of filtered articles with metadata
        """
        # Parse target date
        try:
            day, month, year = target_date.split("/")
            target_dt = datetime(int(year), int(month), int(day))
        except:
            raise ValueError(f"Invalid date format: {target_date}. Expected DD/MM/YYYY")
        
        # Parse time range
        start_time, end_time = self._parse_time_range(time_range)
        
        all_articles = []
        
        # Separate URLs by fetch strategy
        hanoimoi_html_urls = []  # scrape HTML directly (RSS blocked by Cloudflare)
        vov_html_urls = []       # scrape HTML directly (no RSS available)
        secure_urls = []
        normal_urls = []

        for url in rss_urls:
            if 'hanoimoi.vn' in url.lower() and '/rss/' not in url.lower():
                hanoimoi_html_urls.append(url)
            elif 'vov.vn' in url.lower() and '/rss/' not in url.lower():
                vov_html_urls.append(url)
            elif 'laodong.vn' in url.lower():
                secure_urls.append(url)
            else:
                normal_urls.append(url)

        # Scrape Hà Nội Mới HTML (RSS is Cloudflare-blocked)
        if hanoimoi_html_urls:
            print(f"🗞️ Scraping Hà Nội Mới HTML for {len(hanoimoi_html_urls)} category pages")
            hnm_articles = await self._scrape_hanoimoi_html(
                hanoimoi_html_urls, target_dt, start_time, end_time
            )
            all_articles.extend(hnm_articles)

        # Scrape VOV HTML (no RSS available)
        if vov_html_urls:
            print(f"📻 Scraping VOV HTML for {len(vov_html_urls)} category pages")
            vov_articles = await self._scrape_vov_html(
                vov_html_urls, target_dt, start_time, end_time
            )
            all_articles.extend(vov_articles)
        
        # Fetch Secure URLs (Lao Dong with anti-bot protection)
        if secure_urls:
            print(f"🛡️ Using Secure Fetcher for {len(secure_urls)} URLs (anti-bot protection)")
            try:
                secure_contents = await secure_fetcher.fetch_multiple_rss(secure_urls)
                
                for rss_url, content in secure_contents.items():
                    if content:
                        feed = feedparser.parse(content)
                        print(f"   ✅ {rss_url}: {len(feed.entries)} entries")

                        # Hà Nội Mới: double-escaped CDATA → feedparser trả về empty description/image
                        # Giải pháp: extract trực tiếp từ raw XML bằng regex
                        hanoimoi_extras: dict = {}
                        if 'hanoimoi' in rss_url:
                            # Extract từng <item> block và lấy link, img src, description text
                            for item_xml in re.findall(r'<item>(.*?)</item>', content, re.DOTALL):
                                link_m = re.search(r'<link>([^<]+)</link>', item_xml)
                                if not link_m:
                                    continue
                                item_url = link_m.group(1).strip()
                                # Unescape CDATA content để extract
                                cdata_m = re.search(r'&lt;!\[CDATA\[(.*?)\]\]&gt;', item_xml, re.DOTALL)
                                if cdata_m:
                                    inner = html.unescape(cdata_m.group(1))
                                    img_m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', inner)
                                    text = re.sub(r'<[^>]+>', ' ', inner).strip()
                                    text = re.sub(r'\s+', ' ', text)
                                    hanoimoi_extras[item_url] = {
                                        'thumbnail': img_m.group(1) if img_m else '',
                                        'description': text,
                                    }

                        # Process each entry
                        for entry in feed.entries:
                            article = self._process_entry(
                                entry,
                                target_dt,
                                start_time,
                                end_time,
                                rss_url
                            )
                            if article:
                                # Patch Hà Nội Mới extras nếu có
                                if 'hanoimoi' in rss_url:
                                    extras = hanoimoi_extras.get(article['url'], {})
                                    if extras.get('thumbnail'):
                                        article['thumbnail'] = extras['thumbnail']
                                    if extras.get('description') and not article['description']:
                                        article['description'] = extras['description']
                                all_articles.append(article)
                    else:
                        print(f"   ❌ {rss_url}: No content fetched")
            except Exception as e:
                print(f"❌ Secure Fetcher error: {str(e)}")
        
        # Fetch normal URLs with httpx — concurrent với asyncio.gather
        if normal_urls:
            print(f"⚡ Using HTTP for {len(normal_urls)} URLs (concurrent, no anti-bot)")

            # Headers to bypass basic anti-bot
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            async def _fetch_one(client: httpx.AsyncClient, rss_url: str) -> List[Dict]:
                try:
                    response = await client.get(rss_url)
                    feed = feedparser.parse(response.text)
                    print(f"   ✅ {rss_url}: {len(feed.entries)} entries")
                    articles = []
                    for entry in feed.entries:
                        article = self._process_entry(entry, target_dt, start_time, end_time, rss_url)
                        if article:
                            articles.append(article)
                    return articles
                except Exception as e:
                    print(f"   ❌ {rss_url}: {str(e)}")
                    return []

            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers=headers
            ) as client:
                tasks = []
                for url in normal_urls:
                    tasks.append(_fetch_one(client, url))
                results = await asyncio.gather(*tasks)
                for article_list in results:
                    all_articles.extend(article_list)
        
        return all_articles
    
    def _parse_time_range(self, time_range: str) -> tuple:
        """
        Parse Vietnamese time range string to time objects
        Example: "6h00 đến 8h00" -> (time(6, 0), time(8, 0))
        """
        # Extract hours and minutes using regex
        pattern = r"(\d+)h(\d+)\s*đến\s*(\d+)h(\d+)"
        match = re.search(pattern, time_range)
        
        if not match:
            raise ValueError(f"Invalid time range format: {time_range}")
        
        start_hour, start_min, end_hour, end_min = map(int, match.groups())
        
        start_time = time(start_hour, start_min)
        end_time = time(end_hour, end_min)
        
        return start_time, end_time

    async def _scrape_vov_html(
        self,
        urls: list,
        target_dt: datetime,
        start_time: time,
        end_time: time,
    ) -> list:
        """Scrape VOV category pages (HTML) — no RSS available on vov.vn.

        Strategy:
        1. Fetch category listing page → extract article URLs, titles, thumbnails
        2. Batch-fetch article detail pages concurrently → extract
           `article:published_time` meta tag for accurate date/time filtering
        3. Filter by target date + time range
        """
        VOV_CATEGORY_MAP = {
            "xa-hoi": "XÃ HỘI",
            "the-gioi": "THẾ GIỚI",
            "kinh-te": "KINH TẾ",
            "phap-luat": "PHÁP LUẬT",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        }

        import asyncio as _asyncio
        import os as _os

        cf_proxy_url = _os.environ.get("CF_PROXY_URL", "").rstrip("/")
        if cf_proxy_url:
            print(f"🔀 Using CF Worker proxy for VOV scrape")

        def _proxy(url: str) -> str:
            """Wrap URL with CF Worker proxy if configured."""
            return f"{cf_proxy_url}/?url={url}" if cf_proxy_url else url

        async def fetch_listing(client: httpx.AsyncClient, url: str) -> list:
            """Fetch category page, extract article cards (URL, title, thumbnail)."""
            slug = url.rstrip("/").split("/")[-1]
            category = VOV_CATEGORY_MAP.get(slug, slug.upper().replace("-", " "))
            try:
                resp = await client.get(_proxy(url))
                if resp.status_code != 200:
                    print(f"   ⚠️ VOV {url}: status {resp.status_code}")
                    return []
                content = resp.text
                cards = []
                # Split by article-card div starts to extract each card block
                # Limit to first 20 cards (newest articles appear first)
                card_starts = [m.start() for m in re.finditer(r'<div class="article-card', content)][:20]
                for i, start in enumerate(card_starts):
                    end = card_starts[i + 1] if i + 1 < len(card_starts) else start + 3000
                    block = content[start:end]
                    # Extract href (relative or absolute)
                    link_m = re.search(r'href="(/[^"]+\.vov)"', block)
                    if not link_m:
                        continue
                    article_url = "https://vov.vn" + link_m.group(1)

                    # Extract title from card-title or alt attribute
                    title_m = re.search(r'class="[^"]*card-title[^"]*"[^>]*>\s*([^<]+)', block, re.DOTALL)
                    if not title_m:
                        title_m = re.search(r'alt="([^"]+)"', block)
                    title = html.unescape(title_m.group(1).strip()) if title_m else ""

                    # Extract thumbnail: prefer largest srcset source, fall back to img src
                    thumb_m = re.search(r'<img[^>]+src="([^"]+)"', block)
                    thumbnail = thumb_m.group(1) if thumb_m else ""

                    cards.append({
                        "url": article_url,
                        "title": title,
                        "thumbnail": thumbnail,
                        "category": category,
                        "source": "VOV",
                    })
                print(f"   VOV listing {url}: {len(cards)} cards found")
                return cards
            except Exception as e:
                print(f"❌ VOV listing error {url}: {e}")
                return []

        async def fetch_article_date(client: httpx.AsyncClient, article_url: str, semaphore: _asyncio.Semaphore) -> str:
            """Fetch article detail page, return ISO 8601 published_time or empty string."""
            async with semaphore:
                try:
                    resp = await client.get(_proxy(article_url))
                    if resp.status_code != 200:
                        return ""
                    # Extract article:published_time meta tag
                    m = re.search(
                        r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']',
                        resp.text,
                    )
                    if not m:
                        # Try reversed attribute order
                        m = re.search(
                            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']article:published_time["\']',
                            resp.text,
                        )
                    return m.group(1) if m else ""
                except Exception:
                    return ""

        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers=headers,
        ) as client:
            # Step 1: fetch all category listings concurrently
            listing_results = await _asyncio.gather(*[fetch_listing(client, u) for u in urls])
            all_cards = []
            for cards in listing_results:
                all_cards.extend(cards)

            if not all_cards:
                return []

            # Step 2: fetch article detail pages concurrently (max 8 at a time to avoid rate-limit)
            semaphore = _asyncio.Semaphore(8)
            date_strings = await _asyncio.gather(*[
                fetch_article_date(client, card["url"], semaphore) for card in all_cards
            ])

        # Step 3: filter by date + time range
        articles = []
        for card, date_str in zip(all_cards, date_strings):
            if not date_str:
                continue
            try:
                pub_dt = date_parser.parse(date_str)
                if pub_dt.tzinfo:
                    pub_dt = pub_dt.astimezone(VN_TZ)
                else:
                    from datetime import timezone as _tz
                    pub_dt = pub_dt.replace(tzinfo=_tz.utc).astimezone(VN_TZ)
            except Exception:
                continue

            if pub_dt.date() != target_dt.date():
                continue
            pub_time = pub_dt.time().replace(tzinfo=None)
            if end_time >= start_time:
                if not (start_time <= pub_time <= end_time):
                    continue
            else:
                if not (pub_time >= start_time or pub_time <= end_time):
                    continue

            articles.append({
                **card,
                "published_at": pub_dt.strftime("%H:%M %d/%m/%Y"),
                "description": "",
            })

        print(f"   ✅ VOV total: {len(articles)} bài trong khung giờ")
        return articles

    async def _scrape_hanoimoi_html(
        self,
        urls: list,
        target_dt: datetime,
        start_time: time,
        end_time: time,
    ) -> list:
        """Scrape Hà Nội Mới category pages (HTML) — RSS is Cloudflare-blocked."""
        CATEGORY_MAP = {
            "xa-hoi": "XÃ HỘI",
            "the-gioi": "THẾ GIỚI",
            "phap-luat": "PHÁP LUẬT",
            "kinh-te": "KINH TẾ",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        }
        articles = []

        import os
        proxy_url = os.environ.get("WEBSHARE_PROXY_URL", "")
        proxy_kwargs = {"proxy": proxy_url} if proxy_url else {}
        if proxy_url:
            print(f"🔀 Using Webshare proxy for hanoimoi scrape")

        async def fetch_html_via_playwright(url: str) -> str:
            """Dùng Playwright để vượt Cloudflare JS challenge."""
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                print("⚠️ Playwright not installed")
                return ""
            try:
                async with async_playwright() as pw:
                    browser = await pw.chromium.launch(
                        headless=True,
                        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                              "--disable-blink-features=AutomationControlled"],
                    )
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        locale="vi-VN",
                        extra_http_headers={"Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"},
                    )
                    page = await context.new_page()
                    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(8000)
                    content = await page.content()
                    await browser.close()
                    print(f"   [Playwright] hanoimoi HTML fetched, len={len(content)}")
                    return content
            except Exception as e:
                print(f"❌ Playwright hanoimoi error: {e}")
                return ""

        async def fetch_one(url):
            slug = url.rstrip("/").split("/")[-1]
            category = CATEGORY_MAP.get(slug, slug.upper().replace("-", " "))
            try:
                async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers, **proxy_kwargs) as client:
                    resp = await client.get(url)
                    content = resp.text
                # Detect Cloudflare block → fallback chain: cloudscraper → Playwright
                if "Just a moment" in content or "Chờ một chút" in content or "cf-browser-verification" in content or resp.status_code in (403, 503):
                    print(f"⚠️ hanoimoi blocked (status {resp.status_code}), trying cloudscraper...")
                    try:
                        import cloudscraper as _cs
                        import asyncio as _asyncio
                        scraper = _cs.create_scraper()
                        _resp = await _asyncio.get_event_loop().run_in_executor(
                            None, lambda: scraper.get(url, timeout=30)
                        )
                        if _resp.status_code == 200 and "b-grid" in _resp.text:
                            print(f"   ✅ cloudscraper bypassed CF for {url}")
                            content = _resp.text
                        else:
                            print(f"   ⚠️ cloudscraper failed (status {_resp.status_code}), trying Playwright...")
                            content = await fetch_html_via_playwright(url)
                    except Exception as _e:
                        print(f"   ⚠️ cloudscraper error: {_e}, trying Playwright...")
                        content = await fetch_html_via_playwright(url)
                if not content:
                    return []
                # Parse b-grid blocks
                result = []
                for block in re.findall(r'<div class="b-grid">(.*?)</div>\s*</div>\s*</div>', content, re.DOTALL):
                    link_m = re.search(r'href="(https://hanoimoi\.vn/[^"]+\.html)"', block)
                    title_m = re.search(r'b-grid__title[^>]*>.*?<a[^>]*>([^<]+)</a>', block, re.DOTALL)
                    img_m = re.search(r'<img[^>]+src="([^"]+)"', block)
                    date_m = re.search(r'b-grid__time">([^<]+)<', block)
                    if not (link_m and title_m and date_m):
                        continue
                    # Parse date: "17/06/2026 - 11:02"
                    try:
                        pub_dt = datetime.strptime(date_m.group(1).strip(), "%d/%m/%Y - %H:%M")
                        pub_dt = pub_dt.replace(tzinfo=VN_TZ)
                    except ValueError:
                        continue
                    if pub_dt.date() != target_dt.date():
                        continue
                    pub_time = pub_dt.time().replace(tzinfo=None)
                    if end_time >= start_time:
                        if not (start_time <= pub_time <= end_time):
                            continue
                    else:
                        if not (pub_time >= start_time or pub_time <= end_time):
                            continue
                    result.append({
                        "url": link_m.group(1),
                        "title": html.unescape(title_m.group(1).strip()),
                        "category": category,
                        "published_at": pub_dt.strftime("%H:%M %d/%m/%Y"),
                        "description": "",
                        "source": "HÀ NỘI MỚI",
                        "thumbnail": img_m.group(1) if img_m else "",
                    })
                print(f"   ✅ hanoimoi {url}: {len(result)} bài")
                return result
            except Exception as e:
                print(f"❌ hanoimoi scrape error {url}: {e}")
                return []

        import asyncio as _asyncio
        results = await _asyncio.gather(*[fetch_one(u) for u in urls])
        for r in results:
            articles.extend(r)
        return articles

    def _process_entry(
        self,
        entry: Dict,
        target_date: datetime,
        start_time: time,
        end_time: time,
        rss_url: str
    ) -> Optional[Dict]:
        """
        Process a single RSS entry and filter by date/time
        Category is extracted directly from RSS URL path
        """
        try:
            # Parse publication date
            pub_date_str = entry.get("published", "")
            if not pub_date_str:
                return None
            
            # Normalize 'GMT+N' timezone strings before parsing.
            # dateutil interprets GMT+7 as UTC-7 (POSIX convention), but RSS feeds
            # (RFC 2822) mean UTC+7. _normalize_gmt_offset flips the sign so dateutil
            # produces the correct offset.
            pub_date_str = _normalize_gmt_offset(pub_date_str)

            # Parse the date string (handles various formats)
            pub_date = date_parser.parse(pub_date_str)

            # Convert to Vietnam timezone (UTC+7) for correct date/time comparison
            if pub_date.tzinfo is not None:
                pub_date = pub_date.astimezone(VN_TZ)
            else:
                # Assume UTC if no timezone info
                from datetime import timezone
                pub_date = pub_date.replace(tzinfo=timezone.utc).astimezone(VN_TZ)

            # Check if date matches
            if pub_date.date() != target_date.date():
                return None

            # Check if time is within range
            # Handle both normal ranges (6h-8h) and cross-midnight ranges (21h-23h59, 0h-6h)
            pub_time = pub_date.time().replace(tzinfo=None)
            
            # Normal time range (start < end, e.g., 6h00 to 8h00)
            if end_time >= start_time:
                if not (start_time <= pub_time <= end_time):
                    return None
            # Cross-midnight range (end < start, e.g., 21h00 to 6h00) - NOT USED currently
            # but kept for future flexibility
            else:
                if not (pub_time >= start_time or pub_time <= end_time):
                    return None
            
            # Extract newspaper source from RSS URL
            source = self._extract_source(rss_url)
            
            # Extract category from RSS URL
            category = self._extract_category_from_url(rss_url)
            
            # Extract thumbnail from RSS entry
            thumbnail = self._extract_thumbnail(entry)
            
            # Extract article data
            raw_description = entry.get("description", "") or entry.get("summary", "")
            return {
                "url": entry.get("link", ""),
                "title": html.unescape(entry.get("title", "")),
                "category": category,
                "published_at": pub_date.astimezone(VN_TZ).strftime("%H:%M %d/%m/%Y"),
                "description": self._clean_description(raw_description),
                "source": source,
                "thumbnail": thumbnail,
            }
            
        except Exception as e:
            print(f"Error processing entry: {str(e)}")
            return None
    
    def _extract_source(self, rss_url: str) -> str:
        """
        Extract newspaper source name from RSS URL
        """
        for domain, source_name in self.NEWSPAPER_SOURCES.items():
            if domain in rss_url:
                return source_name
        # Fallback: extract domain from URL
        try:
            from urllib.parse import urlparse
            domain = urlparse(rss_url).netloc
            return domain.replace("www.", "").upper()
        except:
            return "UNKNOWN"
    
    def _extract_category_from_url(self, rss_url: str) -> str:
        """
        Extract category from RSS URL path
        Examples:
        - https://tienphong.vn/rss/phap-luat-12.rss -> PHÁP LUẬT
        - https://laodong.vn/rss/kinh-doanh.rss -> KINH TẾ
        - https://vov.vn/xa-hoi -> XÃ HỘI
        """
        url_lower = rss_url.lower()

        # vov.vn HTML category pages: path is the category slug
        VOV_HTML_CATEGORY_MAP = {
            "xa-hoi": "XÃ HỘI",
            "the-gioi": "THẾ GIỚI",
            "kinh-te": "KINH TẾ",
            "phap-luat": "PHÁP LUẬT",
        }
        if "vov.vn" in url_lower and "/rss/" not in url_lower:
            slug = url_lower.rstrip("/").split("/")[-1]
            if slug in VOV_HTML_CATEGORY_MAP:
                return VOV_HTML_CATEGORY_MAP[slug]

        # Category mapping from URL keywords
        if any(keyword in url_lower for keyword in ['phap-luat', 'phapluat', 'phap_luat']):
            return "PHÁP LUẬT"
        elif any(keyword in url_lower for keyword in ['kinh-te', 'kinhte', 'kinh-doanh', 'kinhdoanh', 'kinh_te']):
            return "KINH TẾ"
        elif any(keyword in url_lower for keyword in ['xa-hoi', 'xahoi', 'doi-song', 'doisong', 'xa_hoi', 'thoi-su', 'thoisu']):
            return "XÃ HỘI"
        elif any(keyword in url_lower for keyword in ['the-gioi', 'thegioi', 'the_gioi', 'quoc-te', 'quocte']):
            return "THẾ GIỚI"
        else:
            # Default to XÃ HỘI if cannot determine
            return "XÃ HỘI"
    
    
    def _extract_thumbnail(self, entry: Dict) -> str:
        """
        Extract thumbnail/image URL from RSS entry
        Checks multiple possible locations: media:content, enclosure, description
        """
        # Check media:content (common in RSS 2.0)
        if hasattr(entry, 'media_content') and entry.media_content:
            return entry.media_content[0].get('url', '')
        
        # Check media:thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0].get('url', '')
        
        # Check enclosure (podcasts/media)
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    return enclosure.get('href', '')
        
        # Try to extract image from description HTML
        description = entry.get('description', '') or entry.get('summary', '')
        if description:
            # Look for img tags
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description)
            if img_match:
                return img_match.group(1)
        
        return ""

rss_fetcher = RSSFetcher()
