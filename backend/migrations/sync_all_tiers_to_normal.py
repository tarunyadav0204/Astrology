import sqlite3
import json

def sync_all_tiers_to_normal():
    """Copy normal tier configuration to premium and light tiers for all categories"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    categories = ["career", "health", "marriage", "wealth", "progeny", "education", "timing", "general"]
    
    for category_key in categories:
        print(f"\nSyncing {category_key}...")
        
        # 1. Sync instruction modules
        cursor.execute('''
            SELECT required_modules FROM prompt_category_config
            WHERE category_key = ? AND tier_key = 'normal'
        ''', (category_key,))
        normal_modules = cursor.fetchone()
        
        if normal_modules and normal_modules[0]:
            modules_json = normal_modules[0]
            cursor.execute('''
                UPDATE prompt_category_config
                SET required_modules = ?
                WHERE category_key = ? AND tier_key IN ('premium', 'light')
            ''', (modules_json, category_key))
            print(f"  ✓ Synced instruction modules")
        
        # 2. Sync layer requirements
        cursor.execute('''
            SELECT layer_id, is_required FROM category_layer_requirements
            WHERE category_key = ? AND tier_key = 'normal'
        ''', (category_key,))
        normal_layers = cursor.fetchall()
        
        for layer_id, is_required in normal_layers:
            cursor.execute('''
                UPDATE category_layer_requirements
                SET is_required = ?
                WHERE category_key = ? AND layer_id = ? AND tier_key IN ('premium', 'light')
            ''', (is_required, category_key, layer_id))
        print(f"  ✓ Synced {len(normal_layers)} layers")
        
        # 3. Sync chart requirements
        cursor.execute('''
            SELECT chart_id, is_required FROM category_divisional_requirements
            WHERE category_key = ? AND tier_key = 'normal'
        ''', (category_key,))
        normal_charts = cursor.fetchall()
        
        for chart_id, is_required in normal_charts:
            cursor.execute('''
                UPDATE category_divisional_requirements
                SET is_required = ?
                WHERE category_key = ? AND chart_id = ? AND tier_key IN ('premium', 'light')
            ''', (is_required, category_key, chart_id))
        print(f"  ✓ Synced {len(normal_charts)} charts")
        
        # 4. Sync transit limits
        cursor.execute('''
            SELECT max_transit_activations, include_macro_transits, include_navatara_warnings
            FROM category_transit_limits
            WHERE category_key = ? AND tier_key = 'normal'
        ''', (category_key,))
        normal_transit = cursor.fetchone()
        
        if normal_transit:
            max_act, macro, navatara = normal_transit
            cursor.execute('''
                UPDATE category_transit_limits
                SET max_transit_activations = ?, include_macro_transits = ?, include_navatara_warnings = ?
                WHERE category_key = ? AND tier_key IN ('premium', 'light')
            ''', (max_act, macro, navatara, category_key))
            print(f"  ✓ Synced transit limits")
        
        # 5. Sync tier_context_config
        cursor.execute('''
            SELECT tier_context_config FROM prompt_category_config
            WHERE category_key = ? AND tier_key = 'normal'
        ''', (category_key,))
        normal_context_config = cursor.fetchone()
        
        if normal_context_config and normal_context_config[0]:
            context_config_json = normal_context_config[0]
            cursor.execute('''
                UPDATE prompt_category_config
                SET tier_context_config = ?
                WHERE category_key = ? AND tier_key IN ('premium', 'light')
            ''', (context_config_json, category_key))
            print(f"  ✓ Synced tier_context_config")
    
    conn.commit()
    conn.close()
    print("\n✅ All tiers synced to match normal tier configuration")

if __name__ == '__main__':
    sync_all_tiers_to_normal()
