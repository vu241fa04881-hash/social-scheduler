import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def generate_post(topic, groq_api_key=None):
    # Initialize the Groq client
    load_dotenv(override=True)
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Groq API Key not provided")
    client = Groq(api_key=api_key)

    prompt = f"""
    Create platform-specific content about: {topic}

    Format exactly:

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

    # Switched model to the active flagship: llama-3.3-70b-versatile
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=1024,
    )

    return completion.choices[0].message.content