
import httpx
from config import settings
import json

class FastGeminiClient:
    """
    Lightweight Gemini Client using direct REST API calls via httpx.
    Replaces the heavy google-generativeai SDK.
    """
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        
    async def generate_content(
        self,
        prompt: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.5,
        max_tokens: int = 4096,
        api_key: str = None
    ) -> str:
        """
        Generate content using Gemini REST API
        """
        key = api_key if api_key else self.api_key
        if not key:
            raise Exception("Gemini API Key is missing")
            
        url = f"{self.BASE_URL}/{model_name}:generateContent?key={key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=60.0)
                
                if response.status_code != 200:
                    error_text = response.text
                    raise Exception(f"Gemini API Error ({response.status_code}): {error_text}")
                
                data = response.json()
                
                # Extract text from response
                try:
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    return text
                except (KeyError, IndexError):
                    # Handle safety blocks or empty responses
                    if 'promptFeedback' in data:
                        return f"Blocked by safety filters: {json.dumps(data['promptFeedback'])}"
                    return ""
                    
            except Exception as e:
                raise Exception(f"FastGeminiClient Error: {str(e)}")

# Singleton instance
fast_gemini = FastGeminiClient()
