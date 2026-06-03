import os
import sqlite3

DB_PATH = os.environ.get("DATABASE_PATH", "data/scheduled_posts.db")


def create_table():
    import os
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scheduled_posts'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Check if the telegram_bot_token column exists
        cursor.execute("PRAGMA table_info(scheduled_posts)")
        columns = [col[1] for col in cursor.fetchall()]
        if "telegram_bot_token" in columns:
            print("Old scheduled_posts table structure containing credentials detected. Migrating to clean schema...")
            cursor.execute("DROP TABLE scheduled_posts")
            table_exists = False
        else:
            # Check for website_url and image_path and add them dynamically
            if "website_url" not in columns:
                cursor.execute("ALTER TABLE scheduled_posts ADD COLUMN website_url TEXT DEFAULT ''")
            if "image_path" not in columns:
                cursor.execute("ALTER TABLE scheduled_posts ADD COLUMN image_path TEXT DEFAULT ''")
            
    if not table_exists:
        cursor.execute("""
        CREATE TABLE scheduled_posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            schedule_time TEXT NOT NULL,
            website_url TEXT DEFAULT '',
            image_path TEXT DEFAULT ''
        )
        """)
        
    conn.commit()
    conn.close()


def add_post(topic, schedule_time, website_url="", image_path=""):
    
    conn = sqlite3.connect(DB_PATH)
    
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO scheduled_posts (topic, schedule_time, website_url, image_path)
    VALUES (?, ?, ?, ?)
    """, (topic, schedule_time, website_url, image_path))

    post_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return post_id


def get_posts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, topic, schedule_time, website_url, image_path
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