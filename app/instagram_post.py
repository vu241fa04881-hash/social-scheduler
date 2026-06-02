import os
import certifi
from dotenv import load_dotenv
from instagrapi import Client

os.environ['SSL_CERT_FILE'] = certifi.where()

load_dotenv()

SESSION_FILE = "session.json"


def get_instagram_client(username=None, password=None):

    cl = Client()

    load_dotenv(override=True)
    uname = username or os.getenv("INSTAGRAM_USERNAME")
    pwd = password or os.getenv("INSTAGRAM_PASSWORD")
    
    if not uname or not pwd:
        print("Instagram Error: Credentials not provided")
        return None

    try:
        print(f"Logging into Instagram as {uname} (in-memory)...")
        cl.login(uname, pwd)
        print("Instagram login successful.")
        return cl

    except Exception as e:
        print("Instagram Login Error:", e)
        print("If Instagram requires verification, update instagrapi or resolve the challenge manually first.")
        return None


def post_instagram(caption, image_path, username=None, password=None):

    if not os.path.exists(image_path):
        print(f"Instagram Error: '{image_path}' not found.")
        return

    cl = get_instagram_client(username, password)

    if cl is None:
        return

    try:

        print("Uploading photo to Instagram...")

        cl.photo_upload(
            image_path,
            caption
        )

        print("Instagram Post Published Successfully")

    except Exception as e:

        print("Instagram Upload Error:", e)