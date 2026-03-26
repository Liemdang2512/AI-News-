
import time
import httpx
from config import settings
import json

from services.app_logger import logger, redact_secrets
from services.request_context import get_request_id


class FastGeminiClient:
    """
    Lightweight Gemini Client using direct REST API calls via httpx.
    Replaces the heavy google-generativeai SDK.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    BASE_URL_BETA = "https://generativelanguage.googleapis.com/v1beta/models"
    
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
        safe_url = redact_secrets(url)

        headers = {
            "Content-Type": "application/json"
        }

        # Tin tức thường có từ khóa "nhạy cảm" theo ngữ cảnh; BLOCK_ONLY_HIGH giảm chặn nhầm
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

                logger.info(
                    "ai.gemini.request",
                    extra={
                        "event": "ai.gemini.request",
                        "request_id": get_request_id(),
                        "model": resolved_model,
                        "prompt_chars": len(prompt),
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": max_tokens,
                        },
                    },
                )
                _t0 = time.monotonic()

                response = await client.post(url, headers=headers, json=payload, timeout=timeout)

                latency_ms = int((time.monotonic() - _t0) * 1000)

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(
                        "ai.gemini.error",
                        extra={
                            "event": "ai.gemini.error",
                            "request_id": get_request_id(),
                            "status_code": response.status_code,
                            "latency_ms": latency_ms,
                            "error_preview": redact_secrets(error_text[:400]),
                        },
                    )
                    raise Exception(f"Gemini API Error ({response.status_code}): {error_text}")

                logger.info(
                    "ai.gemini.response",
                    extra={
                        "event": "ai.gemini.response",
                        "request_id": get_request_id(),
                        "status_code": response.status_code,
                        "latency_ms": latency_ms,
                    },
                )
                
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

    async def generate_content_with_url(
        self,
        article_url: str,
        prompt: str,
        model_name: str = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        api_key: str = None
    ) -> str:
        """
        Generate content bằng cách cho Gemini tự đọc URL qua url_context tool.
        Dùng v1beta endpoint (yêu cầu bởi url_context tool).
        """
        key = api_key if api_key else self.api_key
        if not key:
            raise Exception("Gemini API Key is missing")

        resolved_model = model_name or settings.GEMINI_MODEL
        url = f"{self.BASE_URL_BETA}/{resolved_model}:generateContent?key={key}"
        safe_url = redact_secrets(url)

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]

        payload = {
            "tools": [{"url_context": {}}],
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

                logger.info(
                    "ai.gemini.request_url_context",
                    extra={
                        "event": "ai.gemini.request_url_context",
                        "request_id": get_request_id(),
                        "model": resolved_model,
                        "prompt_chars": len(prompt),
                        "safe_url": safe_url,
                        "article_url": article_url,
                    },
                )
                _t0 = time.monotonic()

                response = await client.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=timeout)

                latency_ms = int((time.monotonic() - _t0) * 1000)

                if response.status_code != 200:
                    logger.error(
                        "ai.gemini.error",
                        extra={
                            "event": "ai.gemini.error",
                            "request_id": get_request_id(),
                            "status_code": response.status_code,
                            "latency_ms": latency_ms,
                            "error_preview": redact_secrets(response.text[:400]),
                        },
                    )
                    raise Exception(f"Gemini API Error ({response.status_code}): {response.text[:400]}")

                logger.info(
                    "ai.gemini.response",
                    extra={
                        "event": "ai.gemini.response",
                        "request_id": get_request_id(),
                        "status_code": response.status_code,
                        "latency_ms": latency_ms,
                    },
                )

                data = response.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    pf = data.get("promptFeedback")
                    raise Exception(
                        f"Gemini không trả về candidates: {json.dumps(pf or data, ensure_ascii=False)[:600]}"
                    )

                c0 = candidates[0]
                parts = (c0.get("content") or {}).get("parts") or []
                texts: list[str] = [p["text"] for p in parts if isinstance(p, dict) and p.get("text")]
                text = "".join(texts).strip()

                if not text:
                    fr = c0.get("finishReason")
                    raise Exception(f"Gemini trả về candidate rỗng. finishReason={fr!r}")

                return text

            except Exception as e:
                raise Exception(f"FastGeminiClient URL Error: {str(e)}")

# Singleton instance
fast_gemini = FastGeminiClient()
