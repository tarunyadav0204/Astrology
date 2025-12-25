#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime

def get_schema_and_messages():
    try:
        # Connect to the database
        conn = sqlite3.connect('/Users/tarunydv/Desktop/Code/AstrologyApp/backend/astrology.db')
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(chat_messages)")
        schema = cursor.fetchall()
        
        print("Chat messages table schema:")
        print("=" * 50)
        for col in schema:
            print(f"{col[1]} ({col[2]}) - PK: {col[5]}")
        
        print("\n" + "=" * 50)
        
        # Get last 5 chat messages with actual column names
        cursor.execute("SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 5")
        messages = cursor.fetchall()
        
        print("Last 5 chat messages:")
        print("=" * 80)
        
        for msg in messages:
            print(f"Message: {msg}")
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_schema_and_messages()