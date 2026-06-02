import sqlite3

DB_PATH = "data/scheduled_posts.db"


def create_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scheduled_posts'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Check if the telegram_bot_token column exists
        cursor.execute("PRAGMA table_info(scheduled_posts)")
        columns = [col[1] for col in cursor.fetchall()]
        if "telegram_bot_token" not in columns:
            print("Old scheduled_posts table structure detected. Migrating to new multi-tenant structure...")
            cursor.execute("DROP TABLE scheduled_posts")
            table_exists = False
            
    if not table_exists:
        cursor.execute("""
        CREATE TABLE scheduled_posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            schedule_time TEXT NOT NULL,
            telegram_bot_token TEXT,
            telegram_chat_id TEXT,
            instagram_username TEXT,
            instagram_password TEXT,
            linkedin_access_token TEXT,
            linkedin_person_urn TEXT,
            groq_api_key TEXT
        )
        """)
        
    conn.commit()
    conn.close()


def add_post(topic, schedule_time, creds=None):
    if creds is None:
        creds = {}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO scheduled_posts
    (topic, schedule_time, telegram_bot_token, telegram_chat_id, instagram_username, instagram_password, linkedin_access_token, linkedin_person_urn, groq_api_key)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        topic,
        schedule_time,
        creds.get("TELEGRAM_BOT_TOKEN", ""),
        creds.get("TELEGRAM_CHAT_ID", ""),
        creds.get("INSTAGRAM_USERNAME", ""),
        creds.get("INSTAGRAM_PASSWORD", ""),
        creds.get("LINKEDIN_ACCESS_TOKEN", ""),
        creds.get("LINKEDIN_PERSON_URN", ""),
        creds.get("GROQ_API_KEY", "")
    ))

    post_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return post_id


def get_posts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, topic, schedule_time, telegram_bot_token, telegram_chat_id, instagram_username, instagram_password, linkedin_access_token, linkedin_person_urn, groq_api_key
    FROM scheduled_posts
    """)

    posts = cursor.fetchall()
    conn.close()
    return posts


def delete_post(post_id):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM scheduled_posts WHERE id=?",
        (post_id,)
    )

    conn.commit()
    conn.close()