import sqlite3

def create_missing_tier_rows():
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Get all normal configs
    cursor.execute('''
        SELECT category_key, category_name, required_modules, required_data_fields, 
               optional_data_fields, max_transit_activations, is_active, tier_context_config
        FROM prompt_category_config WHERE tier_key = 'normal'
    ''')
    
    for row in cursor.fetchall():
        cat_key, cat_name, req_mod, req_fields, opt_fields, max_trans, active, tier_ctx = row
        
        # Check if premium exists
        cursor.execute('SELECT COUNT(*) FROM prompt_category_config WHERE category_key = ? AND tier_key = "premium"', (cat_key,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO prompt_category_config 
                (category_key, tier_key, category_name, required_modules, required_data_fields, 
                 optional_data_fields, max_transit_activations, is_active, tier_context_config)
                VALUES (?, 'premium', ?, ?, ?, ?, ?, ?, ?)
            ''', (cat_key, cat_name, req_mod, req_fields, opt_fields, max_trans, active, tier_ctx))
            print(f"✓ Created premium for {cat_key}")
        
        # Check if light exists
        cursor.execute('SELECT COUNT(*) FROM prompt_category_config WHERE category_key = ? AND tier_key = "light"', (cat_key,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO prompt_category_config 
                (category_key, tier_key, category_name, required_modules, required_data_fields, 
                 optional_data_fields, max_transit_activations, is_active, tier_context_config)
                VALUES (?, 'light', ?, ?, ?, ?, ?, ?, ?)
            ''', (cat_key, cat_name, req_mod, req_fields, opt_fields, max_trans, active, tier_ctx))
            print(f"✓ Created light for {cat_key}")
    
    conn.commit()
    conn.close()
    print("\n✅ All tier rows created")

if __name__ == '__main__':
    create_missing_tier_rows()
