#!/usr/bin/env python3
"""
Seed initial prompt configuration data
Run: python3 chat/PromptConfig/seed_data.py
"""

import sqlite3
import json
import os

def seed_instruction_modules(cursor):
    """Seed instruction modules"""
    
    modules = [
        {
            'module_key': 'core',
            'module_name': 'Core Vedic Principles',
            'instruction_text': '''You are a master Vedic astrologer with deep knowledge of classical texts.
Tone: Direct, technical, objective, solution-oriented.
Philosophy: Astrology indicates "Karma," not "Fate."
Always cite classical texts (BPHS, Jaimini Sutras, Phaladeepika, Saravali).''',
            'priority': 100
        },
        {
            'module_key': 'timing',
            'module_name': 'Timing & Dasha Analysis',
            'instruction_text': '''TIMING SYNTHESIS (MANDATORY):
- Analyze Vimshottari Mahadasha, Antardasha, Pratyantardasha
- Cross-reference with Chara Dasha (Jaimini)
- Include Yogini Dasha for karmic timing
- Cite specific dasha periods with dates''',
            'priority': 90
        },
        {
            'module_key': 'jaimini',
            'module_name': 'Jaimini System',
            'instruction_text': '''JAIMINI ANALYSIS:
- Use Arudha Lagna (AL) for fame/status
- Use Upapada Lagna (UL) for marriage
- Analyze Karkamsa for career dharma
- Check Chara Dasha sign aspects using sign_aspects mapping
- Never assume aspects - verify from JSON data''',
            'priority': 80
        },
        {
            'module_key': 'nadi',
            'module_name': 'Nadi Astrology',
            'instruction_text': '''NADI PRECISION:
- Check nadi_links for specific event nature
- Saturn links define career type (Saturn+Mars=Technical, Saturn+Jupiter=Teaching)
- Venus links define wealth/marriage source
- Moon links define mental patterns''',
            'priority': 70
        },
        {
            'module_key': 'health_kota',
            'module_name': 'Health - Kota Chakra',
            'instruction_text': '''KOTA CHAKRA (Health Crisis Detection):
- Check malefics in Stambha (inner pillar) for health threats
- Analyze Kota Swami strength
- Check Kota Paala (guard) position
- Entering motion = crisis building, Exiting = recovery''',
            'priority': 60
        },
        {
            'module_key': 'health_mrityu',
            'module_name': 'Health - Mrityu Bhaga',
            'instruction_text': '''MRITYU BHAGA (Death Degree):
- Check if planets/Lagna on death degree
- Planet on Mrityu Bhaga cannot protect its house significations
- Requires remedies for afflicted planets''',
            'priority': 50
        },
        {
            'module_key': 'divisional',
            'module_name': 'Divisional Chart Analysis',
            'instruction_text': '''DIVISIONAL CHARTS:
- D9 (Navamsa): Marriage, dharma, strength check
- D10 (Dasamsa): Career, authority
- D7 (Saptamsa): Children, progeny
- D30 (Trimsamsa): Misfortunes, hidden dangers
- Always synthesize D1 + relevant D-chart''',
            'priority': 40
        },
        {
            'module_key': 'transits',
            'module_name': 'Transit Analysis',
            'instruction_text': '''TRANSIT ANALYSIS:
- Use ONLY transit data provided in JSON
- Check Ashtakavarga points for house strength
- Analyze dasha-transit correlation
- Predict specific events with exact dates''',
            'priority': 30
        }
    ]
    
    for module in modules:
        cursor.execute('''
            INSERT OR REPLACE INTO prompt_instruction_modules 
            (module_key, module_name, instruction_text, character_count, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            module['module_key'],
            module['module_name'],
            module['instruction_text'],
            len(module['instruction_text']),
            module['priority']
        ))
    
    print(f"✅ Seeded {len(modules)} instruction modules")

def seed_category_configs(cursor):
    """Seed category configurations"""
    
    categories = [
        {
            'category_key': 'career',
            'category_name': 'Career & Profession',
            'required_modules': ['core', 'timing', 'jaimini', 'nadi'],
            'required_data_fields': [
                'birth_details', 'd1_chart', 'd9_navamsa', 'd10_dasamsa',
                'current_dashas', 'chara_dasha', 'yogini_dasha',
                'jaimini_points', 'nadi_links', 'house_lordships'
            ],
            'optional_data_fields': ['transit_activations', 'yogas'],
            'max_transit_activations': 15
        },
        {
            'category_key': 'health',
            'category_name': 'Health & Wellness',
            'required_modules': ['core', 'timing', 'health_kota', 'health_mrityu'],
            'required_data_fields': [
                'birth_details', 'd1_chart', 'd9_navamsa', 'd30_trimsamsa',
                'current_dashas', 'kota_chakra', 'sniper_points',
                'planetary_analysis', 'house_lordships'
            ],
            'optional_data_fields': ['transit_activations'],
            'max_transit_activations': 10
        },
        {
            'category_key': 'marriage',
            'category_name': 'Marriage & Relationships',
            'required_modules': ['core', 'timing', 'jaimini', 'divisional'],
            'required_data_fields': [
                'birth_details', 'd1_chart', 'd9_navamsa', 'd7_saptamsa',
                'current_dashas', 'chara_dasha', 'jaimini_points',
                'nadi_links', 'house_lordships'
            ],
            'optional_data_fields': ['transit_activations', 'yogas'],
            'max_transit_activations': 12
        },
        {
            'category_key': 'wealth',
            'category_name': 'Wealth & Finance',
            'required_modules': ['core', 'timing', 'jaimini', 'nadi'],
            'required_data_fields': [
                'birth_details', 'd1_chart', 'd9_navamsa',
                'current_dashas', 'chara_dasha', 'jaimini_points',
                'nadi_links', 'house_lordships', 'yogas'
            ],
            'optional_data_fields': ['transit_activations'],
            'max_transit_activations': 15
        },
        {
            'category_key': 'timing',
            'category_name': 'Event Timing & Predictions',
            'required_modules': ['core', 'timing', 'transits'],
            'required_data_fields': [
                'birth_details', 'd1_chart', 'd9_navamsa',
                'current_dashas', 'chara_dasha', 'yogini_dasha',
                'transit_activations', 'ashtakavarga', 'house_lordships'
            ],
            'optional_data_fields': ['jaimini_points', 'nadi_links'],
            'max_transit_activations': 25
        },
        {
            'category_key': 'general',
            'category_name': 'General Life Analysis',
            'required_modules': ['core', 'timing', 'jaimini', 'divisional'],
            'required_data_fields': [
                'birth_details', 'd1_chart', 'd9_navamsa',
                'current_dashas', 'chara_dasha', 'yogini_dasha',
                'planetary_analysis', 'house_lordships', 'yogas'
            ],
            'optional_data_fields': ['transit_activations', 'nadi_links'],
            'max_transit_activations': 20
        }
    ]
    
    for category in categories:
        cursor.execute('''
            INSERT OR REPLACE INTO prompt_category_config 
            (category_key, category_name, required_modules, required_data_fields,
             optional_data_fields, max_transit_activations)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            category['category_key'],
            category['category_name'],
            json.dumps(category['required_modules']),
            json.dumps(category['required_data_fields']),
            json.dumps(category['optional_data_fields']),
            category['max_transit_activations']
        ))
    
    print(f"✅ Seeded {len(categories)} category configurations")

def seed_data():
    """Main seed function"""
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'astrology.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Seeding prompt configuration data...")
    
    seed_instruction_modules(cursor)
    seed_category_configs(cursor)
    
    conn.commit()
    conn.close()
    
    print("\n✅ All data seeded successfully!")
    print("\nYou can now:")
    print("1. Use PromptConfigService to fetch configurations")
    print("2. Access admin UI to manage modules and categories")
    print("3. View performance logs in prompt_performance_log table")

if __name__ == '__main__':
    seed_data()
