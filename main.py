import sys
import uvicorn
from app_web import app

# Reconfigure stdout/stderr to prevent UnicodeEncodeError with emojis on Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
except Exception:
    pass

# Export for Firebase Cloud Functions (v2)
try:
    from firebase_functions import https_fn
    @https_fn.on_request()
    def api(req: https_fn.Request) -> https_fn.Response:
        return https_fn.Response("Social Scheduler Backend API")
except Exception:
    pass
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    print(f"Launching Social Scheduler Web Dashboard on http://localhost:{port}")
    uvicorn.run("app_web:app", host="0.0.0.0", port=port, reload=False, access_log=False)