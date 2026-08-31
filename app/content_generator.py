import os
import base64
import requests
import re
import hashlib
from PIL import Image
import io
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "openai/gpt-oss-120b")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")

def generate_content_hash(user_content):
    """
    Generate a hash of the user-provided content for reference/tracking.
    This is optional and used when user provides their own content.
    """
    if not user_content:
        return None
    try:
        content_bytes = user_content.encode('utf-8')
        content_hash = hashlib.sha256(content_bytes).hexdigest()[:16]  # First 16 chars
        return content_hash
    except Exception as e:
        print(f"[Hash Generation] Error generating content hash: {e}")
        return None

def ensure_dependencies():
    """
    Checks that required Python packages are installed.
    Prints a reminder to run `install_dependencies.bat` if needed.
    """
    try:
        import importlib
        required = {
            "groq": "groq",
            "requests": "requests",
            "beautifulsoup4": "bs4",
            "pillow": "PIL",
            "dotenv": "dotenv",
        }
        missing = [package for package, module in required.items()
                   if importlib.util.find_spec(module) is None]
        if missing:
            print("[Dependency Warning] Missing packages:", ", ".join(missing))
            print("[Hint] Run install_dependencies.bat to install them.")
    except Exception as e:
        print("[Dependency Check Error]", e)


def scrape_website(url):
    if not url:
        return ""
    try:
        print(f"[Scraper] Fetching website content from: {url}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Decompose interactive/layout elements that contain noise
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
            
        text = soup.get_text(separator=" ")
        
        # Clean up whitespaces
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = " ".join(chunk for chunk in chunks if chunk)
        
        # Return truncated text to fit LLM context cleanly
        truncated = cleaned_text[:4000]
        print(f"[Scraper] Scraping successful! Character count: {len(truncated)}")
        return truncated
    except Exception as e:
        print(f"[Scraper] Error scraping URL {url}: {e}")
        return f"[Failed to load content from URL: {str(e)}]"

def search_duckduckgo(query):
    if not query:
        return None
    try:
        print(f"[Search] Searching DuckDuckGo for: '{query}'...")
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        data = {"q": query}
        response = requests.post(url, headers=headers, data=data, timeout=12)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for a in soup.find_all("a", class_="result__a"):
                href = a.get("href")
                if href:
                    # DuckDuckGo wraps links in redirection URLs
                    if href.startswith("/l/?"):
                        from urllib.parse import urlparse, parse_qs
                        parsed = urlparse(href)
                        uddg = parse_qs(parsed.query).get("uddg")
                        if uddg:
                            href = uddg[0]
                    print(f"[Search] Top result found: {href}")
                    return href
        print(f"[Search] DuckDuckGo returned code {response.status_code}")
    except Exception as e:
        print(f"[Search Error] DuckDuckGo search failed: {e}")
    return None

def make_search_decision(topic, client):
    prompt = f"""
    Analyze the user's post request/topic: "{topic}"
    
    Determine if writing this post would benefit from getting up-to-date information by searching the web (e.g., if it refers to news, recent events, facts, latest technology, products, or information that changes over time).
    
    Response format exactly:
    NEEDS_SEARCH: YES or NO
    SEARCH_QUERY: [DuckDuckGo search query, keep empty if NO]
    """
    try:
        completion = client.chat.completions.create(
            model=GROQ_TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=100
        )
        content = completion.choices[0].message.content
        
        needs_search = "NEEDS_SEARCH: YES" in content.upper()
        search_query = ""
        
        if needs_search:
            match = re.search(r"SEARCH_QUERY:\s*(.*)", content, re.I)
            if match:
                search_query = match.group(1).strip()
            if not search_query:
                search_query = topic
                
        return needs_search, search_query
    except Exception as e:
        print(f"[Search Decision Error] {e}")
        return False, ""

def analyze_image_with_groq(image_path, api_key):
    if not image_path or not os.path.exists(image_path):
        return ""
    if not api_key:
        print("[Vision Warning] No Groq API key supplied. Skipping image analysis.")
        return "[Error: Groq API key missing for image analysis]"
        
    try:
        print(f"[Vision] Performing image analysis on: {image_path}...")
        
        # Open and convert image to RGB, then output base64 encoded JPEG bytes
        with Image.open(image_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_bytes = buffered.getvalue()
            
        base64_image = base64.b64encode(img_bytes).decode("utf-8")
        
        client = Groq(api_key=api_key)
        
        # Use the configured Groq vision model.
        completion = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this image and describe what is happening, the subject, the mood, visual elements, and any text visible. Write a detailed summary that can be used to draft matching social media posts."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.5,
            max_tokens=512
        )
        
        description = completion.choices[0].message.content
        print(f"[Vision] Image analyzed successfully! Description snippet: {description[:100]}...")
        return description
    except Exception as e:
        print(f"[Vision] Error during image analysis: {e}")
        return f"[Failed to analyze image: {str(e)}]"

def generate_post(topic, groq_api_key=None, website_url=None, image_path=None, user_content=None):
    load_dotenv(override=True)
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    ensure_dependencies()
    if not api_key:
        raise ValueError("Groq API Key not provided")
        
    client = Groq(api_key=api_key)
    
    # Generate content hash if user provided content
    content_hash = None
    if user_content:
        content_hash = generate_content_hash(user_content)
        print(f"[Content] User-provided content hash: {content_hash}")
        
    # Get scraper context. Prioritize manual website URL if provided.
    # Otherwise, decide autonomously if search is needed.
    website_context = ""
    target_url = website_url
    
    if website_url:
        website_context = scrape_website(website_url)
    else:
        # Only perform auto-search if user hasn't provided their own content
        if not user_content:
            needs_search, search_query = make_search_decision(topic, client)
            if needs_search and search_query:
                print(f"[Search Decision] AI decided search is beneficial for topic: '{topic}'")
                searched_url = search_duckduckgo(search_query)
                if searched_url:
                    target_url = searched_url
                    website_context = scrape_website(searched_url)
            else:
                print("[Search Decision] AI decided no web search is needed for this topic.")
        else:
            print("[Search Decision] Skipping web search since user provided custom content.")
        
    # Get image context if image path is provided
    image_context = ""
    if image_path:
        image_context = analyze_image_with_groq(image_path, api_key)
        
    prompt = f"Create platform-specific social media posts based on the user's primary topic.\n"
    prompt += f"Primary Topic: {topic}\n"
    
    # Add user-provided content if available
    if user_content:
        prompt += f"\nUser-Provided Content (Reference):\n{user_content}\n"
        if content_hash:
            prompt += f"[Content Reference Hash: {content_hash}]\n"
    
    if website_context:
        prompt += f"\nAdditional Context Scraped from URL ({target_url}):\n{website_context}\n"
        
    if image_context:
        prompt += f"\nAdditional Context Analyzed from Uploaded Image:\n{image_context}\n"

    prompt += """
    Format exactly:

    THINKING:
    Provide a brief thinking process details explaining your content plan and reasoning based on the inputs provided (topic, user content, website url, and/or image description).

    INSTAGRAM:
    short trendy caption with hashtags

    LINKEDIN:
    professional detailed post

    TELEGRAM:
    short engaging message

    IMAGE_PROMPT:
    A clear, highly descriptive text-to-image prompt to generate a visually appealing graphic or photo matching this topic for Instagram. Do not include styling buzzwords like 'photorealistic', just describe the scene.

    Make all contents unique.
    """

    # Use the configured Groq text model for post generation.
    completion = client.chat.completions.create(
        model=GROQ_TEXT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=1500,
    )

    return completion.choices[0].message.content