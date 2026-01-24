import feedparser
import httpx
from typing import List, Dict, Optional
from datetime import datetime, time
from dateutil import parser as date_parser
import re

class RSSFetcher:
    """
    Fetches RSS feeds and filters articles by date and time range
    Replaces the ai_browser + extract + second ai_llm nodes
    Uses Python datetime for accurate filtering instead of AI
    """
    
    # Map RSS feed URLs to newspaper display names
    NEWSPAPER_SOURCES = {
        "laodong.vn": "LÃO ĐỘNG",
        "dantri.com.vn": "DÂN TRÍ",
        "vtv.vn": "VTV NEWS",
        "hanoimoi.vn": "HÀ NỘI MỚI",
        "sggp.org.vn": "SGGP",
        "vietnamplus.vn": "VIETNAMPLUS",
        "tienphong.vn": "TIỀN PHONG",
        "vnexpress.net": "VNS EXPRESS",
        "tuoitre.vn": "TUỔI TRẺ",
        "cafef.vn": "CAFEF",
    }
    
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
        
        # Fetch each RSS feed
        async with httpx.AsyncClient(timeout=30.0) as client:
            for rss_url in rss_urls:
                try:
                    response = await client.get(rss_url)
                    feed = feedparser.parse(response.text)
                    
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
                            
                except Exception as e:
                    print(f"Error fetching {rss_url}: {str(e)}")
                    continue
        
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
            
            # Parse the date string (handles various formats)
            pub_date = date_parser.parse(pub_date_str)
            
            # Check if date matches
            if pub_date.date() != target_date.date():
                return None
            
            # Check if time is within range
            pub_time = pub_date.time()
            if not (start_time <= pub_time <= end_time):
                return None
            
            # Extract newspaper source from RSS URL
            source = self._extract_source(rss_url)
            
            # Extract category from RSS URL
            category = self._extract_category_from_url(rss_url)
            
            # Extract thumbnail from RSS entry
            thumbnail = self._extract_thumbnail(entry)
            
            # Extract article data
            return {
                "url": entry.get("link", ""),
                "title": entry.get("title", ""),
                "category": category,
                "published_at": pub_date.strftime("%H:%M %d/%m/%Y"),
                "description": entry.get("description", ""),
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
            import re
            # Look for img tags
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description)
            if img_match:
                return img_match.group(1)
        
        return ""

rss_fetcher = RSSFetcher()
