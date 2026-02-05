import sqlite3

def add_tier_to_context_tables():
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Add tier_key to category_layer_requirements
    cursor.execute('''
        ALTER TABLE category_layer_requirements ADD COLUMN tier_key TEXT DEFAULT 'normal'
    ''')
    
    # Add tier_key to category_divisional_requirements
    cursor.execute('''
        ALTER TABLE category_divisional_requirements ADD COLUMN tier_key TEXT DEFAULT 'normal'
    ''')
    
    # Add tier_key to category_transit_limits
    cursor.execute('''
        ALTER TABLE category_transit_limits ADD COLUMN tier_key TEXT DEFAULT 'normal'
    ''')
    
    # Get all existing categories
    cursor.execute('SELECT DISTINCT category_key FROM category_layer_requirements WHERE tier_key IS NULL')
    categories = [row[0] for row in cursor.fetchall()]
    
    for category_key in categories:
        # Duplicate layer requirements for each tier
        cursor.execute('''
            SELECT layer_id, is_required FROM category_layer_requirements 
            WHERE category_key = ? AND tier_key IS NULL
        ''', (category_key,))
        layer_reqs = cursor.fetchall()
        
        for layer_id, is_required in layer_reqs:
            # Premium: keep all
            cursor.execute('''
                INSERT INTO category_layer_requirements (category_key, tier_key, layer_id, is_required)
                VALUES (?, 'premium', ?, ?)
            ''', (category_key, layer_id, is_required))
            
            # Normal: only basic, houses, planets
            cursor.execute('SELECT layer_key FROM astrological_layers WHERE layer_id = ?', (layer_id,))
            layer_key = cursor.fetchone()[0]
            normal_required = 1 if layer_key in ['basic', 'houses', 'planets'] else 0
            cursor.execute('''
                INSERT INTO category_layer_requirements (category_key, tier_key, layer_id, is_required)
                VALUES (?, 'normal', ?, ?)
            ''', (category_key, layer_id, normal_required))
            
            # Light: only basic
            light_required = 1 if layer_key == 'basic' else 0
            cursor.execute('''
                INSERT INTO category_layer_requirements (category_key, tier_key, layer_id, is_required)
                VALUES (?, 'light', ?, ?)
            ''', (category_key, layer_id, light_required))
        
        # Delete old records without tier
        cursor.execute('DELETE FROM category_layer_requirements WHERE category_key = ? AND tier_key IS NULL', (category_key,))
    
    # Duplicate chart requirements for each tier
    cursor.execute('SELECT DISTINCT category_key FROM category_divisional_requirements WHERE tier_key IS NULL')
    categories = [row[0] for row in cursor.fetchall()]
    
    for category_key in categories:
        cursor.execute('''
            SELECT chart_id, is_required FROM category_divisional_requirements 
            WHERE category_key = ? AND tier_key IS NULL
        ''', (category_key,))
        chart_reqs = cursor.fetchall()
        
        for chart_id, is_required in chart_reqs:
            # Premium: keep all
            cursor.execute('''
                INSERT INTO category_divisional_requirements (category_key, tier_key, chart_id, is_required)
                VALUES (?, 'premium', ?, ?)
            ''', (category_key, chart_id, is_required))
            
            # Normal: only D1 and D9
            cursor.execute('SELECT chart_key FROM divisional_charts WHERE chart_id = ?', (chart_id,))
            chart_key = cursor.fetchone()[0]
            normal_required = 1 if chart_key in ['D1', 'D9'] else 0
            cursor.execute('''
                INSERT INTO category_divisional_requirements (category_key, tier_key, chart_id, is_required)
                VALUES (?, 'normal', ?, ?)
            ''', (category_key, chart_id, normal_required))
            
            # Light: only D1
            light_required = 1 if chart_key == 'D1' else 0
            cursor.execute('''
                INSERT INTO category_divisional_requirements (category_key, tier_key, chart_id, is_required)
                VALUES (?, 'light', ?, ?)
            ''', (category_key, chart_id, light_required))
        
        cursor.execute('DELETE FROM category_divisional_requirements WHERE category_key = ? AND tier_key IS NULL', (category_key,))
    
    # Duplicate transit limits for each tier
    cursor.execute('SELECT DISTINCT category_key FROM category_transit_limits WHERE tier_key IS NULL')
    categories = [row[0] for row in cursor.fetchall()]
    
    for category_key in categories:
        cursor.execute('''
            SELECT max_transit_activations, include_macro_transits, include_navatara_warnings 
            FROM category_transit_limits 
            WHERE category_key = ? AND tier_key IS NULL
        ''', (category_key,))
        transit_config = cursor.fetchone()
        
        if transit_config:
            max_act, macro, navatara = transit_config
            
            # Premium: full transits
            cursor.execute('''
                INSERT INTO category_transit_limits (category_key, tier_key, max_transit_activations, include_macro_transits, include_navatara_warnings)
                VALUES (?, 'premium', ?, ?, ?)
            ''', (category_key, max_act, macro, navatara))
            
            # Normal: no transits
            cursor.execute('''
                INSERT INTO category_transit_limits (category_key, tier_key, max_transit_activations, include_macro_transits, include_navatara_warnings)
                VALUES (?, 'normal', 0, 0, 0)
            ''', (category_key,))
            
            # Light: no transits
            cursor.execute('''
                INSERT INTO category_transit_limits (category_key, tier_key, max_transit_activations, include_macro_transits, include_navatara_warnings)
                VALUES (?, 'light', 0, 0, 0)
            ''', (category_key,))
        
        cursor.execute('DELETE FROM category_transit_limits WHERE category_key = ? AND tier_key IS NULL', (category_key,))
    
    conn.commit()
    conn.close()
    print("✅ Tier support added to context data tables")

if __name__ == '__main__':
    add_tier_to_context_tables()
