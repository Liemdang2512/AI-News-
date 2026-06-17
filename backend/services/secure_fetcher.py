"""
Secure RSS fetcher using curl_cffi to bypass anti-bot protection (Lao Dong, etc.)
Replaces the heavy Playwright implementation.
Falls back to httpx if curl_cffi is not available (Render/Vercel compatibility).
"""

from typing import Dict, List, Optional
import asyncio
import httpx

# Try to import curl_cffi, fallback to httpx if not available
try:
    from curl_cffi.requests import AsyncSession
    CURL_CFFI_AVAILABLE = True
except ImportError:
    print("⚠️ curl_cffi not available, falling back to httpx")
    CURL_CFFI_AVAILABLE = False

class SecureRSSFetcher:
    """
    Fetches RSS feeds using curl_cffi (impersonating Chrome) to bypass anti-bot protection
    Lightweight alternative to Playwright.
    """
    
    def __init__(self):
        # Impersonate recent Chrome version
        self.impersonate = "chrome120"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Upgrade-Insecure-Requests': '1',
        }
        
    async def fetch_rss(self, url: str, timeout: int = 30) -> str:
        """
        Fetch RSS feed content using curl_cffi (with httpx fallback)
        
        Args:
            url: RSS feed URL
            timeout: Timeout in seconds
            
        Returns:
            RSS feed content as string
        """
        # Use curl_cffi if available, otherwise fallback to httpx
        if CURL_CFFI_AVAILABLE:
            try:
                async with AsyncSession(impersonate=self.impersonate, headers=self.headers) as session:
                    response = await session.get(url, timeout=timeout, allow_redirects=True)

                    # Check for cookie challenge (Lao Dong specific)
                    # Response usually contains: document.cookie="KEY=VALUE"+...
                    if "document.cookie" in response.text and "window.location.reload" in response.text:
                        import re
                        # Extract cookie key and value
                        # Look for pattern: document.cookie="KEY=VALUE"
                        # Simple regex to catch the first assignment
                        match = re.search(r'document\.cookie="([^"]+)"', response.text)
                        if match:
                            cookie_str = match.group(1)
                            if "=" in cookie_str:
                                key, value = cookie_str.split("=", 1)
                                # Clean up value (sometimes has extra chars if not parsed perfectly, but usually clean)
                                # Add cookie to session
                                session.cookies.set(key, value)

                                print(f"🔄 Detected cookie challenge for {url}. Retrying with cookie: {key}={value[:10]}...")
                                # Retry request
                                response = await session.get(url, timeout=timeout)

                    content = response.text
                    if content and len(content.strip()) > 100:
                        # Verify it's actually RSS/XML, not a Cloudflare challenge or error page
                        stripped = content.strip()
                        if stripped.startswith('<?xml') or stripped.startswith('<rss') or stripped.startswith('<feed'):
                            return content
                        print(f"⚠️ curl_cffi got non-RSS response for {url} (likely Cloudflare block), trying httpx fallback")
                    else:
                        print(f"⚠️ curl_cffi returned empty/short response for {url}, trying httpx fallback")
            except Exception as e:
                print(f"⚠️ curl_cffi error for {url}: {str(e)}, trying httpx fallback")

        # Fallback to httpx (for Vercel/serverless OR when curl_cffi fails/is unavailable)
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                headers=self.headers
            ) as client:
                response = await client.get(url)
                content = response.text
                stripped = content.strip()
                if stripped.startswith('<?xml') or stripped.startswith('<rss') or stripped.startswith('<feed'):
                    return content
                print(f"⚠️ httpx got non-RSS response for {url}, trying rss2json proxy")
        except Exception as e:
            print(f"⚠️ httpx error for {url}: {str(e)}, trying rss2json proxy")

        # Last resort: rss2json.com proxy — bypasses Cloudflare datacenter IP blocks
        print(f"🔄 Trying rss2json.com proxy for {url}...")
        return await self._fetch_via_rss2json_proxy(url, timeout)

    async def _fetch_via_rss2json_proxy(self, url: str, timeout: int = 30) -> str:
        """Fetch RSS via rss2json.com public API (works from Railway/datacenter IPs blocked by Cloudflare)"""
        import urllib.parse
        import html as _html
        proxy_url = f"https://api.rss2json.com/v1/api.json?rss_url={urllib.parse.quote(url, safe='')}"
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(proxy_url)
                data = response.json()
                if data.get('status') == 'ok' and data.get('items'):
                    print(f"   ✅ rss2json proxy: {len(data['items'])} items for {url}")
                    return self._rss2json_to_rss_xml(data)
                print(f"⚠️ rss2json proxy returned status={data.get('status')} for {url}")
        except Exception as e:
            print(f"❌ rss2json proxy error for {url}: {e}")
        return ""

    def _rss2json_to_rss_xml(self, data: dict) -> str:
        """Convert rss2json API JSON response to RSS XML for feedparser compatibility"""
        import html as _html
        lines = ['<?xml version="1.0" encoding="utf-8"?>', '<rss version="2.0"><channel>']
        feed = data.get('feed', {})
        lines.append(f"<title>{_html.escape(feed.get('title', ''))}</title>")
        for item in data.get('items', []):
            lines.append('<item>')
            lines.append(f"<title><![CDATA[{item.get('title', '')}]]></title>")
            lines.append(f"<link>{_html.escape(item.get('link', ''))}</link>")
            # rss2json returns pubDate in "YYYY-MM-DD HH:MM:SS" UTC format
            lines.append(f"<pubDate>{item.get('pubDate', '')}</pubDate>")
            desc = item.get('description', '') or item.get('content', '')
            lines.append(f"<description><![CDATA[{desc}]]></description>")
            thumbnail = item.get('thumbnail', '')
            if not thumbnail:
                enc = item.get('enclosure') or {}
                thumbnail = enc.get('link', '')
            if thumbnail:
                lines.append(f'<media:content url="{_html.escape(thumbnail)}" medium="image"/>')
            lines.append('</item>')
        lines.append('</channel></rss>')
        return '\n'.join(lines)
    
    async def fetch_multiple_rss(self, urls: list[str]) -> dict[str, str]:
        """
        Fetch multiple RSS feeds efficiently
        
        Args:
            urls: List of RSS feed URLs
            
        Returns:
            Dictionary mapping URL to content
        """
        results = {}
        
        # Helper function for concurrent execution
        async def fetch_single(url):
            content = await self.fetch_rss(url)
            return url, content
            
        # Create tasks
        tasks = [fetch_single(url) for url in urls]
        
        # Run concurrently
        fetched_results = await asyncio.gather(*tasks)
        
        # Collect results
        for url, content in fetched_results:
            results[url] = content
            
        return results

# Singleton instance
secure_fetcher = SecureRSSFetcher()
