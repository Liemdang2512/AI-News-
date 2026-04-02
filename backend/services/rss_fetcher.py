import asyncio
import feedparser
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
        
        # Separate URLs by whether they need Secure Fetcher (anti-bot protection)
        secure_urls = []
        normal_urls = []
        
        for url in rss_urls:
            # Lao Dong and Hanoi Moi need secure fetcher (anti-bot or IP blocking)
            if 'laodong.vn' in url.lower() or 'hanoimoi.vn' in url.lower():
                secure_urls.append(url)
            else:
                normal_urls.append(url)
        
        # Fetch Secure URLs (Lao Dong with anti-bot protection)
        if secure_urls:
            print(f"🛡️ Using Secure Fetcher for {len(secure_urls)} URLs (anti-bot protection)")
            try:
                secure_contents = await secure_fetcher.fetch_multiple_rss(secure_urls)
                
                for rss_url, content in secure_contents.items():
                    if content:
                        feed = feedparser.parse(content)
                        print(f"   ✅ {rss_url}: {len(feed.entries)} entries")
                        
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
                results = await asyncio.gather(*[_fetch_one(client, url) for url in normal_urls])
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
                "title": entry.get("title", ""),
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
        """
        url_lower = rss_url.lower()
        
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
