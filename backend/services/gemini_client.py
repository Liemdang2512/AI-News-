from config import settings


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
        # Khi dùng OpenAI, luôn dùng OPENAI_MODEL thay vì Gemini model name
        if settings.AI_PROVIDER == "openai":
            model_name = settings.OPENAI_MODEL
        return await client.generate_content(prompt, model_name, temperature, max_tokens, api_key)

    def generate_content(self, *args, **kwargs) -> str:
        return "This method is deprecated. Use async_generate_content instead."


# Singleton
gemini_client = GeminiClient()
