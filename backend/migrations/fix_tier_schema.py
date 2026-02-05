import sqlite3

def fix_tier_schema():
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Create new table with correct schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_category_config_new (
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
    
    # Copy existing data
    cursor.execute('''
        INSERT INTO prompt_category_config_new 
        SELECT * FROM prompt_category_config
    ''')
    
    # Get all normal tier configs to duplicate
    cursor.execute('SELECT * FROM prompt_category_config WHERE tier_key = "normal"')
    normal_configs = cursor.fetchall()
    
    for row in normal_configs:
        id, cat_key, cat_name, req_mod, req_fields, opt_fields, max_trans, active, created, updated, tier_key, tier_ctx = row
        
        # Insert premium
        cursor.execute('''
            INSERT OR IGNORE INTO prompt_category_config_new 
            (category_key, tier_key, category_name, required_modules, required_data_fields, 
             optional_data_fields, max_transit_activations, is_active, tier_context_config)
            VALUES (?, 'premium', ?, ?, ?, ?, ?, ?, ?)
        ''', (cat_key, cat_name, req_mod, req_fields, opt_fields, max_trans, active, tier_ctx))
        
        # Insert light
        cursor.execute('''
            INSERT OR IGNORE INTO prompt_category_config_new 
            (category_key, tier_key, category_name, required_modules, required_data_fields, 
             optional_data_fields, max_transit_activations, is_active, tier_context_config)
            VALUES (?, 'light', ?, ?, ?, ?, ?, ?, ?)
        ''', (cat_key, cat_name, req_mod, req_fields, opt_fields, max_trans, active, tier_ctx))
    
    # Drop old table and rename new one
    cursor.execute('DROP TABLE prompt_category_config')
    cursor.execute('ALTER TABLE prompt_category_config_new RENAME TO prompt_category_config')
    
    conn.commit()
    conn.close()
    print("✅ Schema fixed and all tier configs created")

if __name__ == '__main__':
    fix_tier_schema()
