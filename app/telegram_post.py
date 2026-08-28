import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.request import HTTPXRequest
import asyncio

async def send_message(message, bot_token=None, chat_id=None, image_path=None):
    load_dotenv(override=True)
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    cid = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not cid:
        print("Telegram Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not provided")
        return False
        
    request = HTTPXRequest(
        connect_timeout=10,
        read_timeout=20,
        write_timeout=20,
        pool_timeout=10,
    )
    bot = Bot(token=token, request=request)

    if image_path and os.path.exists(image_path):
        print(f"Sending photo to Telegram (Chat ID: {cid})...")
        with open(image_path, 'rb') as photo_file:
            caption = message[:1024] if message else ""
            await asyncio.wait_for(
                bot.send_photo(chat_id=cid, photo=photo_file, caption=caption),
                timeout=30,
            )
    else:
        print(f"Sending text message to Telegram (Chat ID: {cid})...")
        await asyncio.wait_for(
            bot.send_message(chat_id=cid, text=message),
            timeout=30,
        )
    return True

def send_telegram_message(message, bot_token=None, chat_id=None, image_path=None):
    import threading
    exception = None
    result = False
    
    def target():
        nonlocal exception, result
        try:
            result = asyncio.run(send_message(message, bot_token, chat_id, image_path))
        except Exception as e:
            exception = e
            
    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=35)

    if thread.is_alive():
        raise TimeoutError("Telegram request timed out after 35 seconds")
    
    if exception:
        raise exception                                                                                                                                    

    return result