#!/usr/bin/env python3
"""
Migration: Create prompt configuration tables for dynamic instruction management
Run: python migrations/create_prompt_config_tables.py
"""

import sqlite3
import os

def create_tables():
    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'astrology.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating prompt configuration tables...")
    
    # 1. Instruction modules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_instruction_modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_key TEXT UNIQUE NOT NULL,
            module_name TEXT NOT NULL,
            instruction_text TEXT NOT NULL,
            character_count INTEGER,
            is_active BOOLEAN DEFAULT 1,
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created prompt_instruction_modules table")
    
    # 2. Category configuration table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_category_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_key TEXT NOT NULL,
            tier_key TEXT NOT NULL DEFAULT 'normal',
            category_name TEXT NOT NULL,
            required_modules TEXT NOT NULL,
            required_data_fields TEXT NOT NULL,
            optional_data_fields TEXT,
            max_transit_activations INTEGER DEFAULT 20,
            is_active BOOLEAN DEFAULT 1,
            tier_context_config TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category_key, tier_key)
        )
    ''')
    print("✅ Created prompt_category_config table")
    
    # 3. Performance tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_performance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_key TEXT,
            instruction_size INTEGER,
            context_size INTEGER,
            total_prompt_size INTEGER,
            response_time_seconds REAL,
            success BOOLEAN,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created prompt_performance_log table")
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_module_key ON prompt_instruction_modules(module_key)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_category_key ON prompt_category_config(category_key)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_category ON prompt_performance_log(category_key)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_created ON prompt_performance_log(created_at)')
    print("✅ Created indexes")
    
    conn.commit()
    conn.close()
    
    print("\n✅ All tables created successfully!")
    print("\nNext steps:")
    print("1. Run: python migrations/seed_prompt_config.py")
    print("2. Access admin UI to manage configurations")

if __name__ == '__main__':
    create_tables()
