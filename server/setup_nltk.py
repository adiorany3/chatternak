import nltk
import ssl
import time
import sys

def download_nltk_data():
    # Try to create an unverified SSL context to handle SSL certificate issues
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    # List of data packages to download with retry logic
    packages = ['wordnet', 'punkt', 'stopwords', 'averaged_perceptron_tagger']
    
    for package in packages:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                print(f"Downloading NLTK package: {package} (attempt {attempt+1}/{max_attempts})")
                nltk.download(package, quiet=False)
                break
            except Exception as e:
                print(f"Error downloading {package}: {str(e)}")
                if attempt < max_attempts - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Failed to download {package} after {max_attempts} attempts.")
                    print("You may need to download it manually later with:")
                    print(f"import nltk; nltk.download('{package}')")

if __name__ == "__main__":
    print("Starting NLTK data download...")
    download_nltk_data()
    print("NLTK setup completed.")