"""
Migration: Create chat_error_logs table
Run once: python migrate_chat_error_logs.py
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            phone TEXT,
            error_type TEXT,
            error_message TEXT,
            user_question TEXT,
            stack_trace TEXT,
            platform TEXT,
            error_source TEXT DEFAULT 'backend',
            birth_data_context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ chat_error_logs table created")

if __name__ == "__main__":
    migrate()
