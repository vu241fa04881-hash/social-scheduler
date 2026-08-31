# Content Generator Modifications Summary

## Overview
The content generator has been enhanced to accept **optional user-provided content** and generate content hashing for reference tracking. This allows users to provide their own content as a reference while the AI creates platform-specific variations.

---

## Key Changes Made

### 1. **Content Generator Module** (`app/content_generator.py`)
   
#### New Imports
- Added `import hashlib` for content hash generation

#### New Function: `generate_content_hash(user_content)`
- Generates a SHA-256 hash of user-provided content (first 16 characters)
- Returns `None` if no content is provided
- Used for reference tracking and verification
- Example: `sha256_hash → "3c5f8a2b1d9e4c"` (shortened)

#### Updated Function: `generate_post()`
**New Parameters:**
- `user_content: str = None` (optional) - User-provided content to use as reference

**Behavior Changes:**
- If user provides content:
  - Generates and logs content hash
  - Skips automatic web search (only proceeds if explicitly requested)
  - Includes user content in the AI prompt with reference hash
- If no user content:
  - Operates as before (auto-search decision, website scraping)

**Prompt Enhancement:**
- Added section: "User-Provided Content (Reference)" with content hash reference
- AI is instructed to create unique posts based on the reference

---

### 2. **Database Schema** (`scheduler/database.py`)

#### Schema Update
Added new column to `scheduled_posts` table:
```sql
user_content TEXT DEFAULT ''
```

#### Function Updates
- **`create_table()`**: Creates new column dynamically for existing databases
- **`add_post()`**: Now accepts `user_content=""` parameter and stores it
- **`get_posts()`**: Returns user_content in the result tuple (6 fields now instead of 5)

#### Backward Compatibility
- Handles both old (5-field) and new (6-field) post formats
- Automatically migrates existing databases

---

### 3. **API Endpoints** (`app_web.py`)

#### Updated Models
**ScheduleData** (POST `/api/schedule`):
```python
user_content: str = ""  # Optional user-provided content
```

**PublishNowData** (POST `/api/publish-now`):
```python
user_content: str = ""  # Optional user-provided content
```

#### Updated Routes

**1. `/api/schedule` (POST)**
- Accepts `user_content` in request body
- Passes to `add_post()` for database storage
- Passes to `add_job()` for scheduler

**2. `/api/publish-now` (POST)**
- Accepts `user_content` in request body
- Passes to `publish_post()` for generation

**3. `/api/posts` (GET)**
- Returns `user_content` field in responses
- Example response:
  ```json
  {
    "id": 1,
    "topic": "AI Revolution",
    "schedule_time": "2025-01-15 10:00",
    "website_url": "https://example.com",
    "image_path": "uploads/image.jpg",
    "user_content": "Latest AI breakthroughs..."
  }
  ```

**4. Startup Recovery (`restore_scheduled_jobs()`)**
- Updated to handle 6-field post tuples
- Restores `user_content` when re-scheduling jobs

---

### 4. **Publisher Module** (`app/publisher.py`)

#### Updated Function: `publish_post()`
**New Parameter:**
- `user_content: str = None` (optional)

**Behavior:**
- Passes `user_content` to `generate_post()`
- Enables content generation based on user reference

---

### 5. **Scheduler Module** (`scheduler/scheduler.py`)

#### Updated Function: `add_job()`
**New Parameter:**
- `user_content: str = None` (optional)

**Implementation:**
- Adds `user_content` to the job arguments passed to the scheduled function
- Ensures user content is available when job executes

---

## Usage Examples

### Example 1: Schedule Post with User Content
```bash
POST /api/schedule
{
  "topic": "AI Ethics Discussion",
  "date": "2025-01-20",
  "time": "14:30",
  "user_content": "AI companies need stricter ethical guidelines and transparency. Recent breakthroughs show both potential and risks...",
  "website_url": "",
  "image_path": "",
  "GROQ_API_KEY": "xxx"
}
```

**Result:**
- Content hash generated: `2f5e8c1a3d9b4c` (example)
- AI creates platform-specific posts based on the reference content
- User content stored in database with post entry

### Example 2: Publish Post with User Content
```bash
POST /api/publish-now
{
  "topic": "Product Launch",
  "user_content": "We're excited to announce our new feature that solves real-time data synchronization challenges...",
  "image_path": "uploads/product.jpg",
  "GROQ_API_KEY": "xxx",
  "INSTAGRAM_ACCESS_TOKEN": "xxx"
}
```

**Result:**
- AI generates unique posts for Instagram, LinkedIn, Telegram
- AI-generated image if needed
- Posts published immediately

### Example 3: Schedule Without User Content (Original Behavior)
```bash
POST /api/schedule
{
  "topic": "Climate Change News",
  "date": "2025-01-25",
  "time": "09:00",
  "GROQ_API_KEY": "xxx"
}
```

**Result:**
- Works as before
- Auto web search if needed
- No content hash generated

---

## Features

### ✅ Optional User Content
- User can provide custom content or leave blank
- Fully backward compatible with existing flows

### ✅ Content Hashing
- SHA-256 hash generation for reference tracking
- Hash included in AI prompt for context
- Useful for audit trails and content attribution

### ✅ Smart Search Behavior
- Auto web search only when NO user content provided
- Reduces unnecessary API calls when user has reference content
- Improves response times

### ✅ Database Persistence
- User content stored with scheduled posts
- Restored on server restart
- Available in GET `/api/posts` responses

### ✅ Full Integration
- Works with all platforms (Instagram, LinkedIn, Telegram)
- Compatible with image uploads
- Compatible with website URL references

---

## Data Flow Diagram

```
User Request (with optional user_content)
    ↓
API Endpoint (/api/schedule or /api/publish-now)
    ↓
add_post() [Database] + add_job() [Scheduler]
    ↓
publish_post() [Publisher]
    ↓
generate_post() [Content Generator]
    ├─ Generate content hash if user_content provided
    ├─ Skip auto-search if user_content provided
    └─ Include user_content in AI prompt
    ↓
AI Response (platform-specific posts)
    ↓
Publish to platforms (Instagram, LinkedIn, Telegram)
```

---

## Migration Guide

**For Existing Databases:**
- No manual migration needed
- `ALTER TABLE` commands run automatically on startup
- Old posts (without user_content) work seamlessly
- New field defaults to empty string

**For Clients/UI:**
- Add optional `user_content` text field to forms
- Submit empty string if user doesn't provide content
- New field appears in post list responses

---

## Testing Checklist

- [x] User can schedule posts with user content
- [x] User can publish posts immediately with user content
- [x] User content is stored in database
- [x] User content is returned in GET /api/posts
- [x] Content hash is generated correctly
- [x] Web search is skipped when user content provided
- [x] Existing posts without user content still work
- [x] Server restarts preserve user content
- [x] All platforms (Instagram, LinkedIn, Telegram) work with user content

---

## Technical Specifications

### Content Hash
- **Algorithm**: SHA-256
- **Length**: First 16 hexadecimal characters
- **Format**: Lowercase hex string
- **Example**: `3c5f8a2b1d9e4c7f`

### Database Changes
- **New Column**: `user_content` (TEXT, DEFAULT '')
- **Table**: `scheduled_posts`
- **Migration**: Automatic via ALTER TABLE

### API Compatibility
- **Backward Compatible**: Yes ✓
- **Breaking Changes**: None ✓
- **Optional Fields**: user_content (defaults to "")
