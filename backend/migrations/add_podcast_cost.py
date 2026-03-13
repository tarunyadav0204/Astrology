"""
Migration: Add podcast_cost to credit_settings so it appears in Admin Feature Costs.
"""

import sqlite3
import os

def migrate():
    db_path = os.getenv('DATABASE_PATH', 'astrology.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'podcast_cost'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO credit_settings (setting_key, setting_value, description)
            VALUES ('podcast_cost', 2, 'Credits per podcast (listen to message as audio)')
        ''')
        conn.commit()
        print("✅ Added podcast_cost setting (2 credits)")
    else:
        print("ℹ️  podcast_cost setting already exists")
    
    conn.close()
    print("✅ Migration completed")

if __name__ == "__main__":
    migrate()
