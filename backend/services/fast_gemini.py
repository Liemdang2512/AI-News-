
import httpx
from config import settings
import json

class FastGeminiClient:
    """
    Lightweight Gemini Client using direct REST API calls via httpx.
    Replaces the heavy google-generativeai SDK.
    """
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1/models"
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        
    async def generate_content(
        self,
        prompt: str,
        model_name: str = None,
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

        resolved_model = model_name or settings.GEMINI_MODEL
        url = f"{self.BASE_URL}/{resolved_model}:generateContent?key={key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Tin tức thường có từ khóa “nhạy cảm” theo ngữ cảnh; BLOCK_ONLY_HIGH giảm chặn nhầm
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            },
            "safetySettings": safety_settings,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                timeout = settings.GEMINI_REQUEST_TIMEOUT
                response = await client.post(url, headers=headers, json=payload, timeout=timeout)
                
                if response.status_code != 200:
                    error_text = response.text
                    raise Exception(f"Gemini API Error ({response.status_code}): {error_text}")
                
                data = response.json()

                candidates = data.get("candidates") or []
                if not candidates:
                    pf = data.get("promptFeedback")
                    if pf:
                        raise Exception(
                            f"Gemini không trả về candidates: {json.dumps(pf, ensure_ascii=False)[:800]}"
                        )
                    raise Exception(
                        f"Gemini response không có candidates: {json.dumps(data, ensure_ascii=False)[:600]}"
                    )

                c0 = candidates[0]
                parts = (c0.get("content") or {}).get("parts") or []
                texts: list[str] = []
                for p in parts:
                    if isinstance(p, dict) and p.get("text"):
                        texts.append(p["text"])
                text = "".join(texts).strip()

                if not text:
                    fr = c0.get("finishReason")
                    pf = data.get("promptFeedback")
                    hint = f" finishReason={fr!r}"
                    if pf:
                        hint += f" promptFeedback={json.dumps(pf, ensure_ascii=False)[:500]}"
                    raise Exception(f"Gemini trả về candidate rỗng.{hint}")

                return text
                    
            except Exception as e:
                raise Exception(f"FastGeminiClient Error: {str(e)}")

# Singleton instance
fast_gemini = FastGeminiClient()
