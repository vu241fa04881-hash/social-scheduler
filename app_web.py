import os
import io
import sys
import sqlite3
from datetime import datetime

# Reconfigure stdout/stderr to prevent UnicodeEncodeError with emojis on Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
except Exception:
    pass
import shutil
import uuid
from contextlib import redirect_stdout
from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from scheduler.scheduler import add_job, remove_job
from scheduler.database import create_table, add_post, get_posts, delete_post
from app.publisher import publish_post

# Initialize database table
create_table()

app = FastAPI(title="Social Scheduler API")

# Ensure .env exists
if not os.path.exists(".env"):
    with open(".env", "w") as f:
        f.write("")

# Helper to read environment variables from .env
def read_env_file():
    env_vars = {
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_CHAT_ID": "",
        "INSTAGRAM_BUSINESS_ACCOUNT_ID": "",
        "INSTAGRAM_ACCESS_TOKEN": "",
        "LINKEDIN_ACCESS_TOKEN": "",
        "LINKEDIN_PERSON_URN": "",
        "GROQ_API_KEY": "",
        "POLLINATIONS_API_KEY": ""
    }
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    if key in env_vars:
                        env_vars[key] = val
    return env_vars

# Helper to write environment variables to .env
def write_env_file(env_vars):
    with open(".env", "w", encoding="utf-8") as f:
        for key, val in env_vars.items():
            f.write(f'{key}="{val}"\n')
    # Force reload variables into current process environment
    load_dotenv(override=True)

# Restore scheduled jobs on startup
def restore_scheduled_jobs():
    posts = get_posts()
    now = datetime.now()
    count = 0
    for post in posts:
        try:
            if len(post) == 5:
                post_id, topic, schedule_time_str, website_url, image_path = post
            else:
                post_id, topic, schedule_time_str = post
                website_url, image_path = "", ""
            
            run_time = datetime.strptime(schedule_time_str, "%Y-%m-%d %H:%M")
            if run_time > now:
                # Credentials are not stored on disk; restored jobs run with empty credentials (fallback to environment variables)
                creds = {}
                # Add to scheduler with the matching post_id key
                add_job(run_time, publish_post, topic, job_id=f"job_{post_id}", creds=creds, website_url=website_url, image_path=image_path)
                count += 1
        except Exception as e:
            print(f"Failed to restore job: {e}")
    print(f"[*] Restored {count} scheduled posts into APScheduler. Note: credentials were not stored and must be supplied from environment or memory.")

@app.on_event("startup")
def startup_event():
    restore_scheduled_jobs()
    print("\n" + "═" * 60)
    print("  [*] Social Scheduler Web Dashboard is running!")
    print("═" * 60 + "\n")
    if os.environ.get("RENDER"):
        print("  Running in Render cloud environment. Skipping browser launch.")
        return

    import webbrowser
    try:
        # Try to locate and open in Chrome explicitly on Windows
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe"
        ]
        chrome_path = None
        for path in chrome_paths:
            expanded = os.path.expandvars(path)
            if os.path.exists(expanded):
                chrome_path = expanded
                break
        
        if chrome_path:
            webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
            webbrowser.get('chrome').open("http://localhost:8000")
        else:
            webbrowser.open("http://localhost:8000")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

# Pydantic models for API
class ConfigData(BaseModel):
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str
    INSTAGRAM_ACCESS_TOKEN: str
    LINKEDIN_ACCESS_TOKEN: str
    LINKEDIN_PERSON_URN: str
    GROQ_API_KEY: str
    POLLINATIONS_API_KEY: str

class ScheduleData(BaseModel):
    topic: str
    date: str
    time: str
    website_url: str = ""
    image_path: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    INSTAGRAM_ACCESS_TOKEN: str = ""
    LINKEDIN_ACCESS_TOKEN: str = ""
    LINKEDIN_PERSON_URN: str = ""
    GROQ_API_KEY: str = ""
    POLLINATIONS_API_KEY: str = ""

class PublishNowData(BaseModel):
    topic: str
    website_url: str = ""
    image_path: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    INSTAGRAM_ACCESS_TOKEN: str = ""
    LINKEDIN_ACCESS_TOKEN: str = ""
    LINKEDIN_PERSON_URN: str = ""
    GROQ_API_KEY: str = ""
    POLLINATIONS_API_KEY: str = ""

# Routes
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Dashboard template not found.")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/config")
async def get_config():
    # Credentials are saved client-side in localStorage, so return empty strings
    return {
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_CHAT_ID": "",
        "INSTAGRAM_BUSINESS_ACCOUNT_ID": "",
        "INSTAGRAM_ACCESS_TOKEN": "",
        "LINKEDIN_ACCESS_TOKEN": "",
        "LINKEDIN_PERSON_URN": "",
        "GROQ_API_KEY": "",
        "POLLINATIONS_API_KEY": ""
    }

