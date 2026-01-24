from typing import List, Dict
from services.gemini_client import gemini_client
from prompts import ARTICLE_CATEGORIZE_PROMPT
import asyncio

class ArticleCategorizer:
    """
    Categorizes individual articles into 4 main categories using Gemini AI
    Categories: KINH TẾ, TÀI CHÍNH, XÃ HỘI, PHÁP LUẬT
    """
    
    VALID_CATEGORIES = ["KINH TẾ", "TÀI CHÍNH", "XÃ HỘI", "PHÁP LUẬT"]
    
    def categorize_article(self, title: str, description: str) -> str:
        """
        Categorize a single article based on title and description
        
        Args:
            title: Article title
            description: Article description
            
        Returns:
            One of: KINH TẾ, TÀI CHÍNH, XÃ HỘI, PHÁP LUẬT
        """
        # Clean description (remove HTML tags)
        import re
        clean_desc = re.sub(r'<[^>]+>', '', description)
        
        # Create prompt
        prompt = ARTICLE_CATEGORIZE_PROMPT.format(
            title=title,
            description=clean_desc[:500]  # Limit description length
        )
        
        try:
            response = gemini_client.generate_content(
                prompt=prompt,
                model_name="gemini-2.0-flash",
                temperature=0,
                max_tokens=50
            )
            
            # Clean and validate response
            category = response.strip().upper()
            
            # Ensure it's one of the valid categories
            if category in self.VALID_CATEGORIES:
                return category
            
            # Fallback: try to find category in response
            for valid_cat in self.VALID_CATEGORIES:
                if valid_cat in category:
                    return valid_cat
            
            # Default fallback
            return "XÃ HỘI"
            
        except Exception as e:
            print(f"Categorization error for '{title}': {str(e)}")
            return "XÃ HỘI"  # Default category on error
    
    async def categorize_articles_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Categorize multiple articles (process in batches to avoid rate limits)
        
        Args:
            articles: List of article dictionaries with 'title' and 'description'
            
        Returns:
            Same list with 'category' field updated
        """
        categorized = []
        
        # Process in smaller batches with longer delays to avoid rate limits
        batch_size = 3  # Reduced from 5 to 3
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            for article in batch:
                category = self.categorize_article(
                    article.get('title', ''),
                    article.get('description', '')
                )
                article['category'] = category
                categorized.append(article)
            
            # Longer delay between batches (2 seconds)
            if i + batch_size < len(articles):
                await asyncio.sleep(2.0)
        
        return categorized

article_categorizer = ArticleCategorizer()
