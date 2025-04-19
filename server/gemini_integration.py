import google.generativeai as genai
import os
from typing import Optional, Dict, Any

class GeminiAPI:
    """Integration class for Google's Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini API client
        
        Args:
            api_key (str, optional): Gemini API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: No Gemini API key provided. Please set GEMINI_API_KEY environment variable.")
        else:
            genai.configure(api_key=self.api_key)
    
    def generate_response(self, prompt: str, context: str = "", 
                        temperature: float = 0.7, max_tokens: int = 800,
                        fallback_response: Optional[str] = None) -> str:
        """Generate a response from Gemini API
        
        Args:
            prompt (str): The user's query or prompt
            context (str, optional): Additional context to provide to the model
            temperature (float, optional): Controls randomness in generation (0.0-1.0)
            max_tokens (int, optional): Maximum number of tokens to generate
            fallback_response (str, optional): Response to return if the API call fails
            
        Returns:
            str: The generated response
        """
        try:
            if not self.api_key:
                if fallback_response:
                    return fallback_response
                return "Gemini API key is not configured. Please set the GEMINI_API_KEY environment variable."
            
            # Configure the generation parameters
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": 0.9,
                "top_k": 40
            }
            
            # Create the model
            model = genai.GenerativeModel(
                model_name="gemini-pro",
                generation_config=generation_config
            )
            
            # Prepare the complete prompt with context
            complete_prompt = f"{context}\n\nPertanyaan: {prompt}"
            
            # Generate content
            response = model.generate_content(complete_prompt)
            
            # Extract the text from the response
            return response.text
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            if fallback_response:
                return fallback_response
            return f"Maaf, terjadi kesalahan saat berkomunikasi dengan Gemini API: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if the Gemini API is available and properly configured
        
        Returns:
            bool: True if the API is available, False otherwise
        """
        if not self.api_key:
            return False
            
        try:
            # Try a simple generation to test the API
            model = genai.GenerativeModel(model_name="gemini-pro")
            response = model.generate_content("Hello")
            return True
        except Exception as e:
            print(f"Gemini API check failed: {str(e)}")
            return False