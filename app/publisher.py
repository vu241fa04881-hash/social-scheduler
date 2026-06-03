import re
import uuid
import os
import requests

from app.content_generator import generate_post
from app.telegram_post import send_telegram_message
from app.instagram_post import post_instagram
from app.linkedin_post import post_linkedin
from app.image_generator import generate_post_image


def extract_section(content, start_label, end_label=None):
    if end_label:
        pattern = rf"{re.escape(start_label)}\s*(.*?)(?={re.escape(end_label)})"
    else:
        pattern = rf"{re.escape(start_label)}\s*(.*)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""


def upload_to_tmpfiles(image_path):
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        print(f"[Upload] Uploading user image {image_path} to tmpfiles.org...")
        url = "https://tmpfiles.org/api/v1/upload"
        with open(image_path, "rb") as f:
            response = requests.post(url, files={"file": f}, timeout=20)
        
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("status") == "success":
                file_url = res_data["data"]["url"]
                # Convert standard URL to direct download URL (required by Instagram Graph API)
                direct_url = file_url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
                print(f"[Upload] Upload successful! Direct URL for Instagram: {direct_url}")
                return direct_url
        print(f"[Upload Error] tmpfiles.org returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Upload Error] Failed to upload image: {e}")
    return None


def publish_post(topic, creds=None, website_url=None, image_path=None):
    if creds is None:
        creds = {}

    print(f"\nGenerating content for: {topic}")

    content = generate_post(
        topic, 
        groq_api_key=creds.get("GROQ_API_KEY"),
        website_url=website_url,
        image_path=image_path
    )

    thinking_content = extract_section(
        content,
        "THINKING:",
        "INSTAGRAM:"
    )
    instagram_content = extract_section(
        content,
        "INSTAGRAM:",
        "LINKEDIN:"
    )
    linkedin_content = extract_section(
        content,
        "LINKEDIN:",
        "TELEGRAM:"
    )
    telegram_content = extract_section(
        content,
        "TELEGRAM:",
        "IMAGE_PROMPT:"
    )
    image_prompt = extract_section(
        content,
        "IMAGE_PROMPT:"
    )

    if thinking_content:
        print("\n" + "="*40)
        print("★ AI THINKING PROCESS ★")
        print(thinking_content)
        print("="*40 + "\n")

    if not instagram_content:
        print("Warning: Instagram content block not found or empty.")
    if not linkedin_content:
        print("Warning: LinkedIn content block not found or empty.")
    if not telegram_content:
        print("Warning: Telegram content block not found or empty.")

    # Image logic: If user provided an image, upload to tmpfiles.org and use it.
    # Otherwise, generate image using Pollinations engine.
    local_image_path = None
    public_image_url = None

    if image_path and os.path.exists(image_path):
        public_image_url = upload_to_tmpfiles(image_path)
        if public_image_url:
            local_image_path = image_path
        else:
            print("[Publisher] Public image upload failed. Falling back to Pollinations generation.")

    if not public_image_url:
        if not image_prompt:
            print("Warning: Image prompt block not found or empty.")
        local_image_path, public_image_url = generate_post_image(
            image_prompt,
            output_path=f"generated_image_{uuid.uuid4().hex}.jpg",
            topic=topic,
            pollinations_api_key=creds.get("POLLINATIONS_API_KEY")
        )

    print("\nPublishing...")

    post_instagram(
        instagram_content,
        public_image_url,
        instagram_business_account_id=creds.get("INSTAGRAM_BUSINESS_ACCOUNT_ID"),
        access_token=creds.get("INSTAGRAM_ACCESS_TOKEN")
    )
    post_linkedin(
        linkedin_content,
        access_token=creds.get("LINKEDIN_ACCESS_TOKEN"),
        person_urn=creds.get("LINKEDIN_PERSON_URN")
    )
    send_telegram_message(
        telegram_content,
        bot_token=creds.get("TELEGRAM_BOT_TOKEN"),
        chat_id=creds.get("TELEGRAM_CHAT_ID"),
        image_path=local_image_path
    )

    print("\nPOST PUBLISHED SUCCESSFULLY")