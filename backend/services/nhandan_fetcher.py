"""
Nhan Dan Fetcher Service
Lấy RSS từ Báo Nhân Dân và đối chiếu nội dung
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config import settings
from services.secure_fetcher import secure_fetcher
import feedparser
import json
from services.fast_gemini import fast_gemini


class NhanDanFetcher:
    def __init__(self):
        # RSS URLs cho các chuyên mục chính
        self.rss_urls = {
            "KINH TẾ": "https://nhandan.vn/rss/kinhte-1185.rss",
            "PHÁP LUẬT": "https://nhandan.vn/rss/phapluat-1287.rss",
            "XÃ HỘI": "https://nhandan.vn/rss/xahoi-1211.rss",
            "THẾ GIỚI": "https://nhandan.vn/rss/thegioi-1231.rss",
        }
        
        # Cache headlines (in-memory)
        self.cached_headlines: List[Dict] = []
        self.last_fetch_time: Optional[datetime] = None
        self.cache_duration = timedelta(hours=1)  # Refresh mỗi 1 giờ
        
    async def setup_background_fetch(self):
        """
        Fetch RSS feeds từ Báo Nhân Dân và cache
        """
        print("🔄 Fetching Báo Nhân Dân RSS...")
        all_articles = []
        
        for category, rss_url in self.rss_urls.items():
            try:
                # Sử dụng SecureRSSFetcher cho các trang có chống bot
                rss_content = await secure_fetcher.fetch_rss(rss_url)
                feed = feedparser.parse(rss_content)
                
                for entry in feed.entries[:20]:  # Lấy 20 bài mới nhất mỗi chuyên mục
                    all_articles.append({
                        "title": entry.get('title', ''),
                        "link": entry.get('link', ''),
                        "category": category,
                        "published": entry.get('published', '')
                    })
            except Exception as e:
                print(f"⚠️ Error fetching Nhan Dan RSS for {category}: {e}")
        
        self.cached_headlines = all_articles
        self.last_fetch_time = datetime.now()
        print(f"✅ Cached {len(all_articles)} articles from Báo Nhân Dân")
        
        return all_articles
    
    async def ensure_cache_fresh(self):
        """Đảm bảo cache còn mới (tự động refresh nếu cần)"""
        if not self.cached_headlines or not self.last_fetch_time:
            await self.setup_background_fetch()
        elif datetime.now() - self.last_fetch_time > self.cache_duration:
            await self.setup_background_fetch()
    
    async def check_official_coverage(
        self, 
        articles: List[Dict],
        api_key: str
    ) -> List[Dict]:
        """
        Kiểm tra xem các bài viết có được Báo Nhân Dân đăng không
        Sử dụng batch processing theo category để tối ưu tốc độ
        
        Args:
            articles: Danh sách bài viết cần kiểm tra
            api_key: Gemini API key
            
        Returns:
            Danh sách bài viết đã được gắn thêm field 'official_source_link'
        """
        # Skip if no API key (avoid slow processing)
        if not api_key:
            print("⚠️ No API key - skipping Nhan Dan verification")
            for article in articles:
                article['official_source_link'] = None
            return articles
        
        await self.ensure_cache_fresh()
        
        if not self.cached_headlines:
            print("⚠️ No Nhan Dan cache available")
            for article in articles:
                article['official_source_link'] = None
            return articles
        
        # Group articles by category
        MAX_ARTICLES_PER_CATEGORY = 70  # Limit to prevent timeout
        articles_by_category = {}
        for article in articles:
            category = article.get('category', 'KHÁC')
            if category not in articles_by_category:
                articles_by_category[category] = []
            articles_by_category[category].append(article)
        
        print(f"🔍 Checking Nhan Dan coverage for {len(articles)} articles across {len(articles_by_category)} categories")
        
        # Process each category in parallel (with limit)
        tasks = []
        for category, category_articles in articles_by_category.items():
            if category in self.rss_urls:
                # Limit articles per category
                if len(category_articles) > MAX_ARTICLES_PER_CATEGORY:
                    print(f"⚠️ Category {category} has {len(category_articles)} articles, limiting to {MAX_ARTICLES_PER_CATEGORY} for Nhan Dan check")
                    category_articles = category_articles[:MAX_ARTICLES_PER_CATEGORY]
                
                task = self._check_category_batch(category, category_articles, api_key)
                tasks.append(task)
            else:
                # Mark as not applicable
                for article in category_articles:
                    article['official_source_link'] = None
        
        # Run all category checks in parallel
        if tasks:
            await asyncio.gather(*tasks)
        
        return articles
    
    async def _check_category_batch(
        self,
        category: str,
        articles: List[Dict],
        api_key: str
    ):
        """
        Check một batch articles cùng category với Nhan Dan headlines
        """
        # Get Nhan Dan headlines for this category
        category_headlines = [
            h for h in self.cached_headlines 
            if h['category'] == category
        ]
        
        if not category_headlines:
            for article in articles:
                article['official_source_link'] = None
            return
        
        # Batch check: Send all articles at once to Gemini
        await self._batch_semantic_match(articles, category_headlines, api_key)
    
    async def _batch_semantic_match(
        self,
        articles: List[Dict],
        nhan_dan_headlines: List[Dict],
        api_key: str
    ):
        """
        Batch semantic matching: Check nhiều bài cùng lúc
        """
        # Prepare batch data
        # Prepare batch data with XML tags
        articles_formatted = "\n".join([
            f"{i}. {a['title']}"
            for i, a in enumerate(articles)
        ])
        
        headlines_formatted = "\n".join([
            f"- {h['title']} | URL: {h['link']}"
            for h in nhan_dan_headlines[:20]  # Increased limit slightly
        ])
        
        prompt = f"""# Role