@app.post("/api/config")
async def save_config():
    # Stub endpoint, credentials are now managed client-side
    return {"status": "success", "message": "Saved locally in browser."}

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        os.makedirs("uploads", exist_ok=True)
        file_extension = os.path.splitext(file.filename)[1]
        if not file_extension:
            file_extension = ".jpg"
        filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join("uploads", filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"status": "success", "image_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

@app.get("/api/posts")
async def list_posts():
    try:
        posts = get_posts()
        formatted_posts = []
        for post in posts:
            if len(post) == 5:
                post_id, topic, schedule_time, website_url, image_path = post
            else:
                post_id, topic, schedule_time = post
                website_url, image_path = "", ""
            formatted_posts.append({
                "id": post_id,
                "topic": topic,
                "schedule_time": schedule_time,
                "website_url": website_url,
                "image_path": image_path
            })
        return formatted_posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedule")
async def schedule_new_post(data: ScheduleData):
    if not data.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required.")
    
    try:
        run_time = datetime.strptime(f"{data.date} {data.time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format. Use YYYY-MM-DD and HH:MM.")
    
    if run_time < datetime.now():
         raise HTTPException(status_code=400, detail="Scheduled time must be in the future.")

    creds = {
        "TELEGRAM_BOT_TOKEN": data.TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": data.TELEGRAM_CHAT_ID,
        "INSTAGRAM_BUSINESS_ACCOUNT_ID": data.INSTAGRAM_BUSINESS_ACCOUNT_ID,
        "INSTAGRAM_ACCESS_TOKEN": data.INSTAGRAM_ACCESS_TOKEN,
        "LINKEDIN_ACCESS_TOKEN": data.LINKEDIN_ACCESS_TOKEN,
        "LINKEDIN_PERSON_URN": data.LINKEDIN_PERSON_URN,
        "GROQ_API_KEY": data.GROQ_API_KEY,
        "POLLINATIONS_API_KEY": data.POLLINATIONS_API_KEY
    }

    try:
        # 1. Save to SQLite database (without storing credentials) and get the row ID
        post_id = add_post(
            data.topic, 
            run_time.strftime("%Y-%m-%d %H:%M"),
            website_url=data.website_url,
            image_path=data.image_path
        )
        
        # 2. Add job to scheduler using the unique row ID and custom credentials (stored in-memory in scheduler)
        add_job(
            run_time, 
            publish_post, 
            data.topic, 
            job_id=f"job_{post_id}", 
            creds=creds,
            website_url=data.website_url,
            image_path=data.image_path
        )
        
        return {"status": "success", "message": f"Post scheduled successfully for {run_time}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/posts/{post_id}")
async def delete_scheduled_post(post_id: int):
    try:
        # Delete from database
        delete_post(post_id)
        # Remove from scheduler queue
        remove_job(f"job_{post_id}")
        return {"status": "success", "message": "Scheduled post deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/publish-now")
async def publish_immediately(data: PublishNowData):
    if not data.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required.")
    
    creds = {
        "TELEGRAM_BOT_TOKEN": data.TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": data.TELEGRAM_CHAT_ID,
        "INSTAGRAM_BUSINESS_ACCOUNT_ID": data.INSTAGRAM_BUSINESS_ACCOUNT_ID,
        "INSTAGRAM_ACCESS_TOKEN": data.INSTAGRAM_ACCESS_TOKEN,
        "LINKEDIN_ACCESS_TOKEN": data.LINKEDIN_ACCESS_TOKEN,
        "LINKEDIN_PERSON_URN": data.LINKEDIN_PERSON_URN,
        "GROQ_API_KEY": data.GROQ_API_KEY,
        "POLLINATIONS_API_KEY": data.POLLINATIONS_API_KEY
    }

    # Capture stdout logs to display to user
    log_stream = io.StringIO()
    try:
        with redirect_stdout(log_stream):
            results = publish_post(
                data.topic, 
                creds=creds,
                website_url=data.website_url,
                image_path=data.image_path
            )
        logs = log_stream.getvalue()
        failed = [platform for platform, success in results.items() if success is False]
        if failed:
            return {
                "status": "partial",
                "message": f"Publishing incomplete. Failed: {', '.join(failed)}",
                "results": results,
                "logs": logs
            }
        return {
            "status": "success",
            "message": "Post generated and published successfully!",
            "results": results,
            "logs": logs
        }
    except Exception as e:
        logs = log_stream.getvalue()
        error_msg = f"{str(e)}\n\nLogs leading up to error:\n{logs}"
        raise HTTPException(status_code=500, detail=error_msg)
