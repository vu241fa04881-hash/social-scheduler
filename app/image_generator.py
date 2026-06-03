import urllib.parse
import requests
import io
import re
import os
import sys
from PIL import Image

# Reconfigure stdout/stderr to prevent UnicodeEncodeError on Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='backslashreplace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(errors='backslashreplace')
except Exception:
    pass

def generate_post_image(image_prompt, output_path="generated_image.jpg", topic="", pollinations_api_key=None):
    print("[Image Generator] Generating Instagram image via Pollinations Engine...")
    
    # Check for pollinations api key from args or environment variable
    api_key = pollinations_api_key or os.getenv("POLLINATIONS_API_KEY")
    if api_key:
        api_key = api_key.strip()
        
    try:
        # Properly clean and URL-encode the text prompt passed from Groq
        encoded_prompt = urllib.parse.quote(image_prompt.strip())
        
        # Use new endpoint if API key is provided, else fallback to standard
        if api_key:
            url = f"https://gen.pollinations.ai/image/{encoded_prompt}?width=1080&height=1080&nologo=true"
            headers = {"Authorization": f"Bearer {api_key}"}
            print("[Image Generator] Using provided Pollinations API Key for generation...")
        else:
            url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1080&height=1080&nologo=true"
            headers = {}
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Open the image using Pillow to guarantee it is saved as a true compliant JPEG
            image = Image.open(io.BytesIO(response.content))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(output_path, 'JPEG', quality=95)
            
            print(f"[Image Generator] Dynamic photo asset saved successfully at: {output_path}")
            return output_path, url
        else:
            print(f"Image API returned an error status code: {response.status_code}")
            
    except Exception as e:
        print(f"Image Generation Error: {e}")
        
    # Dynamic fallback to loremflickr.com based on topic keywords
    try:
        fallback_query = topic.strip() if topic else image_prompt.strip()
        # Keep only alphanumeric characters and spaces/commas, replace spaces with commas
        clean_query = re.sub(r'[^a-zA-Z0-9\s,]', '', fallback_query)
        keywords = ",".join([word.strip() for word in clean_query.split() if word.strip()])
        if not keywords:
            keywords = "social"
            
        print(f"[Image Generator] Attempting dynamic fallback image from loremflickr for keywords: {keywords}...")
        fallback_url = f"https://loremflickr.com/1080/1080/{urllib.parse.quote(keywords)}"
        fallback_response = requests.get(fallback_url, timeout=20, allow_redirects=True)
        
        if fallback_response.status_code == 200:
            image = Image.open(io.BytesIO(fallback_response.content))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(output_path, 'JPEG', quality=95)
            
            print(f"[Image Generator] Dynamic fallback photo asset saved successfully at: {output_path}")
            return output_path, fallback_response.url
        else:
            print(f"Fallback Image API returned status code: {fallback_response.status_code}")
    except Exception as fe:
        print(f"Fallback Image Generation Error: {fe}")
        
    print("[Image Generator] Using static sample image layout fallback.")
    return "sample.jpg", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1080&q=80"