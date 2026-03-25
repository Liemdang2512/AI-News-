import asyncio
import json
import re
from typing import List, Optional, Callable, Awaitable, AsyncGenerator, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
try:
    import trafilatura as _trafilatura
    _TRAFILATURA_AVAILABLE = True
except ImportError:
    _TRAFILATURA_AVAILABLE = False
import httpx
from config import settings
from services.secure_fetcher import secure_fetcher
from services.rss_fetcher import rss_fetcher
from services.gemini_client import gemini_client
from services.fast_gemini import fast_gemini
from services.playwright_fetcher import playwright_fetcher
from prompts import SINGLE_ARTICLE_SUMMARIZE_PROMPT, SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT

class Summarizer:
    """
    Fetches article content and generates AI summaries
    Refactored to process articles in parallel for better performance and reliability.
    """
    
    def __init__(self):
        # Semaphore to limit concurrent tasks (avoid rate limits)
        self.semaphore = asyncio.Semaphore(10) # Process 10 articles at a time

    _MIN_CHARS_TO_SUMMARIZE = 80
    _HTTP_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

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
        for prop in ("og:description", "twitter:description", "article:description"):
            m = soup.find("meta", attrs={"property": prop})
            if m and m.get("content"):
                c = m["content"].strip()
                if len(c) > 20 and c not in parts:
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

    @staticmethod
    def _looks_like_block_page(html: str) -> bool:
        if not html:
            return True
        low = html.lower()
        block_signals = (
            "document.cookie",
            "window.location.reload",
            "checking your browser",
            "cf-browser-verification",
            "access denied",
            "captcha",
            "enable javascript and cookies to continue",
        )
        return any(sig in low for sig in block_signals)

    # Các domain dùng JS nặng — dùng Playwright trước để đọc được nội dung
    _JS_HEAVY_DOMAINS = (
        "laodong.vn", "dantri.com.vn", "vtv.vn", "tuoitre.vn",
        "vnexpress.net", "thanhnien.vn", "tienphong.vn", "vietnamplus.vn",
        "sggp.org.vn", "hanoimoi.vn", "nhandan.vn", "baotintuc.vn", "vov.vn",
    )

    def _is_js_heavy(self, url: str) -> bool:
        return any(d in url for d in self._JS_HEAVY_DOMAINS)

    async def _fetch_article_html(self, url: str, timeout: int = 25) -> str:
        """
        Fetch nội dung HTML bài báo bằng nhiều cơ chế.
        Site JS-heavy: Playwright trước. Site khác: curl_cffi → httpx → Playwright.
        """
        # Site dùng JS nặng: thử Playwright trước để đọc đúng nội dung
        if self._is_js_heavy(url):
            try:
                html = await playwright_fetcher.fetch(url, timeout=timeout)
                if html and len(html.strip()) > 500 and not self._looks_like_block_page(html):
                    print(f"   🎭 Playwright (JS-heavy) thành công: {url[:60]}")
                    return html
            except Exception:
                pass

        # 1) Secure fetcher / curl_cffi (tốt cho site anti-bot)
        try:
            html = await secure_fetcher.fetch_rss(url, timeout=timeout)
            if html and len(html.strip()) > 200 and not self._looks_like_block_page(html):
                return html
        except Exception:
            pass

        # 2) Fallback httpx
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                headers=self._HTTP_HEADERS,
            ) as client:
                resp = await client.get(url)
                html = resp.text or ""
                if html and len(html.strip()) > 200 and not self._looks_like_block_page(html):
                    return html
        except Exception:
            pass

        # 3) Playwright (site không phải JS-heavy, thử lần cuối)
        if not self._is_js_heavy(url):
            try:
                html = await playwright_fetcher.fetch(url, timeout=timeout)
                if html and len(html.strip()) > 200 and not self._looks_like_block_page(html):
                    print(f"   🎭 Playwright thành công: {url[:60]}")
                    return html
            except Exception:
                pass

        return ""

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
                    # Always include a "- " bullet so output is consistent with AI summaries.
                    # Use RSS description excerpt if available, otherwise a short note.
                    excerpt = " ".join((rss_plain or "").split())
                    if len(excerpt) > 400:
                        cut = excerpt[:401]
                        excerpt = cut.rsplit(" ", 1)[0] + "…"
                    if excerpt:
                        bullet = f"- {excerpt}"
                    else:
                        extra = note or "Không tải được nội dung đầy đủ. Mở liên kết để đọc toàn bài."
                        bullet = f"- {extra}"
                    return (
                        f"### [{title}]({url})\n"
                        f"**Nguồn:** {source}\n\n"
                        f"{bullet}"
                    )

                await asyncio.sleep(0.5)
                last_ai_error: Optional[str] = None

                # Bước 1: Thử cho Gemini tự đọc URL qua url_context tool (v1beta)
                url_prompt = SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT.format(
                    url=url, title=title, source=source,
                )
                url_models = [settings.GEMINI_MODEL]
                url_context_ok = False

                for model_attempt, model in enumerate(url_models):
                    try:
                        print(f"   🔗 Thử URL context ({model}): {url[:60]}")
                        summary = await fast_gemini.generate_content_with_url(
                            article_url=url,
                            prompt=url_prompt,
                            model_name=model,
                            temperature=0.2,
                            max_tokens=2048,
                            api_key=api_key,
                        )
                        if summary and len(summary.strip()) > 150 and "- " in summary:
                            print(f"   ✅ Summarized via URL context ({model})")
                            return {"category": category.upper(), "text": summary.strip()}
                        print(f"   ⚠️ URL context thiếu nội dung tóm tắt ({len(summary.strip()) if summary else 0} ký tự), fallback fetch: {url[:60]}")
                        last_ai_error = "Phản hồi thiếu bullet tóm tắt"
                    except Exception as e:
                        last_ai_error = str(e)
                        el = last_ai_error.lower()
                        if "429" in last_ai_error or "resource exhausted" in el:
                            await asyncio.sleep(min(32, (model_attempt + 1) * 5))
                        print(f"   ⚠️ URL context lỗi ({model}): {last_ai_error[:200]}")

                # Bước 2: Fallback — tự fetch trang + gửi nội dung cho Gemini
                print(f"   🔄 URL context thất bại, fallback sang fetch thủ công: {url[:50]}")
                content: Optional[str] = None
                best_merged = ""

                for attempt in range(3):
                    try:
                        raw_html = await self._fetch_article_html(url)
                        if not raw_html or len(raw_html.strip()) < 80:
                            if attempt < 2:
                                await asyncio.sleep(2 * (attempt + 1))
                            continue
                        page_extracted = self._extract_content(raw_html, limit=15000)
                        merged = self._merge_page_and_feed(page_extracted, rss_plain, event_plain)
                        if len(merged) > len(best_merged):
                            best_merged = merged
                        if len(merged.strip()) >= self._MIN_CHARS_TO_SUMMARIZE:
                            content = merged
                            break
                        if attempt < 2:
                            await asyncio.sleep(2 * (attempt + 1))
                    except Exception as e:
                        print(f"   ❌ Fetch error attempt {attempt+1}: {e}")
                        await asyncio.sleep(2 * (attempt + 1))

                if not content and best_merged:
                    content = best_merged

                # Nếu fetch thất bại, dùng title + RSS description làm content
                if not content or len(content.strip()) < self._MIN_CHARS_TO_SUMMARIZE:
                    fallback_content = f"{title}\n\n{rss_plain}".strip()
                    if len(fallback_content) >= 60:
                        content = fallback_content
                        print(f"   ℹ️ Dùng title+RSS làm content ({len(content)} ký tự): {url[:50]}")
                    else:
                        return {"category": category.upper(), "text": get_fallback_summary()}

                # Gọi Gemini với nội dung đã fetch
                body_limits = (28000, 16000, 9000, 4500, 2000)
                for ai_attempt, max_body in enumerate(body_limits):
                    try:
                        prompt = self._build_summarize_prompt(title, content, source, category, url, max_body)
                        summary = await gemini_client.async_generate_content(
                            prompt=prompt,
                            model_name=settings.GEMINI_MODEL,
                            temperature=0.2,
                            max_tokens=2048,
                            api_key=api_key,
                        )
                        if summary and len(summary.strip()) > 150 and "- " in summary:
                            print(f"   ✅ Summarized via fetch fallback: {url[:50]}")
                            return {"category": category.upper(), "text": summary.strip()}
                        last_ai_error = "Phản hồi thiếu bullet tóm tắt"
                    except Exception as e:
                        last_ai_error = str(e)
                        el = last_ai_error.lower()
                        if "429" in last_ai_error or "resource exhausted" in el:
                            await asyncio.sleep(min(32, (ai_attempt + 1) * 3))
                            continue
                        if any(x in last_ai_error for x in ("503", "502", "500", "504")) or "timeout" in el:
                            await asyncio.sleep(2 + ai_attempt)
                            continue
                        if ai_attempt < len(body_limits) - 1:
                            await asyncio.sleep(1)
                            continue

                # Thử 1 lần cuối với RSS description ngắn — luôn yêu cầu AI tóm tắt, không hiện excerpt thô
                short_content = f"{title}\n\n{rss_plain}".strip() if rss_plain else title
                if short_content:
                    try:
                        prompt = self._build_summarize_prompt(title, short_content, source, category, url, 4000)
                        summary = await gemini_client.async_generate_content(
                            prompt=prompt,
                            model_name=settings.GEMINI_MODEL,
                            temperature=0.3,
                            max_tokens=1024,
                            api_key=api_key,
                        )
                        if summary and len(summary.strip()) > 100 and "- " in summary:
                            print(f"   ✅ Summarized via RSS fallback: {url[:50]}")
                            return {"category": category.upper(), "text": summary.strip()}
                    except Exception:
                        pass
                return {"category": category.upper(), "text": get_fallback_summary("API tóm tắt AI không phản hồi hoặc bị chặn.")}

            except Exception as e:
                print(f"❌ Error processing {url}: {str(e)}")
                return {"error": f"Lỗi xử lý: {str(e)}"}

    def _extract_content(self, html: str, limit: int = 8000) -> str:
        """
        Trích nội dung chính từ HTML.
        Layer 0: trafilatura (F1: 0.945) — nếu >= 200 chars, dùng ngay.
        Layer 1: JSON-LD articleBody.
        Layer 2: BS4 CSS selectors (20 selectors).
        Layer 3: Meta tags.
        """
        try:
            # Layer 0: trafilatura — highest precision content extraction
            if _TRAFILATURA_AVAILABLE and html:
                try:
                    traf_text = _trafilatura.extract(
                        html,
                        include_comments=False,
                        include_tables=False,
                        output_format="txt",
                        no_fallback=False,
                    )
                    if traf_text and len(traf_text.strip()) > 200:
                        return traf_text.strip()[:limit]
                except Exception:
                    pass  # trafilatura failed, fall through to BS4

            # Layer 1: JSON-LD (existing logic — unchanged)
            soup = BeautifulSoup(html, "html.parser")
            ld_text = self._extract_json_ld_text(soup)

            for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
                tag.decompose()

            # Layer 2: CSS selectors (existing logic — unchanged)
            meta_text = self._extract_meta_text(soup)

            main_content = None
            selectors = [
                ".entry", ".b-maincontent", ".details__content", ".cms-body",
                "#article-body", ".article-body", ".fck_detail", ".detail__content",
                ".sapo", ".post-content", '[role="main"]', "article",
                ".article-content", ".content-detail", ".detail-content",
                ".post_content", ".body-content", "#content", ".content",
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

            # Layer 3: combine and return best
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
