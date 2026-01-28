import asyncio
from typing import List, Optional, Callable, Awaitable
from bs4 import BeautifulSoup
from services.secure_fetcher import secure_fetcher
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
        
    async def summarize_articles(
        self, 
        urls: List[str], 
        api_key: str = None, 
        articles_metadata: dict = None,
        progress_callback: Optional[Callable[[int, int, str, str], Awaitable[None]]] = None
    ) -> str:
        """
        Fetch and summarize articles in parallel, then group by category.
        """
        if articles_metadata is None:
            articles_metadata = {}
            
        print(f"🚀 Starting parallel summarization for {len(urls)} articles...")
        
        # Create tasks for each URL
        tasks = []
        total = len(urls)
        completed_count = 0
        
        async def track_progress(url, metadata, api_key):
            nonlocal completed_count
            # Notify start
            if progress_callback:
                try:
                    await progress_callback(completed_count, total, url, "processing")
                except Exception as e:
                    print(f"Error in progress callback: {e}")
                
            result = await self._process_single_article(url, metadata, api_key)
            
            completed_count += 1
            # Notify completion (success or fail)
            if progress_callback:
                try:
                    await progress_callback(completed_count, total, url, "completed")
                except Exception as e:
                    print(f"Error in progress callback: {e}")
                
            return result

        for url in urls:
            clean_url = url.strip().rstrip('/')
            metadata = articles_metadata.get(clean_url, {})
            # If not found, try original just in case
            if not metadata:
                metadata = articles_metadata.get(url, {})
            
            # Fallback: Infer category if missing
            if not metadata or not metadata.get('category'):
                inferred_category = rss_fetcher._extract_category_from_url(url)
                if not metadata:
                    metadata = {'source': None, 'title': None}
                metadata['category'] = inferred_category
                
            task = track_progress(url, metadata, api_key)
            tasks.append(task)
        
        # Process in chunks to prevent overload (BATCH_SIZE = 5)
        BATCH_SIZE = 5
        all_results = []
        
        for i in range(0, len(tasks), BATCH_SIZE):
            batch_tasks = tasks[i:i + BATCH_SIZE]
            print(f"🔄 Processing batch {i//BATCH_SIZE + 1}/{(len(tasks) + BATCH_SIZE - 1)//BATCH_SIZE}...")
            
            # Run batch concurrently
            batch_results = await asyncio.gather(*batch_tasks)
            all_results.extend(batch_results)
            
            # Optional: Add delay between batches if needed to cool down rate limits
            if i + BATCH_SIZE < len(tasks):
                await asyncio.sleep(2) 
        
        results = all_results
            
        # Collect results
        category_groups = {}
        failed_articles = []
        
        valid_count = 0
        for i, res in enumerate(results):
            if res and "text" in res:
                # Success case
                cat = res.get("category", "KHÁC")
                if cat not in category_groups:
                    category_groups[cat] = []
                category_groups[cat].append(res["text"])
                valid_count += 1
            elif res and "error" in res:
                # Error case
                url = urls[i] if i < len(urls) else "Unknown URL"
                failed_articles.append(f"- [{url}]({url}): {res['error']}")
            else:
                # None or unknown
                pass
        
        print(f"✅ Completed. Valid: {valid_count}/{len(urls)}, Failed: {len(failed_articles)}")
        
        # Build final Markdown
        final_markdown_parts = []
        
        # 1. Success Groups
        sorted_categories = sorted(category_groups.keys())
        for i, cat in enumerate(sorted_categories, 1):
            articles = category_groups[cat]
            final_markdown_parts.append(f"## {i}. Chuyên mục {cat} ({len(articles)} bài)")
            final_markdown_parts.extend(articles)
            final_markdown_parts.append("") 
            
        # 2. Failed List (if any)
        if failed_articles:
            final_markdown_parts.append("---")
            final_markdown_parts.append(f"### ⚠️ Không thể tóm tắt ({len(failed_articles)} bài)")
            final_markdown_parts.append("\n".join(failed_articles))
        
        return "\n\n".join(final_markdown_parts)

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
