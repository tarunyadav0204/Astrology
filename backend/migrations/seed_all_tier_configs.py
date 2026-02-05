import sqlite3
import json

def seed_all_tier_configs():
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Category configurations (same for all tiers initially)
    categories = {
        'career': {
            'name': 'Career & Profession',
            'modules': ["core_preamble", "classical_text_authority_mandatory_citations", "user_memory_integration", 
                       "core_analytical_rules_the_synthesis_protocol", "if_the_user_asks_about_career", "response_format_structure"]
        },
        'health': {
            'name': 'Health & Wellness',
            'modules': ["core_preamble", "classical_text_authority_mandatory_citations", "user_memory_integration",
                       "core_analytical_rules_the_synthesis_protocol", "if_the_user_asks_about_health", "response_format_structure"]
        },
        'marriage': {
            'name': 'Marriage & Relationships',
            'modules': ["core_preamble", "classical_text_authority_mandatory_citations", "user_memory_integration",
                       "core_analytical_rules_the_synthesis_protocol", "if_the_user_asks_about_marriage_relationships", "response_format_structure"]
        },
        'wealth': {
            'name': 'Wealth & Finance',
            'modules': ["core_preamble", "classical_text_authority_mandatory_citations", "user_memory_integration",
                       "core_analytical_rules_the_synthesis_protocol", "if_the_user_asks_about_wealth", "response_format_structure"]
        },
        'progeny': {
            'name': 'Children & Progeny',
            'modules': ["core_preamble", "classical_text_authority_mandatory_citations", "user_memory_integration",
                       "core_analytical_rules_the_synthesis_protocol", "response_format_structure"]
        },
        'education': {
            'name': 'Education & Learning',
            'modules': ["core_preamble", "classical_text_authority_mandatory_citations", "user_memory_integration",
                       "core_analytical_rules_the_synthesis_protocol", "response_format_structure"]
        },
        'timing': {
            'name': 'Event Timing & Predictions',
            'modules': ["core_preamble", "classical_text_authority_mandatory_citations", "user_memory_integration",
                       "core_analytical_rules_the_synthesis_protocol", "r_mandatory_timing_synthesis", "response_format_structure"]
        },
        'general': {
            'name': 'General Life Analysis',
            'modules': ["core_preamble", "classical_text_authority_mandatory_citations", "user_memory_integration",
                       "core_analytical_rules_the_synthesis_protocol", "response_format_structure"]
        }
    }
    
    tiers = ['premium', 'normal', 'light']
    
    for category_key, config in categories.items():
        for tier_key in tiers:
            cursor.execute('''
                INSERT INTO prompt_category_config 
                (category_key, tier_key, category_name, required_modules, required_data_fields, 
                 optional_data_fields, max_transit_activations, is_active, tier_context_config)
                VALUES (?, ?, ?, ?, '[]', '[]', 20, 1, '{}')
            ''', (category_key, tier_key, config['name'], json.dumps(config['modules'])))
            print(f"✓ Created {category_key} - {tier_key}")
    
    conn.commit()
    conn.close()
    print("\n✅ All category+tier configurations seeded")

if __name__ == '__main__':
    seed_all_tier_configs()
