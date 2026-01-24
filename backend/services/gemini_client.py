import google.generativeai as genai
from config import settings

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
    
    def generate_content(
        self,
        prompt: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.5,
        max_tokens: int = 4096
    ) -> str:
        """
        Generate content using Gemini API
        
        Args:
            prompt: The prompt to send to the model
            model_name: Model to use (gemini-2.0-flash-exp, gemini-1.5-pro, etc.)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            model = genai.GenerativeModel(model_name)
            
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

gemini_client = GeminiClient()
