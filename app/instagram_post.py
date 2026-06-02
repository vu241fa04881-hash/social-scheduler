import os
import certifi
from dotenv import load_dotenv
from instagrapi import Client

os.environ['SSL_CERT_FILE'] = certifi.where()

load_dotenv()

def get_instagram_client(username=None, password=None):
    cl = Client()

    load_dotenv(override=True)
    uname = username or os.getenv("INSTAGRAM_USERNAME")
    pwd = password or os.getenv("INSTAGRAM_PASSWORD")
    
    if not uname or not pwd:
        print("Instagram Error: Credentials not provided")
        return None

    # Determine persistent directory based on DATABASE_PATH
    db_path = os.environ.get("DATABASE_PATH", "data/scheduled_posts.db")
    storage_dir = os.path.dirname(db_path) or "data"
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir, exist_ok=True)
    
    session_file = os.path.join(storage_dir, f"session_{uname}.json")

    if os.path.exists(session_file):
        print(f"Loading saved Instagram session ({session_file})...")
        try:
            cl.load_settings(session_file)
        except Exception as se:
            print(f"Warning: Could not load saved session: {se}")

    try:
        print(f"Logging into Instagram as {uname}...")
        cl.login(uname, pwd)
        
        try:
            cl.dump_settings(session_file)
            print(f"Instagram login successful and session saved to {session_file}.")
        except Exception as de:
            print(f"Warning: Could not save session settings: {de}")
            print("Instagram login successful.")
            
        return cl

    except Exception as e:
        print("Instagram Login Error:", e)
        print("\n" + "!" * 80)
        print("  🔒 INSTAGRAM LOGIN CHALLENGE DETECTED!")
        print("  👉 Instagram has blocked this login attempt because it is from a new location/device.")
        print("  👉 Action Required:")
        print("     1. Open your Instagram app or log in via a browser on this/another device.")
        print("     2. Look for a security check / login alert notification.")
        print("     3. Tap 'This was me' or 'It was me' to approve the connection.")
        print("     4. Once approved, retry publishing. The session will be saved persistently.")
        print("!" * 80 + "\n")
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