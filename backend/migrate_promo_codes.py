#!/usr/bin/env python3
"""
Migration script to update promo codes schema to support max_uses_per_user
and remove the unique constraint from promo_code_usage table.
"""

import sqlite3

def migrate_database(db_path='astrology.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        conn.execute('BEGIN IMMEDIATE')
        
        # Add max_uses_per_user column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE promo_codes ADD COLUMN max_uses_per_user INTEGER DEFAULT 1")
            print("Added max_uses_per_user column")
        except sqlite3.OperationalError:
            print("max_uses_per_user column already exists")
        
        # Recreate promo_code_usage table without unique constraint
        print("Recreating promo_code_usage table without unique constraint...")
        
        # Backup existing data
        cursor.execute("""
            CREATE TEMPORARY TABLE promo_code_usage_backup AS 
            SELECT * FROM promo_code_usage
        """)
        
        # Drop and recreate table
        cursor.execute("DROP TABLE promo_code_usage")
        cursor.execute('''
            CREATE TABLE promo_code_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                promo_code_id INTEGER NOT NULL,
                userid INTEGER NOT NULL,
                credits_earned INTEGER NOT NULL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (promo_code_id) REFERENCES promo_codes (id),
                FOREIGN KEY (userid) REFERENCES users (userid)
            )
        ''')
        
        # Restore data
        cursor.execute("""
            INSERT INTO promo_code_usage (id, promo_code_id, userid, credits_earned, used_at)
            SELECT id, promo_code_id, userid, credits_earned, used_at 
            FROM promo_code_usage_backup
        """)
        
        cursor.execute("DROP TABLE promo_code_usage_backup")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    migrate_database()