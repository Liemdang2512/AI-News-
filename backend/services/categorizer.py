from typing import List, Dict
from services.gemini_client import gemini_client
from prompts import CATEGORIZE_PROMPT

class Categorizer:
    """
    Categorizes articles into 4 main categories using Gemini AI
    Uses prompt from prompts.py file
    """
    
    def categorize_articles(self, articles_text: str) -> str:
        """
        Categorize articles into: Xã hội, Kinh tế, Pháp luật, Thế giới
        
        Args:
            articles_text: Raw text containing article URLs and metadata
            
        Returns:
            Categorized article list as formatted text
        """
        # Load prompt from prompts.py
        prompt = CATEGORIZE_PROMPT.format(articles_text=articles_text)

        try:
            response = gemini_client.generate_content(
                prompt=prompt,
                model_name="gemini-2.0-flash",
                temperature=0,
                max_tokens=30000
            )
            return response
        except Exception as e:
            raise Exception(f"Categorization failed: {str(e)}")

categorizer = Categorizer()
