# Social Media Scheduler Dashboard

A modern, deployable FastAPI web application designed to automatically draft platform-specific content, generate dynamic visual assets, and coordinate delivery across **Telegram**, **Instagram**, and **LinkedIn**.

This dashboard features a premium glassmorphic dark-theme UI and implements a decentralized client-side credentials architecture, allowing anyone to access the deployment and publish posts to their respective social accounts securely.

---

## Key Features

1. **Decentralized Credentials Security**: 
   * Form inputs start completely blank. 
   * Credentials (API keys, usernames, tokens, and passwords) are saved locally in the browser's `localStorage` (not exposed to the server or shared with other users).
   * Credentials are sent in the payload of each individual post dispatch request.
2. **JPEG Transcoding via Pillow**:
   * Uses PIL to convert visual assets downloaded from the Pollinations AI generator into compliant RGB JPEGs, resolving Instagram media-upload errors.
3. **Queue Database & APScheduler Recovery**:
   * Saves topics, run-times, and credentials in SQLite.
   * Auto-restores and re-queues pending posts into APScheduler background queues upon server startup, ensuring no schedules are lost.
4. **Platform Integrations**:
   * **Telegram**: Direct message delivery via HTTP Bot API wrapped in an isolated thread context.
   * **Instagram**: Session-isolated photo uploads via the private `instagrapi` wrapper.
   * **LinkedIn**: Professional ugcPosts sharing via the LinkedIn partner API.
   * **Groq AI (Llama 3.3)**: Generates optimized platform captions and graphic prompts.

---

## Getting Started

### Prerequisites

* Python 3.12+
* Installed packages (inside `venv`): `fastapi`, `uvicorn`, `APScheduler`, `instagrapi`, `requests`, `python-dotenv`, `python-telegram-bot`, `groq`, `pillow`.

### Running Locally

1. Open your terminal in the project directory.
2. Activate your virtual environment and run the main entrypoint:
   ```bash
   # Windows PowerShell
   .\venv\Scripts\python.exe main.py
   ```
3. Open your browser and navigate to:
   **[http://localhost:8000](http://localhost:8000)**

---

## Pushing to GitHub

To publish this project to your own GitHub account:

1. **Initialize the local Git repository**:
   ```bash
   git init
   ```
2. **Add all files to staging**:
   ```bash
   git add .
   ```
3. **Create the initial commit**:
   ```bash
   git commit -m "Initial commit"
   ```
4. **Rename the default branch** (optional):
   ```bash
   git branch -M main
   ```
5. **Add your GitHub remote repository** (replace with your repo URL):
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
   ```
6. **Push to GitHub**:
   ```bash
   git push -u origin main
   ```
