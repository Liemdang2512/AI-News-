import asyncio
from typing import List, Optional, Callable, Awaitable, AsyncGenerator, Dict
from datetime import datetime
from bs4 import BeautifulSoup
from services.secure_fetcher import secure_fetcher
from services.rss_fetcher import rss_fetcher
from services.gemini_client import gemini_client
from prompts import SINGLE_ARTICLE_SUMMARIZE_PROMPT

class Summarizer:
    """
    Fetches article content and generates AI summaries
    Refactored to process articles in parallel for better performance and reliability.
    """
    
    def __init__(self):
        # Semaphore to limit concurrent tasks (avoid rate limits)
        self.semaphore = asyncio.Semaphore(10) # Process 10 articles at a time
        
    async def summarize_articles_generator(
        self, 
        urls: List[str], 
        api_key: str = None, 
        articles_metadata: dict = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Summarize articles and yield progress updates (for StreamingResponse)
        Yields dicts: {'type': 'progress', ...} or {'type': 'complete', 'summary': ...}
        """
        if not urls:
            yield {"type": "error", "message": "No articles selected"}
            return

        if not articles_metadata:
            articles_metadata = {}

        tasks = []
        total = len(urls)
        completed = 0
        
        # We need to process tasks and yield as they complete
        # Create a list of coroutines
        for url in urls:
            clean_url = url.strip().rstrip('/')
            metadata = articles_metadata.get(clean_url, {})
            if not metadata:
                metadata = articles_metadata.get(url, {})
            
            # Fallback logic
            if not metadata or not metadata.get('category'):
                inferred_category = rss_fetcher._extract_category_from_url(url)
                if not metadata: metadata = {'source': None, 'title': None}
                metadata['category'] = inferred_category

            tasks.append(self._process_single_article(url, metadata, api_key))
            
        # Process in batches (BATCH_SIZE = 5) and yield progress
        BATCH_SIZE = 5
        all_results = []
        
        for i in range(0, len(tasks), BATCH_SIZE):
            batch_tasks = tasks[i:i + BATCH_SIZE]
            batch_urls = urls[i:i + BATCH_SIZE]
            
            # Current batch progress update
            for url in batch_urls:
                 # Try to get title for better UI
                 meta = articles_metadata.get(url.strip().rstrip('/')) or articles_metadata.get(url) or {}
                 title = meta.get('title', url)
                 yield {
                     "type": "progress",
                     "completed": completed,
                     "total": total,
                     "current_article": f"Đang xử lý: {title}...",
                     "status": "processing"
                 }
            
            batch_results = await asyncio.gather(*batch_tasks)
            all_results.extend(batch_results)
            completed += len(batch_results)
            
            # Update progress after batch
            yield {
                "type": "progress",
                "completed": completed,
                "total": total,
                "current_article": "Đang chuyển sang lô tiếp theo...",
                "status": "processing"
            }
            
            if i + BATCH_SIZE < len(tasks):
                await asyncio.sleep(2) 
                
        # ... (rest of processing logic identical to summarize_articles) ...
        # Copied logic for combining results
        
        results = all_results
        
        # Sort results by category
        # ... (reuse logic) ...
        # For brevity, calling internal helper or duplicating logic? 
        # Duplicating logic is safer to avoid breaking existing method
        
        categorized_results = {
            "KINH TẾ": [],
            "TÀI CHÍNH": [],
            "XÃ HỘI": [],
            "PHÁP LUẬT": [],
            "THẾ GIỚI": [],
            "KHÁC": []
        }
        
        failed_articles = []
        
        for res in results:
            if "error" in res or "text" not in res:
                 # Check if it was a fallback text result (which is a dict with category/text)
                 if isinstance(res, dict) and "text" in res and "category" in res:
                     # It's a valid result (fallback or normal)
                     cat = res.get("category", "KHÁC").upper()
                     if cat not in categorized_results: cat = "KHÁC"
                     categorized_results[cat].append(res["text"])
                 else:
                     # It is a failure
                     failed_articles.append(res)
            else:
                 cat = res.get("category", "KHÁC").upper()
                 if cat not in categorized_results: cat = "KHÁC"
                 categorized_results[cat].append(res["text"])

        # Format Markdown
        final_summary = f"# TIN TỨC TỔNG HỢP ({datetime.now().strftime('%d/%m/%Y')})\n\n"
        
        priority_order = ["KINH TẾ", "TÀI CHÍNH", "XÃ HỘI", "PHÁP LUẬT", "THẾ GIỚI", "KHÁC"]
        
        for cat in priority_order:
            articles_list = categorized_results.get(cat, [])
            if articles_list:
                final_summary += f"## {cat}\n\n"
                for idx, article_text in enumerate(articles_list, 1):
                    final_summary += f"{article_text}\n\n"
                final_summary += "---\n\n"
        
        if failed_articles:
             final_summary += f"### ⚠️ Không thể tóm tắt ({len(failed_articles)} bài)\n"
             # ... error details ...
        
        yield {
            "type": "complete", 
            "summary": final_summary
        }

    async def _process_single_article(self, url: str, metadata: dict, api_key: str) -> dict:
        """
        Fetch and summarize a single article with concurrency control.
        Returns dict: {"category": str, "text": str} or None
        """
        async with self.semaphore:


            try:
                # Prepare metadata first for fallback
                source = metadata.get('source', 'Nguồn Khác')
                category = metadata.get('category', 'TIN TỨC') 
                title = metadata.get('title', 'Tiêu đề bài viết')
                
                # Fallback text generator
                def get_fallback_summary(reason=""):
                    return (
                        f"### [{title}]({url})\n"
                        f"**Nguồn:** {source}\n\n"
                        f"*(Bài viết có nội dung ngắn hoặc hình ảnh, vui lòng xem chi tiết tại đường dẫn)*"
                    )

                # 1. Fetch Content
                await asyncio.sleep(0.5) 
                
                content = None
                fetch_retries = 3
                for attempt in range(fetch_retries):
                    try:
                        raw_html = await secure_fetcher.fetch_rss(url)
                        # Try to extract
                        soup = BeautifulSoup(raw_html, 'html.parser')
                        # Remove script/style
                        for script in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
                            script.decompose()
                            
                        # Selectors logic (inlined or called)
                        # We call the helper
                        extracted = self._extract_content(raw_html, limit=15000)
                        
                        if extracted and len(extracted) >= 200:
                            content = extracted
                            break
                        else:
                            # If extraction failed/short, wait and retry? 
                            # Actually if content is short, retrying might not help if it's the article nature.
                            # But we retry for network issues.
                            # For now, let's just wait.
                            if attempt < fetch_retries - 1:
                                await asyncio.sleep(2 * (attempt + 1))
                    except Exception as e:
                        print(f"   ❌ Fetch error attempt {attempt+1} for {url}: {e}")
                        await asyncio.sleep(2 * (attempt + 1))
                
                # If still no content or content too short
                if not content or len(content) < 200:
                    print(f"⚠️ Content short/empty for {url}, returning fallback.")
                    return {
                        "category": category.upper(),
                        "text": get_fallback_summary()
                    }

                # 2. Prepare Prompt
                prompt = SINGLE_ARTICLE_SUMMARIZE_PROMPT.format(
                    title=title,
                    content=content,
                    source=source,
                    category=category,
                    url=url
                )

                # 3. Generate Summary with Gemini (with Retry)
                retries = 3
                for attempt in range(retries):
                    try:
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
                        if "429" in str(e) or "Resource exhausted" in str(e):
                            wait_time = (attempt + 1) * 2
                            print(f"   ⏳ Rate limit Gemini for {url[:20]}... Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        else:
                            print(f"   ❌ Error generating summary for {url}: {str(e)}")
                            break # Don't retry generic errors
                
                return None

            except Exception as e:
                print(f"❌ Error processing {url}: {str(e)}")
                return {"error": f"Lỗi xử lý: {str(e)}"}

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
                # Specific Selectors (High Priority)
                '.entry', # HanoiMoi (Verified)
                '.b-maincontent', # HanoiMoi
                '.details__content', # Lao Dong
                '.cms-body', # VietnamPlus
                '#article-body', # TienPhong, SGGP
                '.article-body', 
                '.fck_detail', # VnExpress/DanTri
                '.post-content', 
                '[role="main"]', 
                'article', 
                
                # Generic Selectors (Low Priority - Use with caution)
                '.article-content', 
                '.content-detail', 
                '.detail-content', 
                '.post_content',
                '.body-content',
                '#content', 
                '.content' 
            ]
            
            for selector in selectors:
                found = soup.select_one(selector)
                if found:
                    temp_text = found.get_text(separator=' ', strip=True)
                    if len(temp_text) > 200:
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