Bạn là một AI News Aggregator Engineer chuyên nghiệp. Nhiệm vụ của bạn là đối chiếu danh sách các "Tin tức mới" (Input) với "Cơ sở dữ liệu báo chí" (Reference) để tìm ra các bài viết trùng lặp về mặt sự kiện.

# Input Data
Tôi sẽ cung cấp cho bạn 2 danh sách được bao bọc bởi thẻ XML:
1. <input_articles>: Danh sách các tiêu đề cần kiểm tra (đã được đánh ID).
2. <reference_database>: Danh sách các bài báo gốc (gồm Tiêu đề và URL).

# Instruction (Hướng dẫn xử lý)
Hãy thực hiện từng bước suy luận sau:

Bước 1: Trích xuất thực thể (Entity Extraction)
Với mỗi bài trong <input_articles>, hãy xác định: Ai (Who), Cái gì (What), Ở đâu (Where), Con số thương vong/thiệt hại (Numbers).

Bước 2: So khớp (Matching Logic)
So sánh các thực thể trên với <reference_database>.
- Quy tắc khớp: Hai bài viết chỉ được coi là MATCH khi chúng nói về CÙNG MỘT SỰ KIỆN CỤ THỂ (Same specific event).
- Quy tắc loại trừ: 
  + Cùng chủ đề nhưng khác góc độ -> KHÔNG KHỚP (Ví dụ: "Nga tái thiết Syria" khác với "Họp LHQ về hòa bình Syria").
  + Cùng địa điểm nhưng khác sự kiện -> KHÔNG KHỚP.
  + Nếu nghi ngờ hoặc thông tin quá chung chung -> Trả về null.

Bước 3: Output JSON
Trả về kết quả dưới dạng JSON Array, không kèm lời giải thích nào khác ngoài JSON.

# Output Format
[
  {{
    "article_index": 0, 
    "matched_link": "URL_từ_reference_list" (hoặc null nếu không tìm thấy)
  }},
  ...
]

# Data
<input_articles>
{articles_formatted}
</input_articles>

<reference_database>
{headlines_formatted}
</reference_database>
"""

        try:
            response = await fast_gemini.generate_content(
                prompt=prompt,
                model_name=settings.GEMINI_MODEL,
                temperature=0.2,
                max_tokens=1024,
                api_key=api_key
            )
            
            # Parse response
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            results = json.loads(response_text)
            
            # Apply results to articles
            for result in results:
                idx = result.get('article_index')
                if 0 <= idx < len(articles):
                    articles[idx]['official_source_link'] = result.get('matched_link')
            
        except Exception as e:
            print(f"⚠️ Batch semantic match error: {e}")
            # Fallback: mark all as not matched
            for article in articles:
                if 'official_source_link' not in article:
                    article['official_source_link'] = None
    
    async def _semantic_match(
        self, 
        article: Dict, 
        nhan_dan_headlines: List[Dict],
        api_key: str
    ) -> Optional[str]:
        """
        Sử dụng Gemini để kiểm tra xem bài viết có khớp với bài nào của Nhân Dân không
        """
        # Prepare data
        headlines_text = "\n".join([
            f"{i+1}. {h['title']} ({h['link']})"
            for i, h in enumerate(nhan_dan_headlines[:10])  # Limit to 10 for token efficiency
        ])
        
        prompt = f"""Bạn là chuyên gia phân tích tin tức. Hãy kiểm tra xem bài viết dưới đây có cùng nội dung với bài nào trong danh sách Báo Nhân Dân không.

Bài viết cần kiểm tra:
Tiêu đề: {article['title']}

Danh sách Báo Nhân Dân:
{headlines_text}

Trả về JSON:
{{
  "is_match": true/false,
  "matched_link": "url nếu khớp, null nếu không"
}}

Lưu ý: Chỉ trả về true nếu chắc chắn 2 bài viết về cùng sự kiện.
"""

        try:
            response = await fast_gemini.generate_content(
                prompt=prompt,
                model_name=settings.GEMINI_MODEL,
                temperature=0.2,
                max_tokens=256,
                api_key=api_key
            )
            
            # Parse response
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            if result.get('is_match'):
                return result.get('matched_link')
            
        except Exception as e:
            print(f"⚠️ Semantic match error: {e}")
        
        return None


# Singleton
nhandan_fetcher = NhanDanFetcher()
