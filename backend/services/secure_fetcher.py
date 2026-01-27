"""
Secure RSS fetcher using curl_cffi to bypass anti-bot protection (Lao Dong, etc.)
Replaces the heavy Playwright implementation.
"""

from curl_cffi.requests import AsyncSession
from typing import Dict, List, Optional
import asyncio

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
        Fetch RSS feed content using curl_cffi
        
        Args:
            url: RSS feed URL
            timeout: Timeout in seconds
            
        Returns:
            RSS feed content as string
        """
        try:
            async with AsyncSession(impersonate=self.impersonate, headers=self.headers) as session:
                response = await session.get(url, timeout=timeout)
                return response.text
        except Exception as e:
            print(f"❌ Error fetching {url}: {str(e)}")
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
