from config import settings
from services.app_logger import logger
from services.request_context import get_request_id


def _get_ai_client():
    if settings.AI_PROVIDER == "openai":
        from services.openai_client import openai_client
        return openai_client
    else:
        from services.fast_gemini import fast_gemini
        return fast_gemini


class GeminiClient:
    """
    AI client adapter — tự động chọn Gemini hoặc OpenAI theo AI_PROVIDER trong config.
    """

    async def async_generate_content(
        self,
        prompt: str,
        model_name: str = None,
        temperature: float = 0.5,
        max_tokens: int = 4096,
        api_key: str = None,
    ) -> str:
        client = _get_ai_client()
        # Khi dùng OpenAI, luôn dùng OPENAI_MODEL thay vì Gemini model name.
        if settings.AI_PROVIDER == "openai":
            model_name = settings.OPENAI_MODEL
            try:
                return await client.generate_content(prompt, model_name, temperature, max_tokens, api_key)
            except Exception as exc:
                # Graceful provider failover:
                # If OpenAI key is valid but quota/rate limits are hit, auto-fallback
                # to Gemini to keep user flows available.
                msg = str(exc).lower()
                should_fallback = any(
                    token in msg
                    for token in (
                        "insufficient_quota",
                        "quota",
                        "rate_limit",
                        "429",
                    )
                )
                if should_fallback and settings.GEMINI_API_KEY:
                    logger.warning(
                        "ai.provider.fallback",
                        extra={
                            "event": "ai.provider.fallback",
                            "request_id": get_request_id(),
                            "from_provider": "openai",
                            "to_provider": "gemini",
                            "reason": "openai_quota_or_rate_limited",
                        },
                    )
                    from services.fast_gemini import fast_gemini

                    fallback_model = settings.GEMINI_MODEL
                    return await fast_gemini.generate_content(
                        prompt, fallback_model, temperature, max_tokens, api_key=None
                    )
                raise

        return await client.generate_content(prompt, model_name, temperature, max_tokens, api_key)

    def generate_content(self, *args, **kwargs) -> str:
        return "This method is deprecated. Use async_generate_content instead."


# Singleton
gemini_client = GeminiClient()
