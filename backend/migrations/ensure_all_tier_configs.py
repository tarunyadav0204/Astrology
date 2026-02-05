import sqlite3
import json

def ensure_all_tier_configs():
    """Ensure premium and light tier configs exist, copying from normal"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Get all normal tier configs
    cursor.execute('''
        SELECT category_key, category_name, required_modules, required_data_fields, 
               optional_data_fields, max_transit_activations, is_active, tier_context_config
        FROM prompt_category_config
        WHERE tier_key = 'normal'
    ''')
    
    normal_configs = cursor.fetchall()
    
    for config in normal_configs:
        category_key, category_name, req_modules, req_fields, opt_fields, max_transit, is_active, tier_context = config
        
        # Insert premium tier (if not exists)
        cursor.execute('''
            INSERT OR IGNORE INTO prompt_category_config 
            (category_key, tier_key, category_name, required_modules, required_data_fields, 
             optional_data_fields, max_transit_activations, is_active, tier_context_config)
            VALUES (?, 'premium', ?, ?, ?, ?, ?, ?, ?)
        ''', (category_key, category_name, req_modules, req_fields, opt_fields, max_transit, is_active, tier_context))
        
        # Insert light tier (if not exists)
        cursor.execute('''
            INSERT OR IGNORE INTO prompt_category_config 
            (category_key, tier_key, category_name, required_modules, required_data_fields, 
             optional_data_fields, max_transit_activations, is_active, tier_context_config)
            VALUES (?, 'light', ?, ?, ?, ?, ?, ?, ?)
        ''', (category_key, category_name, req_modules, req_fields, opt_fields, max_transit, is_active, tier_context))
        
        print(f"✓ Created premium/light configs for {category_key}")
    
    # Sync layer requirements
    cursor.execute('SELECT DISTINCT category_key FROM category_layer_requirements WHERE tier_key = "normal"')
    categories = [row[0] for row in cursor.fetchall()]
    
    for category_key in categories:
        cursor.execute('''
            SELECT layer_id, is_required FROM category_layer_requirements
            WHERE category_key = ? AND tier_key = 'normal'
        ''', (category_key,))
        
        for layer_id, is_required in cursor.fetchall():
            cursor.execute('''
                INSERT OR IGNORE INTO category_layer_requirements (category_key, tier_key, layer_id, is_required)
                VALUES (?, 'premium', ?, ?)
            ''', (category_key, layer_id, is_required))
            
            cursor.execute('''
                INSERT OR IGNORE INTO category_layer_requirements (category_key, tier_key, layer_id, is_required)
                VALUES (?, 'light', ?, ?)
            ''', (category_key, layer_id, is_required))
    
    # Sync chart requirements
    cursor.execute('SELECT DISTINCT category_key FROM category_divisional_requirements WHERE tier_key = "normal"')
    categories = [row[0] for row in cursor.fetchall()]
    
    for category_key in categories:
        cursor.execute('''
            SELECT chart_id, is_required FROM category_divisional_requirements
            WHERE category_key = ? AND tier_key = 'normal'
        ''', (category_key,))
        
        for chart_id, is_required in cursor.fetchall():
            cursor.execute('''
                INSERT OR IGNORE INTO category_divisional_requirements (category_key, tier_key, chart_id, is_required)
                VALUES (?, 'premium', ?, ?)
            ''', (category_key, chart_id, is_required))
            
            cursor.execute('''
                INSERT OR IGNORE INTO category_divisional_requirements (category_key, tier_key, chart_id, is_required)
                VALUES (?, 'light', ?, ?)
            ''', (category_key, chart_id, is_required))
    
    # Sync transit limits
    cursor.execute('SELECT DISTINCT category_key FROM category_transit_limits WHERE tier_key = "normal"')
    categories = [row[0] for row in cursor.fetchall()]
    
    for category_key in categories:
        cursor.execute('''
            SELECT max_transit_activations, include_macro_transits, include_navatara_warnings
            FROM category_transit_limits
            WHERE category_key = ? AND tier_key = 'normal'
        ''', (category_key,))
        
        result = cursor.fetchone()
        if result:
            max_act, macro, navatara = result
            cursor.execute('''
                INSERT OR IGNORE INTO category_transit_limits 
                (category_key, tier_key, max_transit_activations, include_macro_transits, include_navatara_warnings)
                VALUES (?, 'premium', ?, ?, ?)
            ''', (category_key, max_act, macro, navatara))
            
            cursor.execute('''
                INSERT OR IGNORE INTO category_transit_limits 
                (category_key, tier_key, max_transit_activations, include_macro_transits, include_navatara_warnings)
                VALUES (?, 'light', ?, ?, ?)
            ''', (category_key, max_act, macro, navatara))
    
    conn.commit()
    conn.close()
    print("\n✅ All tier configurations ensured and synced")

if __name__ == '__main__':
    ensure_all_tier_configs()
