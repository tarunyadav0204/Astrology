import sqlite3
import json

conn = sqlite3.connect('astrology.db')
cursor = conn.cursor()

# Define sensible defaults for each category with actual module_key values
category_defaults = {
    'career': [
        'core_preamble',
        'core_analytical_rules_the_synthesis_protocol',
        'a_the_root_vs_fruit_rule_d1_vs_d9_synthesis',
        'b_the_master_clock_rule_dasha_transit',
        'if_the_user_asks_about_career'
    ],
    'health': [
        'core_preamble',
        'core_analytical_rules_the_synthesis_protocol',
        'a_the_root_vs_fruit_rule_d1_vs_d9_synthesis',
        'b_the_master_clock_rule_dasha_transit',
        'e_the_kota_chakra_rule_uttara_kalamrita_fortress_a',
        'if_the_user_asks_about_health'
    ],
    'marriage': [
        'core_preamble',
        'core_analytical_rules_the_synthesis_protocol',
        'a_the_root_vs_fruit_rule_d1_vs_d9_synthesis',
        'b_the_master_clock_rule_dasha_transit',
        'g_jaimini_full_system_rashi_drishti_yogas',
        'if_the_user_asks_about_marriage_relationships'
    ],
    'wealth': [
        'core_preamble',
        'core_analytical_rules_the_synthesis_protocol',
        'a_the_root_vs_fruit_rule_d1_vs_d9_synthesis',
        'b_the_master_clock_rule_dasha_transit'
    ],
    'progeny': [
        'core_preamble',
        'core_analytical_rules_the_synthesis_protocol',
        'a_the_root_vs_fruit_rule_d1_vs_d9_synthesis',
        'b_the_master_clock_rule_dasha_transit'
    ],
    'education': [
        'core_preamble',
        'core_analytical_rules_the_synthesis_protocol',
        'a_the_root_vs_fruit_rule_d1_vs_d9_synthesis',
        'b_the_master_clock_rule_dasha_transit'
    ],
    'timing': [
        'core_preamble',
        'core_analytical_rules_the_synthesis_protocol',
        'b_the_master_clock_rule_dasha_transit',
        'd_the_micro_timing_rule_yogini_dasha',
        'e_the_double_confirmation_rule_jaimini_chara_dasha',
        'j_the_triple_confirmation_rule_sudarshana_chakra'
    ],
    'general': [
        'core_preamble',
        'core_analytical_rules_the_synthesis_protocol',
        'a_the_root_vs_fruit_rule_d1_vs_d9_synthesis',
        'b_the_master_clock_rule_dasha_transit',
        'classical_text_authority_mandatory_citations',
        'user_memory_integration'
    ]
}

for category_key, modules in category_defaults.items():
    modules_json = json.dumps(modules)
    cursor.execute("""
        UPDATE prompt_category_config
        SET required_modules = ?
        WHERE category_key = ?
    """, (modules_json, category_key))
    print(f"Updated {category_key}: {len(modules)} modules")

conn.commit()
conn.close()
print("✓ Fixed required_modules with actual module_key values")
