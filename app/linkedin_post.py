import os
import requests
from dotenv import load_dotenv
load_dotenv()

def post_linkedin(content, access_token=None, person_urn=None):
    load_dotenv(override=True)
    token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN")
    urn = person_urn or os.getenv("LINKEDIN_PERSON_URN")

    if not token or not urn:
        print("LinkedIn Error: LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_URN not provided")
        return False

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    data = {
        "author": f"urn:li:person:{urn}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=30
    )
    print("LinkedIn Response:", response.status_code)
    if response.status_code == 201:
        print("LinkedIn Post Published")
        return True
    else:
        print(response.text)
        return False