import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

def post_instagram(caption, image_url, instagram_business_account_id=None, access_token=None):
    load_dotenv(override=True)
    ig_user_id = instagram_business_account_id or os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")

    if not ig_user_id or not token:
        print("Instagram Error: INSTAGRAM_BUSINESS_ACCOUNT_ID or INSTAGRAM_ACCESS_TOKEN not provided")
        return False

    print("Uploading photo to Instagram via Graph API...")
    
    # Step 1: Create media container
    # Endpoint: POST /v19.0/{ig-user-id}/media
    url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": token
    }
    
    try:
        response = requests.post(url, data=payload, timeout=30)
        response_data = response.json()
        
        if response.status_code != 200:
            print("Instagram Media Container Error:", response_data)
            return False
            
        container_id = response_data.get("id")
        if not container_id:
            print("Instagram Error: Failed to retrieve container ID")
            return False
            
        print(f"Media container created successfully (ID: {container_id}).")
        
        # Step 2: Poll container status until FINISHED
        # Endpoint: GET /v19.0/{container-id}?fields=status_code
        status_url = f"https://graph.facebook.com/v19.0/{container_id}"
        status_params = {
            "fields": "status_code",
            "access_token": token
        }
        
        print("Waiting for media container to finish processing...")
        max_attempts = 12  # Try for 1 minute
        for attempt in range(max_attempts):
            time.sleep(5)
            status_response = requests.get(status_url, params=status_params, timeout=10)
            status_data = status_response.json()
            
            if status_response.status_code != 200:
                print("Warning: Failed to check container status:", status_data)
                continue
                
            status_code = status_data.get("status_code")
            print(f"Container status: {status_code} (attempt {attempt+1}/{max_attempts})")
            
            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                print("Instagram Error: Media container processing failed.")
                return False
        else:
            print("Instagram Error: Container processing timed out.")
            return False
            
        # Step 3: Publish container
        # Endpoint: POST /v19.0/{ig-user-id}/media_publish
        publish_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
        publish_payload = {
            "creation_id": container_id,
            "access_token": token
        }
        
        publish_response = requests.post(publish_url, data=publish_payload, timeout=30)
        publish_data = publish_response.json()
        
        if publish_response.status_code == 200:
            print(f"Instagram Post Published Successfully (Media ID: {publish_data.get('id')})")
            return True
        else:
            print("Instagram Publish Error:", publish_data)
            return False
            
    except Exception as e:
        print("Instagram Graph API Error:", e)
        return False