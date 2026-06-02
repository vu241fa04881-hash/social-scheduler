import re
import uuid

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


def publish_post(topic, creds=None):
    if creds is None:
        creds = {}

    print(f"\nGenerating content for: {topic}")

    content = generate_post(topic, groq_api_key=creds.get("GROQ_API_KEY"))

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

    if not instagram_content:
        print("Warning: Instagram content block not found or empty.")
    if not linkedin_content:
        print("Warning: LinkedIn content block not found or empty.")
    if not telegram_content:
        print("Warning: Telegram content block not found or empty.")
    if not image_prompt:
        print("Warning: Image prompt block not found or empty.")

    local_image_path, public_image_url = generate_post_image(
        image_prompt,
        output_path=f"generated_image_{uuid.uuid4().hex}.jpg"
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
        chat_id=creds.get("TELEGRAM_CHAT_ID")
    )

    print("\nPOST PUBLISHED SUCCESSFULLY")