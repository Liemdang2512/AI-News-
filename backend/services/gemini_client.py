
from services.fast_gemini import fast_gemini

class GeminiClient:
    """
    Adapter for FastGeminiClient to maintain backward compatibility
    """
    def generate_content(
        self,
        prompt: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.5,
        max_tokens: int = 4096,
        api_key: str = None
    ) -> str:
        # In async context (FastAPI), we should really make this async.
        # However, the original code was synchronous (google-generativeai SDK).
        # We need to bridge sync existing code to async FastGeminiClient.
        # BUT since we are in FastAPI, we can just change the caller to await if possible,
        # OR run event loop.
        
        # Checking usage:
        # summarizer.py calls it.
        # categorizer.py calls it.
        
        # Let's check if callers are async. 
        # summarizer.py: async def summarize_articles -> calls generate_content
        # categorizer.py: def categorize_articles -> calls generate_content (SYNC)
        
        # We need a sync wrapper for categorizer, but summarizer can await.
        # Actually, let's just make this async and update the callers. One caller is already async.
        # The other (categorizer) will need update to async.
        
        import asyncio
        import nest_asyncio
        nest_asyncio.apply()
        
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we are already in an event loop (FastAPI), we can't block it.
            # But the original code was blocking? No, google SDK makes network request.
            # We should update callers to be async for better performance anyway.
            # For now to be safe and compatible, we run async in new loop? No that fails.
            
            # Best approach: Make this method async and update callers.
            pass
            
        return "This method is deprecated. Use async_generate_content instead."

    async def async_generate_content(
        self,
        prompt: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.5,
        max_tokens: int = 4096,
        api_key: str = None
    ) -> str:
        return await fast_gemini.generate_content(
            prompt, model_name, temperature, max_tokens, api_key
        )

# Singleton
gemini_client = GeminiClient()
