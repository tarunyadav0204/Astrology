import sqlite3

def create_tier_system():
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Create prompt_tiers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_tiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tier_key TEXT UNIQUE NOT NULL,
            tier_name TEXT NOT NULL,
            description TEXT,
            max_instruction_size INTEGER,
            max_context_size INTEGER,
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add tier_key column to prompt_category_config
    cursor.execute('''
        ALTER TABLE prompt_category_config ADD COLUMN tier_key TEXT DEFAULT 'normal'
    ''')
    
    # Add tier_context_config column for context data filtering
    cursor.execute('''
        ALTER TABLE prompt_category_config ADD COLUMN tier_context_config TEXT DEFAULT '{}'
    ''')
    
    # Seed tier data
    tiers = [
        ('premium', 'Premium', 'Full instructions and complete context data', 200000, 300000, 3),
        ('normal', 'Normal', 'Standard instructions and essential context data', 100000, 150000, 2),
        ('light', 'Light', 'Minimal instructions and basic context data', 50000, 75000, 1)
    ]
    
    cursor.executemany('''
        INSERT INTO prompt_tiers (tier_key, tier_name, description, max_instruction_size, max_context_size, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', tiers)
    
    # Create default tier configurations for each category
    cursor.execute('SELECT DISTINCT category_key FROM prompt_category_config WHERE tier_key IS NULL')
    categories = cursor.fetchall()
    
    for (category_key,) in categories:
        # Get the existing config
        cursor.execute('''
            SELECT required_modules, enabled FROM prompt_category_config 
            WHERE category_key = ? AND tier_key IS NULL
        ''', (category_key,))
        result = cursor.fetchone()
        
        if result:
            required_modules, enabled = result
            
            # Create premium tier (all modules, all context)
            cursor.execute('''
                INSERT INTO prompt_category_config (category_key, tier_key, required_modules, enabled, tier_context_config)
                VALUES (?, 'premium', ?, ?, ?)
            ''', (category_key, required_modules, enabled, '{"layers": "all", "charts": "all", "transits": true}'))
            
            # Create normal tier (essential modules, essential context)
            cursor.execute('''
                INSERT INTO prompt_category_config (category_key, tier_key, required_modules, enabled, tier_context_config)
                VALUES (?, 'normal', ?, ?, ?)
            ''', (category_key, required_modules, enabled, '{"layers": ["basic", "houses", "planets"], "charts": ["D1", "D9"], "transits": false}'))
            
            # Create light tier (minimal modules, minimal context)
            cursor.execute('''
                INSERT INTO prompt_category_config (category_key, tier_key, required_modules, enabled, tier_context_config)
                VALUES (?, 'light', ?, ?, ?)
            ''', (category_key, '["core_identity", "response_format"]', enabled, '{"layers": ["basic"], "charts": ["D1"], "transits": false}'))
            
            # Delete the old config without tier_key
            cursor.execute('DELETE FROM prompt_category_config WHERE category_key = ? AND tier_key IS NULL', (category_key,))
    
    conn.commit()
    conn.close()
    print("✅ Tier system created successfully")

if __name__ == '__main__':
    create_tier_system()
