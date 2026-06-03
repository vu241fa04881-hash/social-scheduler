import os
from dotenv import load_dotenv
from telegram import Bot
import asyncio

async def send_message(message, bot_token=None, chat_id=None, image_path=None):
    load_dotenv(override=True)
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    cid = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not cid:
        print("Telegram Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not provided")
        return
        
    bot = Bot(token=token)

    if image_path and os.path.exists(image_path):
        print(f"Sending photo to Telegram (Chat ID: {cid})...")
        with open(image_path, 'rb') as photo_file:
            caption = message[:1024] if message else ""
            await bot.send_photo(
                chat_id=cid,
                photo=photo_file,
                caption=caption
            )
    else:
        print(f"Sending text message to Telegram (Chat ID: {cid})...")
        await bot.send_message(
            chat_id=cid,
            text=message
        )

def send_telegram_message(message, bot_token=None, chat_id=None, image_path=None):
    import threading
    exception = None
    
    def target():
        nonlocal exception
        try:
            asyncio.run(send_message(message, bot_token, chat_id, image_path))
        except Exception as e:
            exception = e
            
    thread = threading.Thread(target=target)
    thread.start()
    thread.join()
    
    if exception:
        raise exception                                                                                                                                    