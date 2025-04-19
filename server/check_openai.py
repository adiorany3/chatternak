import sys
import importlib.metadata
import importlib.util

print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

# Check if openai is installed and get its version
try:
    openai_version = importlib.metadata.version('openai')
    print(f"OpenAI version: {openai_version}")
except importlib.metadata.PackageNotFoundError:
    print("OpenAI package is NOT installed")

# Try to import OpenAI
try:
    import openai
    print(f"OpenAI imported successfully from: {openai.__file__}")
    
    # Try to import error classes directly from openai
    try:
        from openai import APIError, APIConnectionError, RateLimitError
        print("Successfully imported error classes directly from openai")
    except ImportError as e:
        print(f"Failed to import error classes directly from openai: {e}")
        
        # Check if the error types exist in openai.types.error as fallback
        try:
            import openai.types.error
            print("openai.types.error module exists")
            has_module = True
        except ImportError as e:
            print(f"openai.types.error module does NOT exist: {e}")
            has_module = False
        
        # Check what attributes exist in the module
        if has_module:
            print(f"openai.types.error dir: {dir(openai.types.error)}")
            
            # Check for specific error classes
            if hasattr(openai.types.error, 'APIError'):
                print("APIError class exists")
            else:
                print("APIError class does NOT exist")
                
            if hasattr(openai.types.error, 'APIConnectionError'):
                print("APIConnectionError class exists")
            else:
                print("APIConnectionError class does NOT exist")
                
            if hasattr(openai.types.error, 'RateLimitError'):
                print("RateLimitError class exists")
            else:
                print("RateLimitError class does NOT exist")
            
except ImportError as e:
    print(f"Failed to import OpenAI: {e}")

# Check if Google Generative AI (Gemini) is installed
print("\n--- Checking Gemini API Support ---")
try:
    google_genai_version = importlib.metadata.version('google-generativeai')
    print(f"Google Generative AI version: {google_genai_version}")
    
    # Try to import Google Generative AI
    try:
        import google.generativeai as genai
        print(f"Google Generative AI imported successfully")
        
        # Check if we can access key Gemini functionality
        if hasattr(genai, 'configure'):
            print("genai.configure function exists")
        else:
            print("genai.configure function does NOT exist")
            
        if hasattr(genai, 'GenerativeModel'):
            print("genai.GenerativeModel class exists")
        else:
            print("genai.GenerativeModel class does NOT exist")
            
        print("Gemini API is ready to use")
        
    except ImportError as e:
        print(f"Failed to import Google Generative AI: {e}")
        
except importlib.metadata.PackageNotFoundError:
    print("Google Generative AI package is NOT installed. Install with: pip install google-generativeai")