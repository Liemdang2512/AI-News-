import httpx
from bs4 import BeautifulSoup
from typing import List
import asyncio
from services.gemini_client import gemini_client
from prompts import SUMMARIZE_PROMPT, SINGLE_ARTICLE_SUMMARIZE_PROMPT

class Summarizer:
    """
    Fetches article content and generates AI summaries
    Refactored to process articles in parallel for better performance and reliability.
    """
    
    def __init__(self):
        # Semaphore to limit concurrent tasks (avoid rate limits)
        self.semaphore = asyncio.Semaphore(10) # Process 10 articles at a time
        
    async def summarize_articles(self, urls: List[str], api_key: str = None, articles_metadata: dict = None) -> str:
        """
        Fetch and summarize articles in parallel, then group by category.
        """
        if articles_metadata is None:
            articles_metadata = {}
            
        print(f"🚀 Starting parallel summarization for {len(urls)} articles...")
        
        # Create tasks for each URL
        tasks = []
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for url in urls:
                metadata = articles_metadata.get(url, {})
                task = self._process_single_article(client, url, metadata, api_key)
                tasks.append(task)
            
            # Run all tasks concurrently
            results = await asyncio.gather(*tasks)
            
        # Collect valid results
        # results structure: [{"category": "...", "text": "..."}, None, ...]
        category_groups = {}
        
        valid_count = 0
        for res in results:
            if res:
                cat = res.get("category", "KHÁC")
                if cat not in category_groups:
                    category_groups[cat] = []
                category_groups[cat].append(res["text"])
                valid_count += 1
        
        print(f"✅ Completed summarization. Valid: {valid_count}/{len(urls)}")
        
        # Build final Markdown with Group Headers
        final_markdown_parts = []
        
        # Sort categories (optional, but nice)
        sorted_categories = sorted(category_groups.keys())
        
        for i, cat in enumerate(sorted_categories, 1):
            articles = category_groups[cat]
            # Add Group Header
            final_markdown_parts.append(f"## {i}. Chuyên mục {cat} ({len(articles)} bài)")
            # Add summaries
            final_markdown_parts.extend(articles)
            final_markdown_parts.append("") # Spacer
        
        return "\n\n".join(final_markdown_parts)

    async def _process_single_article(self, client: httpx.AsyncClient, url: str, metadata: dict, api_key: str) -> dict:
        """
        Fetch and summarize a single article with concurrency control.
        Returns dict: {"category": str, "text": str} or None
        """
        async with self.semaphore:
            try:
                # 1. Fetch Content
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = await client.get(url, headers=headers)
                
                content = self._extract_content(response.text, limit=15000)
                
                if not content or len(content) < 200:
                    print(f"⚠️ Content too short/empty for {url}")
                    return None

                # 2. Prepare Prompt
                source = metadata.get('source', 'Nguồn Khác')
                category = metadata.get('category', 'TIN TỨC') # Default uppercase better for header
                title = metadata.get('title', 'Tiêu đề bài viết')
                
                prompt = SINGLE_ARTICLE_SUMMARIZE_PROMPT.format(
                    title=title,
                    content=content,
                    source=source,
                    category=category,
                    url=url
                )

                # 3. Generate Summary with Gemini
                summary = await gemini_client.async_generate_content(
                    prompt=prompt,
                    model_name="gemini-2.0-flash",
                    temperature=0.2,
                    max_tokens=1000,
                    api_key=api_key
                )
                
                print(f"   ✅ Summarized: {url[:30]}...")
                
                return {
                    "category": category.upper(), # Normalize category
                    "text": summary
                }

            except Exception as e:
                print(f"❌ Error processing {url}: {str(e)}")
                return None

    def _extract_content(self, html: str, limit: int = 8000) -> str:
        """
        Extract main content from HTML using BeautifulSoup
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
                script.decompose()
            
            # Attempt to find main content areas for cleaner text
            # Common selectors for news sites
            main_content = None
            selectors = [
                'article', 
                '[role="main"]', 
                '.post-content', 
                '.article-content', 
                '#content', 
                '.content',
                '.fck_detail', # VnExpress/DanTri specific often
                '.details__content' # Lao Dong
            ]
            
            for selector in selectors:
                found = soup.select_one(selector)
                if found:
                    main_content = found
                    break
            
            target = main_content if main_content else soup

            # Get text
            text = target.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = ' '.join(text.split())
            
            # Limit content
            return text[:limit]
        except Exception:
            return ""

summarizer = Summarizer()
