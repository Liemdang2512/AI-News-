"""
Playwright-based RSS fetcher for websites with anti-bot protection
Used specifically for Lao Dong and other sites that block simple HTTP requests
"""

from playwright.async_api import async_playwright, Browser, BrowserContext
from typing import Optional
import asyncio

class PlaywrightRSSFetcher:
    """
    Fetches RSS feeds using a real browser (Playwright) to bypass anti-bot protection
    """
    
    def __init__(self):
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None
        
    async def start(self):
        """Initialize browser"""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
            self._context = await self._browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='vi-VN',
            )
    
    async def close(self):
        """Close browser"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._context = None
        self._playwright = None
    
    async def fetch_rss(self, url: str, timeout: int = 30000) -> str:
        """
        Fetch RSS feed content using Playwright
        
        Args:
            url: RSS feed URL
            timeout: Timeout in milliseconds (default 30s)
            
        Returns:
            RSS feed content as string
        """
        await self.start()
        
        page = await self._context.new_page()
        
        try:
            # Navigate to RSS URL
            await page.goto(url, wait_until='networkidle', timeout=timeout)
            
            # Wait a bit for any JavaScript to execute
            await page.wait_for_timeout(1000)
            
            # Get page content
            content = await page.content()
            
            return content
            
        finally:
            await page.close()
    
    async def fetch_multiple_rss(self, urls: list[str]) -> dict[str, str]:
        """
        Fetch multiple RSS feeds efficiently
        
        Args:
            urls: List of RSS feed URLs
            
        Returns:
            Dictionary mapping URL to content
        """
        await self.start()
        
        results = {}
        
        try:
            # Fetch all URLs concurrently (but limit to 3 at a time to avoid overwhelming)
            for i in range(0, len(urls), 3):
                batch = urls[i:i+3]
                tasks = [self.fetch_rss(url) for url in batch]
                contents = await asyncio.gather(*tasks, return_exceptions=True)
                
                for url, content in zip(batch, contents):
                    if isinstance(content, Exception):
                        print(f"❌ Error fetching {url}: {content}")
                        results[url] = ""
                    else:
                        results[url] = content
        
        finally:
            await self.close()
        
        return results


# Singleton instance
playwright_fetcher = PlaywrightRSSFetcher()
