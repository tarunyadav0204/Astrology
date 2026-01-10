"""
Migration: Add karma_analysis_cost to credit_settings
"""

import sqlite3
import os

def migrate():
    db_path = os.getenv('DATABASE_PATH', 'astrology.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if karma_analysis_cost already exists
    cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'karma_analysis_cost'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO credit_settings (setting_key, setting_value, description)
            VALUES ('karma_analysis_cost', 25, 'Credits per karma analysis')
        ''')
        print("✅ Added karma_analysis_cost setting (25 credits)")
    else:
        print("ℹ️  karma_analysis_cost setting already exists")
    
    conn.commit()
    conn.close()
    print("✅ Migration completed")

if __name__ == "__main__":
    migrate()
