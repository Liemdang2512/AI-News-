import asyncio
import json
import re
from typing import List, Optional, Callable, Awaitable, AsyncGenerator, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
from config import settings
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

    _MIN_CHARS_TO_SUMMARIZE = 80

    @staticmethod
    def _strip_html(raw: str) -> str:
        if not raw:
            return ""
        t = re.sub(r"<[^>]+>", " ", raw)
        return " ".join(t.split()).strip()

    @staticmethod
    def _walk_ld_article_body(data: Any) -> List[str]:
        out: List[str] = []
        if isinstance(data, dict):
            types = data.get("@type")
            if isinstance(types, list):
                type_names = [str(t) for t in types]
            elif isinstance(types, str):
                type_names = [types]
            else:
                type_names = []
            if any(
                t in ("NewsArticle", "Article", "WebPage", "BlogPosting", "ReportageNewsArticle")
                for t in type_names
            ):
                body = data.get("articleBody") or data.get("description")
                if isinstance(body, str) and len(body.strip()) > 40:
                    out.append(body.strip())
            for v in data.values():
                out.extend(Summarizer._walk_ld_article_body(v))
        elif isinstance(data, list):
            for item in data:
                out.extend(Summarizer._walk_ld_article_body(item))
        return out

    def _extract_json_ld_text(self, soup: BeautifulSoup) -> str:
        chunks: List[str] = []
        for script in soup.find_all("script", type=True):
            st = script.get("type") or ""
            if "ld+json" not in st.lower():
                continue
            raw = (script.string or script.get_text() or "").strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            chunks.extend(self._walk_ld_article_body(data))
        return "\n\n".join(dict.fromkeys(chunks))

    @staticmethod
    def _extract_meta_text(soup: BeautifulSoup) -> str:
        parts: List[str] = []
        for prop in ("og:description",):
            m = soup.find("meta", attrs={"property": prop})
            if m and m.get("content"):
                c = m["content"].strip()
                if len(c) > 20:
                    parts.append(c)
        m2 = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if m2 and m2.get("content"):
            c = m2["content"].strip()
            if len(c) > 20 and c not in parts:
                parts.append(c)
        return "\n\n".join(parts)

    def _merge_page_and_feed(
        self, page_text: str, rss_description: str, event_summary: str
    ) -> str:
        page = (page_text or "").strip()
        rss = (rss_description or "").strip()
        ev = (event_summary or "").strip()
        if len(page) >= 200:
            return page[:20000]
        blocks: List[str] = []
        if page:
            blocks.append(page)
        if rss and rss not in page:
            blocks.append(rss)
        if ev and ev not in page and ev not in rss:
            blocks.append(ev)
        merged = "\n\n".join(blocks)
        if len(merged) < self._MIN_CHARS_TO_SUMMARIZE and rss:
            merged = rss
        if len(merged) < self._MIN_CHARS_TO_SUMMARIZE and page:
            merged = page or merged
        return merged[:20000]

    @staticmethod
    def _escape_braces_for_format(s: str) -> str:
        if not s:
            return ""
        return str(s).replace("{", "{{").replace("}", "}}")

    def _build_summarize_prompt(
        self,
        title: str,
        content_body: str,
        source: str,
        category: str,
        url: str,
        max_content_chars: int,
    ) -> str:
        body = (content_body or "")[:max_content_chars]
        e = self._escape_braces_for_format
        return SINGLE_ARTICLE_SUMMARIZE_PROMPT.format(
            title=e(title),
            content=e(body),
            source=e(source),
            category=e(category),
            url=e(url),
        )

    @staticmethod
    def _excerpt_only_fallback(
        title: str, url: str, source: str, content: str, max_len: int = 520
    ) -> str:
        excerpt = " ".join((content or "").split())
        if len(excerpt) > max_len:
            cut = excerpt[: max_len + 1]
            excerpt = cut.rsplit(" ", 1)[0] + "…"
        return (
            f"### [{title}]({url})\n"
            f"**Nguồn:** {source}\n\n"
            f"- {excerpt}\n"
        )

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
                if not metadata:
                    metadata = {"source": None, "title": None, "description": ""}
                metadata["category"] = inferred_category

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
            if res is None:
                failed_articles.append({"error": "Không nhận được kết quả từ AI"})
                continue
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
                final_summary += f"## {cat} ({len(articles_list)} bài)\n\n"
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
                rss_plain = self._strip_html(metadata.get("description") or "")
                event_plain = (metadata.get("event_summary") or "").strip()

                def get_fallback_summary(note: str = "") -> str:
                    extra = (
                        "Không tải được nội dung đủ dài từ trang bài và không có mô tả RSS đủ để tóm tắt."
                    )
                    if note:
                        extra = note
                    return (
                        f"### [{title}]({url})\n"
                        f"**Nguồn:** {source}\n\n"
                        f"*({extra} Mở liên kết để đọc đầy đủ.)*"
                    )

                # 1. Fetch trang bài + trích nội dung; ghép với mô tả RSS / tóm sự kiện nếu trang khó parse
                await asyncio.sleep(0.5)

                content: Optional[str] = None
                best_merged = ""
                fetch_retries = 3
                for attempt in range(fetch_retries):
                    try:
                        raw_html = await secure_fetcher.fetch_rss(url)
                        if not raw_html or len(raw_html.strip()) < 80:
                            if attempt < fetch_retries - 1:
                                await asyncio.sleep(2 * (attempt + 1))
                            continue

                        page_extracted = self._extract_content(raw_html, limit=15000)
                        merged = self._merge_page_and_feed(
                            page_extracted, rss_plain, event_plain
                        )
                        if len(merged) > len(best_merged):
                            best_merged = merged

                        if len(merged.strip()) >= self._MIN_CHARS_TO_SUMMARIZE:
                            content = merged
                            break

                        if attempt < fetch_retries - 1:
                            await asyncio.sleep(2 * (attempt + 1))
                    except Exception as e:
                        print(f"   ❌ Fetch error attempt {attempt+1} for {url}: {e}")
                        await asyncio.sleep(2 * (attempt + 1))

                if not content and best_merged:
                    content = best_merged

                if not content or len(content.strip()) < self._MIN_CHARS_TO_SUMMARIZE:
                    print(
                        f"⚠️ Nội dung quá ngắn cho {url} "
                        f"(trang ~{len(best_merged)} ký tự sau trích, RSS ~{len(rss_plain)})."
                    )
                    return {
                        "category": category.upper(),
                        "text": get_fallback_summary(),
                    }

                # 2–3. Prompt an toàn (escape { } trong nội dung) + Gemini: retry, rút ngắn nội dung khi lỗi
                last_ai_error: Optional[str] = None
                body_limits = (28000, 16000, 9000, 4500, 2000)

                for ai_attempt, max_body in enumerate(body_limits):
                    try:
                        prompt = self._build_summarize_prompt(
                            title, content, source, category, url, max_body
                        )
                    except (KeyError, ValueError) as fmt_e:
                        print(f"   ❌ Lỗi ghép prompt cho {url}: {fmt_e}")
                        last_ai_error = str(fmt_e)
                        break

                    try:
                        summary = await gemini_client.async_generate_content(
                            prompt=prompt,
                            model_name=settings.GEMINI_MODEL,
                            temperature=0.2,
                            max_tokens=2048,
                            api_key=api_key,
                        )
                        if summary and summary.strip():
                            print(f"   ✅ Summarized: {url[:30]}...")
                            return {
                                "category": category.upper(),
                                "text": summary.strip(),
                            }
                        last_ai_error = "Phản hồi rỗng"
                        print(f"   ⚠️ Gemini rỗng, thử lại (lần {ai_attempt + 1})…")
                    except Exception as e:
                        last_ai_error = str(e)
                        el = last_ai_error.lower()
                        if "429" in last_ai_error or "resource exhausted" in el:
                            wait_time = min(32, (ai_attempt + 1) * 3)
                            print(f"   ⏳ Rate limit Gemini, chờ {wait_time}s…")
                            await asyncio.sleep(wait_time)
                            continue
                        if any(x in last_ai_error for x in ("503", "502", "500", "504")) or "timeout" in el:
                            await asyncio.sleep(2 + ai_attempt)
                            continue
                        if ai_attempt < len(body_limits) - 1:
                            print(
                                f"   ⚠️ Gemini lỗi, thử rút nội dung ({max_body}→{body_limits[ai_attempt + 1]}): "
                                f"{last_ai_error[:180]}"
                            )
                            await asyncio.sleep(1)
                            continue
                        print(f"   ❌ Gemini: {last_ai_error[:400]}")

                print(
                    f"   ⚠️ AI không tóm tắt được {url[:50]}… "
                    f"(log: {last_ai_error[:200] if last_ai_error else 'n/a'})"
                )
                if len(content.strip()) >= 120:
                    return {
                        "category": category.upper(),
                        "text": self._excerpt_only_fallback(title, url, source, content),
                    }
                return {
                    "category": category.upper(),
                    "text": get_fallback_summary("API tóm tắt AI không phản hồi hoặc bị chặn."),
                }

            except Exception as e:
                print(f"❌ Error processing {url}: {str(e)}")
                return {"error": f"Lỗi xử lý: {str(e)}"}

    def _extract_content(self, html: str, limit: int = 8000) -> str:
        """
        Trích nội dung chính từ HTML: JSON-LD (articleBody), thẻ meta, rồi các vùng article phổ biến.
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            ld_text = self._extract_json_ld_text(soup)

            for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
                tag.decompose()

            meta_text = self._extract_meta_text(soup)

            main_content = None
            selectors = [
                ".entry",
                ".b-maincontent",
                ".details__content",
                ".cms-body",
                "#article-body",
                ".article-body",
                ".fck_detail",
                ".detail__content",
                ".sapo",
                ".post-content",
                '[role="main"]',
                "article",
                ".article-content",
                ".content-detail",
                ".detail-content",
                ".post_content",
                ".body-content",
                "#content",
                ".content",
            ]

            for selector in selectors:
                found = soup.select_one(selector)
                if found:
                    temp_text = found.get_text(separator=" ", strip=True)
                    if len(temp_text) > 100:
                        main_content = found
                        break

            target = main_content if main_content else soup
            selector_text = target.get_text(separator=" ", strip=True)
            selector_text = " ".join(selector_text.split())

            candidates = [ld_text, selector_text, meta_text]
            candidates = [c for c in candidates if c and len(c.strip()) > 30]
            if not candidates:
                return ""
            best = max(candidates, key=len)
            if len(best) < 200 and len(candidates) >= 2:
                best = "\n\n".join(dict.fromkeys(candidates))
            return best.strip()[:limit]
        except Exception:
            return ""

summarizer = Summarizer()
