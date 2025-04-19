import os
import json
import requests
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Debug info
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")
# Get OpenAI version using importlib instead
try:
    import importlib.metadata
    openai_version = importlib.metadata.version('openai')
    print(f"OpenAI version: {openai_version}")
except Exception as e:
    print(f"Could not get OpenAI version: {str(e)}")

# Use direct class imports instead of module imports for error classes
try:
    # Try direct imports from openai module
    from openai import APIError, APIConnectionError, RateLimitError
    print("Successfully imported error classes directly from openai")
except ImportError as e:
    # Define custom error classes as fallback
    class APIError(Exception): pass
    class APIConnectionError(Exception): pass
    class RateLimitError(Exception): pass
    print("Warning: Could not import OpenAI error classes. Using custom fallback classes.")

# Load environment variables from .env file
load_dotenv()

class DeepSeekAPI:
    """Integration with DeepSeek AI API for advanced language processing capabilities using OpenAI client"""
    
    def __init__(self):
        """Initialize the DeepSeek API client using OpenAI SDK"""
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not self.api_key:
            print("Warning: DEEPSEEK_API_KEY not found in environment variables. DeepSeek API integration will not work.")
        
        # Initialize OpenAI client with DeepSeek's base URL
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        except Exception as e:
            print(f"Error initializing DeepSeek client: {str(e)}")
            self.client = None
    
    def generate_response(self, prompt, context=None, temperature=0.7, max_tokens=1000, fallback_response=None):
        """
        Generate a response using DeepSeek AI
        
        Args:
            prompt (str): The user's query
            context (str, optional): Additional context for the model
            temperature (float): Controls randomness (0-1)
            max_tokens (int): Max tokens to generate
            fallback_response (str, optional): Response to return if API call fails
            
        Returns:
            str: Generated response or error message
        """
        if not self.api_key or not self.client:
            return "Error: DeepSeek API key not configured or client initialization failed. Please set DEEPSEEK_API_KEY in your environment."
        
        messages = []
        
        # Add system message with context
        system_message = "You are Chat Ternak, a farming and agriculture AI assistant. "
        system_message += "You provide accurate information about livestock farming in Indonesia. "
        
        if context:
            system_message += f"\nContext information: {context}"
            
        messages.append({"role": "system", "content": system_message})
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            return response.choices[0].message.content
            
        except APIError as e:
            error_message = str(e)
            print(f"DeepSeek API Error: {error_message}")
            
            if "Insufficient Balance" in error_message or "402" in error_message:
                detailed_message = (
                    "Saldo akun DeepSeek tidak mencukupi untuk melakukan permintaan ini. "
                    "Silakan isi ulang saldo akun DeepSeek Anda atau hubungi administrator sistem."
                )
                if fallback_response:
                    return fallback_response
                return detailed_message
            elif "rate limit" in error_message.lower():
                return "Terlalu banyak permintaan ke DeepSeek API. Mohon coba lagi setelah beberapa saat."
            else:
                return f"Maaf, terjadi kesalahan saat menghubungi DeepSeek API: {error_message}"
                
        except APIConnectionError:
            connection_error = "Tidak dapat terhubung ke DeepSeek API. Silakan periksa koneksi internet Anda."
            print(connection_error)
            return fallback_response if fallback_response else connection_error
            
        except RateLimitError:
            rate_limit_error = "Batas penggunaan API DeepSeek telah tercapai. Silakan coba lagi nanti."
            print(rate_limit_error)
            return fallback_response if fallback_response else rate_limit_error
            
        except Exception as e:
            print(f"Unexpected error with DeepSeek API: {str(e)}")
            if fallback_response:
                return fallback_response
            return f"Maaf, terjadi kesalahan saat menghubungi DeepSeek API: {str(e)}"

# Example usage
if __name__ == "__main__":
    deepseek = DeepSeekAPI()
    response = deepseek.generate_response("Bagaimana cara memelihara kambing yang baik?")
    print(response)