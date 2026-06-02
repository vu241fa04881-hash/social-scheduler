import urllib.parse
import requests
import io
from PIL import Image

def generate_post_image(image_prompt, output_path="generated_image.jpg"):
    print("🎨 Generating Instagram image via Pollinations Engine...")
    try:
        # Properly clean and URL-encode the text prompt passed from Groq
        encoded_prompt = urllib.parse.quote(image_prompt.strip())
        
        # Pulls a high-quality 1:1 square aspect ratio image perfect for social grids
        url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1080&height=1080&nologo=true"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # Open the image using Pillow to guarantee it is saved as a true compliant JPEG
            image = Image.open(io.BytesIO(response.content))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(output_path, 'JPEG', quality=95)
            
            print(f"✅ Dynamic photo asset saved successfully at: {output_path}")
            return output_path, url
        else:
            print(f"Image API returned an error status code: {response.status_code}")
            
    except Exception as e:
        print(f"Image Generation Error: {e}")
        
    print("⚠️ Using static sample image layout fallback.")
    return "sample.jpg", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1080&q=80"