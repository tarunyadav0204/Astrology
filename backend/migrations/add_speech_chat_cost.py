"""
Migration: Add speech_chat_cost to credit_settings (Admin Feature Costs + speech/Tara billing).
"""

import os
import sqlite3


def migrate():
    db_path = os.getenv("DATABASE_PATH", "astrology.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'speech_chat_cost'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO credit_settings (setting_key, setting_value, description)
            VALUES ('speech_chat_cost', 1, 'Credits per speech chat turn (Tara / voice-first)')
            """
        )
        conn.commit()
        print("✅ Added speech_chat_cost setting (1 credit default)")
    else:
        print("ℹ️  speech_chat_cost setting already exists")

    conn.close()
    print("✅ Migration completed")


if __name__ == "__main__":
    migrate()
