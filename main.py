import sys
import uvicorn

# Reconfigure stdout/stderr to utf-8 to prevent UnicodeEncodeError with emojis on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from app_web import app

if __name__ == "__main__":
    print("Launching Social Scheduler Web Dashboard on http://localhost:8000")
    uvicorn.run("app_web:app", host="0.0.0.0", port=8000, reload=False)