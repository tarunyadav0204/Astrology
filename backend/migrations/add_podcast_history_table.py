"""
Migration: Create podcast_history table to record each generated/cached podcast per user.
Used by GET /tts/podcast/history and GET /tts/podcast/stream.
"""

import sqlite3
import os


def migrate():
    db_path = os.getenv("DATABASE_PATH", "astrology.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS podcast_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid INTEGER NOT NULL,
            message_id TEXT NOT NULL,
            session_id TEXT,
            lang TEXT NOT NULL DEFAULT 'en',
            preview TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(userid, message_id, lang)
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_podcast_history_userid ON podcast_history(userid)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_podcast_history_created_at ON podcast_history(created_at DESC)"
    )
    conn.commit()
    conn.close()
    print("✅ podcast_history table ready")


if __name__ == "__main__":
    migrate()
