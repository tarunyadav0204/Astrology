#!/usr/bin/env python3
"""
Database migration script for chat polling architecture
Run this once to add status columns to existing chat_messages table
"""

import sqlite3
from datetime import datetime

def migrate_chat_database():
    """Add polling support columns to chat_messages table"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    print("🔄 Migrating chat database for polling architecture...")
    
    # Add status columns if they don't exist
    columns_to_add = [
        ('status', 'TEXT DEFAULT "completed"'),
        ('started_at', 'TIMESTAMP'),
        ('completed_at', 'TIMESTAMP'),
        ('error_message', 'TEXT')
    ]
    
    for column_name, column_def in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE chat_messages ADD COLUMN {column_name} {column_def}')
            print(f"✅ Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"⚠️ Column {column_name} already exists")
            else:
                print(f"❌ Error adding {column_name}: {e}")
    
    # Update existing completed messages
    cursor.execute("""
        UPDATE chat_messages 
        SET status = 'completed', completed_at = timestamp 
        WHERE status IS NULL OR status = ''
    """)
    
    updated_rows = cursor.rowcount
    print(f"✅ Updated {updated_rows} existing messages to 'completed' status")
    
    # Add index for status column
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_status ON chat_messages (status)')
        print("✅ Added status index")
    except sqlite3.OperationalError as e:
        print(f"⚠️ Index creation: {e}")
    
    conn.commit()
    conn.close()
    
    print("🎉 Migration completed successfully!")
    print("\n📋 New API endpoints available:")
    print("   POST /chat/ask - Start async chat processing")
    print("   GET /chat/status/{message_id} - Poll message status")

if __name__ == "__main__":
    migrate_chat_database()