import sqlite3
import os

def seed_layer_configuration():
    """Seed all layer configuration data"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'astrology.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Seed Astrological Layers
        layers = [
            ('basic_core', 'Basic/Core', 'Essential Vedic techniques - required for ALL queries', 1),
            ('intermediate', 'Intermediate', 'Standard divisional charts and basic dashas', 2),
            ('advanced', 'Advanced', 'Ashtakavarga, Shadbala, Yogas', 3),
            ('jaimini', 'Jaimini System', 'Chara Dasha, Karakas, Argala', 4),
            ('nadi', 'Nadi Astrology', 'Nadi links and age activations', 5),
            ('specialized', 'Specialized Systems', 'Kota Chakra, Sniper Points, Pushkara', 6),
            ('timing_transits', 'Timing & Transits', 'Transit analysis and timing dashas', 7),
            ('metadata', 'Metadata', 'Response structure and special lagnas', 8),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO astrological_layers (layer_key, layer_name, description, priority)
            VALUES (?, ?, ?, ?)
        """, layers)
        
        # 2. Seed Context Fields
        fields = [
            # Layer 1: Basic/Core
            ('planetary_analysis', 'Planetary Analysis (D1)', 'D1 planet analysis with signs, houses, nakshatras', 10071, 'basic_core'),
            ('d9_planetary_analysis', 'D9 Planetary Analysis', 'Navamsa planet analysis', 9755, 'basic_core'),
            ('d1_chart', 'D1 Chart', 'Basic chart positions', 3404, 'basic_core'),
            ('ascendant_info', 'Ascendant Info', 'Lagna details', 287, 'basic_core'),
            ('house_lordships', 'House Lordships', 'House rulers', 117, 'basic_core'),
            ('birth_details', 'Birth Details', 'Date, time, location', 124, 'basic_core'),
            ('birth_panchang', 'Birth Panchang', 'Tithi, nakshatra, yoga, karana', 331, 'basic_core'),
            
            # Layer 2: Intermediate
            ('divisional_charts', 'Divisional Charts', 'All D-charts (filtered by category)', 42908, 'intermediate'),
            ('current_dashas', 'Current Dashas', 'Vimshottari MD/AD/PD with maraka analysis', 1908, 'intermediate'),
            ('yogini_dasha', 'Yogini Dasha', 'Yogini dasha system', 341, 'intermediate'),
            
            # Layer 3: Advanced
            ('ashtakavarga', 'Ashtakavarga', 'SAV + BAV for D1 and D9', 6505, 'advanced'),
            ('yogas', 'Yogas', 'Raj, Dhana, Pancha Mahapurusha yogas', 3172, 'advanced'),
            ('advanced_analysis', 'Advanced Analysis', 'Wars, Vargottama, Neecha Bhanga', 1416, 'advanced'),
            ('nakshatra_remedies', 'Nakshatra Remedies', 'Remedies for all planets', 9311, 'advanced'),
            
            # Layer 4: Jaimini
            ('chara_dasha', 'Chara Dasha', 'Sign-based dasha with antardashas', 22450, 'jaimini'),
            ('jaimini_full_analysis', 'Jaimini Full Analysis', 'Relative views, raj yogas', 4939, 'jaimini'),
            ('chara_karakas', 'Chara Karakas', 'AK, AmK, BK, DK, etc.', 2207, 'jaimini'),
            ('jaimini_points', 'Jaimini Points', 'AL, UL, HL, GL, A7', 716, 'jaimini'),
            ('relationships', 'Relationships (Argala)', 'Argala analysis', 10007, 'jaimini'),
            
            # Layer 5: Nadi
            ('nadi_links', 'Nadi Links', 'Planet-to-planet links', 2550, 'nadi'),
            ('nadi_age_activation', 'Nadi Age Activation', 'Age-based activations', 229, 'nadi'),
            
            # Layer 6: Specialized
            ('sniper_points', 'Sniper Points', 'Bhrigu Bindu, Mrityu Bhaga', 2070, 'specialized'),
            ('kota_chakra', 'Kota Chakra', 'Kota analysis', 1208, 'specialized'),
            ('special_points', 'Special Points', 'Gandanta, Yogi/Avayogi', 787, 'specialized'),
            ('pushkara_navamsa', 'Pushkara Navamsa', 'Pushkara degrees', 675, 'specialized'),
            ('sudarshana_chakra', 'Sudarshana Chakra', 'Triple chakra analysis', 535, 'specialized'),
            
            # Layer 7: Timing & Transits
            ('macro_transits_timeline', 'Macro Transits Timeline', '5-year slow planet transits', 6085, 'timing_transits'),
            ('transit_data_availability', 'Transit Data Availability', 'Transit request instructions', 6011, 'timing_transits'),
            ('transit_activations', 'Transit Activations', 'Current transit activations (limited by category)', 100000, 'timing_transits'),
            ('navatara_warnings', 'Navatara Warnings', 'Nakshatra-based warnings', 765, 'timing_transits'),
            ('shoola_dasha', 'Shoola Dasha', 'Event-based dasha', 1486, 'timing_transits'),
            ('kalchakra_dasha', 'Kalachakra Dasha', 'Kalachakra dasha', 131, 'timing_transits'),
            ('prediction_matrix', 'Prediction Matrix', 'Prediction framework', 141, 'timing_transits'),
            ('dasha_conflicts', 'Dasha Conflicts', 'Conflicting dasha results', 46, 'timing_transits'),
            
            # Layer 8: Metadata
            ('RESPONSE_STRUCTURE_REQUIRED', 'Response Structure', 'JSON response format', 794, 'metadata'),
            ('special_lagnas', 'Special Lagnas', 'Indu Lagna', 146, 'metadata'),
        ]
        
        # Get layer IDs
        cursor.execute("SELECT layer_id, layer_key FROM astrological_layers")
        layer_map = {key: id for id, key in cursor.fetchall()}
        
        fields_with_ids = [(f[0], f[1], f[2], f[3], layer_map[f[4]]) for f in fields]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO context_fields (field_key, field_name, description, estimated_size_bytes, layer_id)
            VALUES (?, ?, ?, ?, ?)
        """, fields_with_ids)
        
        # 3. Seed Divisional Charts
        charts = [
            ('D1', 'Rashi (D1)', 1, 'general', 'Basic birth chart'),
            ('D3', 'Drekkana (D3)', 3, 'general', 'Siblings, courage'),
            ('D4', 'Chaturthamsa (D4)', 4, 'wealth', 'Property, assets'),
            ('D7', 'Saptamsa (D7)', 7, 'marriage', 'Marriage, children'),
            ('D9', 'Navamsa (D9)', 9, 'general', 'Spouse, dharma'),
            ('D10', 'Dasamsa (D10)', 10, 'career', 'Career, profession'),
            ('D12', 'Dwadasamsa (D12)', 12, 'general', 'Parents, ancestry'),
            ('D16', 'Shodasamsa (D16)', 16, 'wealth', 'Vehicles, comforts'),
            ('D20', 'Vimshamsa (D20)', 20, 'general', 'Spiritual progress'),
            ('D24', 'Chaturvimshamsa (D24)', 24, 'education', 'Education, learning'),
            ('D27', 'Nakshatramsa (D27)', 27, 'general', 'Strengths/weaknesses'),
            ('D30', 'Trimsamsa (D30)', 30, 'health', 'Health, diseases'),
            ('D40', 'Khavedamsa (D40)', 40, 'general', 'Auspicious/inauspicious'),
            ('D45', 'Akshavedamsa (D45)', 45, 'general', 'Character, conduct'),
            ('D60', 'Shashtiamsa (D60)', 60, 'general', 'Past life karma'),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO divisional_charts (chart_key, chart_name, chart_number, primary_domain, description)
            VALUES (?, ?, ?, ?, ?)
        """, charts)
        
        # 4. Seed Category Layer Requirements
        category_layers = [
            # Career
            ('career', 'basic_core', 1),
            ('career', 'intermediate', 1),
            ('career', 'advanced', 1),
            ('career', 'jaimini', 1),
            ('career', 'nadi', 1),
            ('career', 'specialized', 0),
            ('career', 'timing_transits', 1),
            ('career', 'metadata', 1),
            
            # Health
            ('health', 'basic_core', 1),
            ('health', 'intermediate', 1),
            ('health', 'advanced', 1),
            ('health', 'jaimini', 0),
            ('health', 'nadi', 0),
            ('health', 'specialized', 1),
            ('health', 'timing_transits', 1),
            ('health', 'metadata', 1),
            
            # Marriage
            ('marriage', 'basic_core', 1),
            ('marriage', 'intermediate', 1),
            ('marriage', 'advanced', 1),
            ('marriage', 'jaimini', 1),
            ('marriage', 'nadi', 1),
            ('marriage', 'specialized', 0),
            ('marriage', 'timing_transits', 1),
            ('marriage', 'metadata', 1),
            
            # Wealth
            ('wealth', 'basic_core', 1),
            ('wealth', 'intermediate', 1),
            ('wealth', 'advanced', 1),
            ('wealth', 'jaimini', 1),
            ('wealth', 'nadi', 1),
            ('wealth', 'specialized', 1),
            ('wealth', 'timing_transits', 1),
            ('wealth', 'metadata', 1),
            
            # Progeny
            ('progeny', 'basic_core', 1),
            ('progeny', 'intermediate', 1),
            ('progeny', 'advanced', 1),
            ('progeny', 'jaimini', 1),
            ('progeny', 'nadi', 1),
            ('progeny', 'specialized', 0),
            ('progeny', 'timing_transits', 1),
            ('progeny', 'metadata', 1),
            
            # Education
            ('education', 'basic_core', 1),
            ('education', 'intermediate', 1),
            ('education', 'advanced', 1),
            ('education', 'jaimini', 1),
            ('education', 'nadi', 1),
            ('education', 'specialized', 0),
            ('education', 'timing_transits', 1),
            ('education', 'metadata', 1),
            
            # Timing
            ('timing', 'basic_core', 1),
            ('timing', 'intermediate', 1),
            ('timing', 'advanced', 1),
            ('timing', 'jaimini', 1),
            ('timing', 'nadi', 1),
            ('timing', 'specialized', 1),
            ('timing', 'timing_transits', 1),
            ('timing', 'metadata', 1),
            
            # General
            ('general', 'basic_core', 1),
            ('general', 'intermediate', 1),
            ('general', 'advanced', 1),
            ('general', 'jaimini', 1),
            ('general', 'nadi', 1),
            ('general', 'specialized', 1),
            ('general', 'timing_transits', 1),
            ('general', 'metadata', 1),
        ]
        
        category_layers_with_ids = [
            (cat, layer_map[layer], req) for cat, layer, req in category_layers
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO category_layer_requirements (category_key, layer_id, is_required)
            VALUES (?, ?, ?)
        """, category_layers_with_ids)
        
        # 5. Seed Category Divisional Chart Requirements
        cursor.execute("SELECT chart_id, chart_key FROM divisional_charts")
        chart_map = {key: id for id, key in cursor.fetchall()}
        
        category_charts = [
            # Career: D10, D24
            ('career', 'D10', 1),
            ('career', 'D24', 1),
            
            # Health: D30
            ('health', 'D30', 1),
            
            # Marriage: D7, D9
            ('marriage', 'D7', 1),
            ('marriage', 'D9', 1),
            
            # Wealth: D4, D16
            ('wealth', 'D4', 1),
            ('wealth', 'D16', 1),
            
            # Progeny: D7
            ('progeny', 'D7', 1),
            
            # Education: D24
            ('education', 'D24', 1),
            
            # Timing: D9
            ('timing', 'D9', 1),
            
            # General: D9
            ('general', 'D9', 1),
        ]
        
        category_charts_with_ids = [
            (cat, chart_map[chart], req) for cat, chart, req in category_charts
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO category_divisional_requirements (category_key, chart_id, is_required)
            VALUES (?, ?, ?)
        """, category_charts_with_ids)
        
        # 6. Seed Category Transit Limits
        transit_limits = [
            ('career', 15, 1, 0),
            ('health', 10, 1, 1),
            ('marriage', 12, 1, 0),
            ('wealth', 15, 1, 0),
            ('progeny', 10, 1, 0),
            ('education', 12, 1, 0),
            ('timing', 25, 1, 1),
            ('general', 20, 1, 0),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO category_transit_limits 
            (category_key, max_transit_activations, include_macro_transits, include_navatara_warnings)
            VALUES (?, ?, ?, ?)
        """, transit_limits)
        
        conn.commit()
        print("✅ Layer configuration seeded successfully")
        print(f"   - {len(layers)} layers")
        print(f"   - {len(fields)} context fields")
        print(f"   - {len(charts)} divisional charts")
        print(f"   - {len(category_layers)} category-layer mappings")
        print(f"   - {len(category_charts)} category-chart mappings")
        print(f"   - {len(transit_limits)} transit limit configs")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    seed_layer_configuration()
