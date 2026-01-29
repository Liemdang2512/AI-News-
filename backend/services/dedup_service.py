"""
Semantic Duplicate Detection Service
Sử dụng Gemini 2.0 Flash để phát hiện các bài viết trùng lặp dựa trên ngữ nghĩa
"""

import asyncio
from typing import List, Dict
from services.fast_gemini import fast_gemini
import json


class DedupService:
    def __init__(self):
        self.model_name = "gemini-2.0-flash"
        
    async def cluster_articles_semantically(
        self, 
        articles: List[Dict], 
        api_key: str = None
    ) -> List[Dict]:
        """
        Nhóm các bài viết theo sự kiện sử dụng AI semantic analysis
        
        Args:
            articles: Danh sách bài viết với các field {id, title, description, source, url, category}
            api_key: Gemini API key
            
        Returns:
            Danh sách bài viết đã được gán group_id, is_master, duplicate_count
        """
        if not articles or len(articles) == 0:
            return articles
            
        # Step 1: Pre-filter - exact title matches (fast path)
        articles = self._mark_exact_duplicates(articles)
        
        # Step 2: Group by category and time window for efficiency
        grouped_by_category = {}
        for article in articles:
            category = article.get('category', 'KHÁC')
            if category not in grouped_by_category:
                grouped_by_category[category] = []
            grouped_by_category[category].append(article)
        
        # Step 3: AI Clustering per category (with limit to prevent timeout)
        MAX_ARTICLES_PER_CATEGORY = 70  # Limit to prevent Gemini timeout
        all_processed = []
        for category, category_articles in grouped_by_category.items():
            if len(category_articles) <= 1:
                # Chỉ 1 bài thì không cần kiểm tra
                for article in category_articles:
                    article['group_id'] = article['url']  # Unique group
                    article['is_master'] = True
                    article['duplicate_count'] = 0
                all_processed.extend(category_articles)
            else:
                # Limit articles to prevent timeout
                if len(category_articles) > MAX_ARTICLES_PER_CATEGORY:
                    print(f"⚠️ Category {category} has {len(category_articles)} articles, limiting to {MAX_ARTICLES_PER_CATEGORY}")
                    # Take most recent articles
                    category_articles = category_articles[:MAX_ARTICLES_PER_CATEGORY]
                
                processed = await self._ai_cluster_articles(category_articles, api_key)
                all_processed.extend(processed)
        
        return all_processed
    
    def _mark_exact_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Fast pre-filter: mark exact title matches"""
        title_map = {}
        for article in articles:
            title_normalized = article['title'].strip().lower()
            if title_normalized not in title_map:
                title_map[title_normalized] = []
            title_map[title_normalized].append(article)
        
        # Mark duplicates
        for title, duplicates in title_map.items():
            if len(duplicates) > 1:
                # First one is master
                duplicates[0]['_exact_duplicate_group'] = title
                duplicates[0]['_is_exact_master'] = True
                for dup in duplicates[1:]:
                    dup['_exact_duplicate_group'] = title
                    dup['_is_exact_master'] = False
        
        return articles
    
    async def _ai_cluster_articles(
        self, 
        articles: List[Dict], 
        api_key: str
    ) -> List[Dict]:
        """
        Sử dụng Gemini để nhóm các bài viết theo sự kiện
        Áp dụng Entity Extraction + Reasoning để tăng độ chính xác
        """
        # Skip if no API key
        if not api_key:
            print("⚠️ No API key - skipping deduplication")
            for i, article in enumerate(articles):
                article['group_id'] = f"article_{i}"
                article['is_master'] = True
                article['duplicate_count'] = 0
                article['event_summary'] = article['title']
            return articles
        
        # Prepare data with XML format
        articles_formatted = "\n".join([
            f"{i}. [{a.get('source', 'Unknown')}] {a['title']}"
            for i, a in enumerate(articles)
        ])
        
        prompt = f"""# Role
Bạn là một AI News Aggregator Engineer chuyên nghiệp. Nhiệm vụ của bạn là phân tích danh sách tin tức để tìm ra các bài viết nói về CÙNG MỘT SỰ KIỆN CỤ THỂ, sau đó gom chúng thành nhóm.

