import time
import httpx
from config import settings
import json

from services.app_logger import logger, redact_secrets
from services.request_context import get_request_id


class OpenAIClient:
    """
    Lightweight OpenAI client using direct REST API calls via httpx.
    Interface tương tự FastGeminiClient để dễ thay thế.
    """

    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY

    async def generate_content(
        self,
        prompt: str,
        model_name: str = None,
        temperature: float = 0.5,
        max_tokens: int = 4096,
        api_key: str = None,
    ) -> str:
        key = api_key if api_key else self.api_key
        if not key:
            raise Exception("OpenAI API Key is missing")

        resolved_model = model_name or settings.OPENAI_MODEL

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        }

        payload = {
            "model": resolved_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient() as client:
            try:
                timeout = settings.GEMINI_REQUEST_TIMEOUT  # reuse timeout setting

                logger.info(
                    "ai.openai.request",
                    extra={
                        "event": "ai.openai.request",
                        "request_id": get_request_id(),
                        "model": resolved_model,
                        "prompt_chars": len(prompt),
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "api_key_present": bool(key),
                    },
                )
                _t0 = time.monotonic()

                response = await client.post(
                    self.BASE_URL, headers=headers, json=payload, timeout=timeout
                )

                latency_ms = int((time.monotonic() - _t0) * 1000)

                if response.status_code != 200:
                    logger.error(
                        "ai.openai.error",
                        extra={
                            "event": "ai.openai.error",
                            "request_id": get_request_id(),
                            "status_code": response.status_code,
                            "latency_ms": latency_ms,
                            "error_preview": redact_secrets(response.text[:400]),
                        },
                    )
                    raise Exception(
                        f"OpenAI API Error ({response.status_code}): {response.text[:400]}"
                    )

                logger.info(
                    "ai.openai.response",
                    extra={
                        "event": "ai.openai.response",
                        "request_id": get_request_id(),
                        "status_code": response.status_code,
                        "latency_ms": latency_ms,
                    },
                )

                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    raise Exception(
                        f"OpenAI response không có choices: {json.dumps(data, ensure_ascii=False)[:600]}"
                    )

                text = (choices[0].get("message") or {}).get("content", "").strip()
                if not text:
                    raise Exception("OpenAI trả về content rỗng")

                return text

            except Exception as e:
                raise Exception(f"OpenAIClient Error: {str(e)}")

    async def async_generate_content(
        self,
        prompt: str,
        model_name: str = None,
        temperature: float = 0.5,
        max_tokens: int = 4096,
        api_key: str = None,
    ) -> str:
        return await self.generate_content(prompt, model_name, temperature, max_tokens, api_key)


# Singleton
openai_client = OpenAIClient()
