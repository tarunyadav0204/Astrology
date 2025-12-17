#!/usr/bin/env python3
"""
Migration script to fix birth_charts table UNIQUE constraint
This prevents cross-user data corruption by ensuring charts are unique per user.
"""

import sqlite3
import sys
import os

def migrate_birth_charts():
    """Migrate birth_charts table to fix UNIQUE constraint"""
    
    db_path = 'astrology.db'
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current table schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='birth_charts'")
        result = cursor.fetchone()
        
        if not result:
            print("birth_charts table not found!")
            return False
        
        current_schema = result[0]
        print(f"Current schema: {current_schema}")
        
        # Check if migration is needed
        if 'UNIQUE(userid, name, date, time, latitude, longitude)' in current_schema:
            print("✅ Table already has correct UNIQUE constraint")
            return True
        
        if 'UNIQUE(userid, date, time, latitude, longitude)' not in current_schema:
            print("⚠️  Table doesn't have the problematic constraint, skipping migration")
            return True
        
        print("🔄 Starting migration...")
        
        # Clean up any existing temporary tables
        cursor.execute("DROP TABLE IF EXISTS birth_charts_backup")
        cursor.execute("DROP TABLE IF EXISTS birth_charts_new")
        
        # Backup original table
        cursor.execute("CREATE TABLE birth_charts_backup AS SELECT * FROM birth_charts")
        print("✅ Created backup table")
        
        # Get column info from existing table
        cursor.execute("PRAGMA table_info(birth_charts)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Found columns: {column_names}")
        
        # Create new table with all existing columns plus correct constraint
        cursor.execute('''
            CREATE TABLE birth_charts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timezone TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                place TEXT DEFAULT '',
                gender TEXT DEFAULT '',
                relation TEXT DEFAULT 'other',
                is_rectified INTEGER DEFAULT 0,
                calibration_year INTEGER,
                FOREIGN KEY (userid) REFERENCES users (userid),
                UNIQUE(userid, name, date, time, latitude, longitude)
            )
        ''')
        print("✅ Created new table with correct constraint")
        
        # Copy data from old table
        column_list = ', '.join(column_names)
        cursor.execute(f'''
            INSERT INTO birth_charts_new ({column_list})
            SELECT {column_list} FROM birth_charts
        ''')
        print("✅ Copied data to new table")
        
        # Drop old table and rename new one
        cursor.execute('DROP TABLE birth_charts')
        cursor.execute('ALTER TABLE birth_charts_new RENAME TO birth_charts')
        print("✅ Replaced old table with new one")
        
        conn.commit()
        conn.close()
        
        print("🎉 Migration completed successfully!")
        print("📝 Backup table 'birth_charts_backup' created for safety")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

def cleanup_backup():
    """Remove backup table after confirming migration worked"""
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS birth_charts_backup')
        conn.commit()
        conn.close()
        print("✅ Backup table removed")
    except Exception as e:
        print(f"⚠️  Could not remove backup: {str(e)}")

if __name__ == "__main__":
    print("🔧 Birth Charts Migration Script")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        cleanup_backup()
        sys.exit(0)
    
    success = migrate_birth_charts()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("💡 Run with --cleanup flag to remove backup table")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)