# Input Data
<input_articles>
{articles_formatted}
</input_articles>

# Instruction (Hướng dẫn xử lý)
Hãy thực hiện từng bước suy luận sau:

Bước 1: Trích xuất thực thể (Entity Extraction)
Với mỗi bài viết, hãy xác định:
- Ai (Who): Nhân vật chính, tổ chức
- Cái gì (What): Hành động, sự kiện chính
- Ở đâu (Where): Địa điểm cụ thể
- Khi nào (When): Thời gian (nếu có)
- Con số quan trọng (Numbers): Số liệu, thiệt hại, v.v.

Bước 2: Nhóm sự kiện (Event Grouping)
So sánh các thực thể giữa các bài viết:
- **Quy tắc gom nhóm**: Chỉ gom khi 2 bài nói về CÙNG MỘT SỰ KIỆN CỤ THỂ (Same specific event).
  + Ví dụ ĐÚNG: "Giá vàng tăng 420 USD" và "Vàng lên đỉnh lịch sử 420 USD" → Cùng nhóm
  + Ví dụ SAI: "Giá vàng tăng" và "Nga hưởng lợi từ giá vàng" → Khác nhóm (khác góc độ)
  
- **Quy tắc loại trừ**:
  + Cùng chủ đề nhưng khác sự kiện cụ thể → KHÔNG gom
  + Cùng địa điểm nhưng khác thời điểm → KHÔNG gom
  + Khác nguồn báo NHƯNG cùng nội dung → VẪN gom (đây là mục đích chính)

Bước 3: Tạo event_summary
Với mỗi nhóm, tạo 1 câu tóm tắt ngắn gọn (< 15 từ) mô tả sự kiện chính.

Bước 4: Output JSON
Trả về kết quả dưới dạng JSON, không kèm lời giải thích.

# Output Format
{{
  "groups": [
    {{
      "group_id": "event_identifier_slug",
      "article_ids": [0, 3, 5],
      "event_summary": "Mô tả ngắn gọn sự kiện"
    }},
    {{
      "group_id": "another_event",
      "article_ids": [1],
      "event_summary": "Bài viết độc lập"
    }}
  ]
}}

Lưu ý:
- Mỗi bài viết chỉ thuộc 1 nhóm duy nhất
- Nếu bài viết độc lập (không trùng), tạo group riêng với 1 article_id
- group_id phải là slug (VD: "gia_vang_tang_420usd", "bao_chandra_anh")
"""

        try:
            response = await fast_gemini.generate_content(
                prompt=prompt,
                model_name=self.model_name,
                temperature=0.3,
                max_tokens=2048,
                api_key=api_key
            )
            
            # Parse response
            response_text = response.strip()
            # Extract JSON from markdown code block if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            try:
                clusters = json.loads(response_text)
            except json.JSONDecodeError as json_err:
                print(f"❌ JSON Parse Error: {json_err}")
                print(f"Response text (first 500 chars): {response_text[:500]}")
                raise  # Re-raise to trigger fallback
            
            # Assign group_id to articles
            for group in clusters.get('groups', []):
                group_id = group['group_id']
                article_ids = group['article_ids']
                
                # First article in group is master
                for idx, article_id in enumerate(article_ids):
                    if 0 <= article_id < len(articles):
                        articles[article_id]['group_id'] = group_id
                        articles[article_id]['is_master'] = (idx == 0)
                        articles[article_id]['duplicate_count'] = len(article_ids) - 1 if idx == 0 else 0
                        articles[article_id]['event_summary'] = group.get('event_summary', '')
            
        except Exception as e:
            print(f"❌ AI Clustering error: {e}")
            print(f"Error type: {type(e).__name__}")
            # Fallback: each article is its own group
            for i, article in enumerate(articles):
                if 'group_id' not in article:
                    article['group_id'] = f"article_{i}"
                    article['is_master'] = True
                    article['duplicate_count'] = 0
                    article['event_summary'] = article['title']
        
        return articles


# Singleton
dedup_service = DedupService()
