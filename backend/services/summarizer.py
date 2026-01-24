import httpx
from bs4 import BeautifulSoup
from typing import List
from services.gemini_client import gemini_client
from prompts import SUMMARIZE_PROMPT

class Summarizer:
    """
    Fetches article content and generates AI summaries
    Replaces ai_browser + ai_multimodal nodes from JSON workflow
    """
    
    async def summarize_articles(self, urls: List[str], api_key: str = None) -> str:
        """
        Fetch article content and generate summaries using Gemini AI
        
        Args:
            urls: List of article URLs to summarize
            api_key: Optional custom API key
            
        Returns:
            Formatted markdown summaries
        """
        # Fetch all article contents
        articles_data = []
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for url in urls:
                try:
                    response = await client.get(url)
                    content = self._extract_content(response.text)
                    articles_data.append({
                        "url": url,
                        "content": content
                    })
                except Exception as e:
                    print(f"Error fetching {url}: {str(e)}")
                    continue
        
        # Format articles content for the prompt
        articles_content = ""
        for i, article in enumerate(articles_data, 1):
            articles_content += f"\n\n--- BÀI VIẾT {i} ---\n"
            articles_content += f"URL: {article['url']}\n"
            articles_content += f"NỘI DUNG:\n{article['content']}\n"
        
        # Load prompt from prompts.py and insert content
        prompt = SUMMARIZE_PROMPT.format(articles_content=articles_content)

        try:
            response = gemini_client.generate_content(
                prompt=prompt,
                model_name="gemini-2.0-flash",
                temperature=0.2,
                max_tokens=30000,
                api_key=api_key
            )
            return response
        except Exception as e:
            raise Exception(f"Summarization failed: {str(e)}")
    
    def _extract_content(self, html: str) -> str:
        """
        Extract main content from HTML using BeautifulSoup
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit to first 8000 characters to avoid token limits
        return text[:8000]

summarizer = Summarizer()
