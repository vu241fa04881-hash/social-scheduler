import re
import uuid
import os
import requests
from html import unescape
from PIL import Image

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
        normalized_path = f"{image_path}.instagram.jpg"
        with Image.open(image_path) as image:
            image.convert("RGB").save(normalized_path, "JPEG", quality=95)

        with open(normalized_path, "rb") as f:
            response = requests.post(url, files={"file": f}, timeout=20)
        
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("status") == "success":
                file_url = res_data["data"]["url"]
                page_url = file_url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
                page_response = requests.get(page_url, timeout=20)
                page_response.raise_for_status()

                # tmpfiles first returns an HTML page; its canonical link contains
                # the timestamped path that serves the actual image bytes.
                matches = re.findall(
                    r"https://tmpfiles\.org/dl/[^\"'\s<]+",
                    unescape(page_response.text),
                )
                direct_url = next((match for match in matches if match != page_url), None)
                if not direct_url:
                    print("[Upload Error] tmpfiles.org did not provide a direct image URL")
                    return None

                image_response = requests.get(direct_url, stream=True, timeout=20)
                content_type = image_response.headers.get("Content-Type", "")
                image_response.close()
                if not content_type.startswith("image/"):
                    print(f"[Upload Error] Direct URL returned non-image content: {content_type}")
                    return None

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

    # Reasoning-capable models may wrap their answer in private thought tags.
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.I | re.S).strip()

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
        print("Warning: Instagram content block not found or empty; skipping Instagram.")
    if not linkedin_content:
        print("Warning: LinkedIn content block not found or empty; skipping LinkedIn.")
    if not telegram_content:
        print("Warning: Telegram content block not found or empty; skipping Telegram.")

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

    results = {}
    if instagram_content:
        results["Instagram"] = post_instagram(
            instagram_content,
            public_image_url,
            instagram_business_account_id=creds.get("INSTAGRAM_BUSINESS_ACCOUNT_ID"),
            access_token=creds.get("INSTAGRAM_ACCESS_TOKEN")
        )
    if linkedin_content:
        results["LinkedIn"] = post_linkedin(
            linkedin_content,
            access_token=creds.get("LINKEDIN_ACCESS_TOKEN"),
            person_urn=creds.get("LINKEDIN_PERSON_URN")
        )
    if telegram_content:
        results["Telegram"] = send_telegram_message(
            telegram_content,
            bot_token=creds.get("TELEGRAM_BOT_TOKEN"),
            chat_id=creds.get("TELEGRAM_CHAT_ID"),
            image_path=local_image_path
        )

    failed = [platform for platform, success in results.items() if success is False]
    succeeded = [platform for platform, success in results.items() if success is True]
    if failed:
        print(f"\nPUBLISHING INCOMPLETE - succeeded: {', '.join(succeeded) or 'none'}; failed: {', '.join(failed)}")
        return results

    print("\nPOST PUBLISHED SUCCESSFULLY")
    return results