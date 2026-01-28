"""
Secure RSS fetcher using curl_cffi to bypass anti-bot protection (Lao Dong, etc.)
Replaces the heavy Playwright implementation.
Falls back to httpx if curl_cffi is not available (Render/Vercel compatibility).
"""

from typing import Dict, List, Optional
import asyncio

# Try to import curl_cffi, fallback to httpx if not available
try:
    from curl_cffi.requests import AsyncSession
    CURL_CFFI_AVAILABLE = True
except ImportError:
    print("⚠️ curl_cffi not available, falling back to httpx")
    import httpx
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
                                
                    return response.text
            except Exception as e:
                print(f"❌ curl_cffi error for {url}: {str(e)}")
                return ""
        else:
            # Fallback to httpx (for Vercel/serverless environments)
            try:
                async with httpx.AsyncClient(
                    timeout=timeout,
                    follow_redirects=True,
                    headers=self.headers
                ) as client:
                    response = await client.get(url)
                    return response.text
            except Exception as e:
                print(f"❌ httpx error for {url}: {str(e)}")
                return ""
    
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
