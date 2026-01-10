"""
Database migration: Create karma_insights table
"""
import sqlite3

conn = sqlite3.connect('astrology.db')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS karma_insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chart_id TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT DEFAULT 'processing',
        karma_context TEXT,
        ai_interpretation TEXT,
        sections TEXT,
        error TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(chart_id, user_id)
    )
""")

conn.commit()
conn.close()

print("✅ karma_insights table created")
