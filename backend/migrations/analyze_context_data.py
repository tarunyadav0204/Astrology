#!/usr/bin/env python3
"""
Analyze all context data fields sent to Gemini
This will help us understand what we're calculating and optimize iteratively
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat.chat_context_builder import ChatContextBuilder
from datetime import datetime

def analyze_context_structure():
    """Analyze the structure and size of context data"""
    
    # Sample birth data for analysis
    sample_birth_data = {
        'name': 'Test User',
        'date': '1990-01-15',
        'time': '10:30:00',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'timezone': 'Asia/Kolkata',
        'place': 'New Delhi'
    }
    
    # Build context
    builder = ChatContextBuilder()
    
    print("Building complete context...")
    context = builder.build_complete_context(
        sample_birth_data,
        user_question="How is my career?",
        target_date=None,
        requested_period=None,
        intent_result={'category': 'career', 'needs_transits': False}
    )
    
    print(f"\n{'='*80}")
    print("COMPLETE CONTEXT DATA INVENTORY")
    print(f"{'='*80}\n")
    
    # Analyze each top-level key
    total_size = 0
    field_analysis = []
    
    for key, value in context.items():
        # Calculate size
        json_str = json.dumps(value, default=str)
        size = len(json_str)
        total_size += size
        
        # Determine type and structure
        value_type = type(value).__name__
        
        # Count nested items
        nested_count = 0
        if isinstance(value, dict):
            nested_count = len(value)
        elif isinstance(value, list):
            nested_count = len(value)
        
        field_analysis.append({
            'key': key,
            'type': value_type,
            'size': size,
            'nested_count': nested_count,
            'percentage': 0  # Will calculate after total
        })
    
    # Calculate percentages
    for field in field_analysis:
        field['percentage'] = (field['size'] / total_size * 100) if total_size > 0 else 0
    
    # Sort by size (largest first)
    field_analysis.sort(key=lambda x: x['size'], reverse=True)
    
    # Print analysis
    print(f"{'Field Name':<50} {'Type':<15} {'Size':<12} {'%':<8} {'Items':<8}")
    print(f"{'-'*50} {'-'*15} {'-'*12} {'-'*8} {'-'*8}")
    
    for field in field_analysis:
        size_str = f"{field['size']:,} B"
        pct_str = f"{field['percentage']:.1f}%"
        items_str = str(field['nested_count']) if field['nested_count'] > 0 else '-'
        
        print(f"{field['key']:<50} {field['type']:<15} {size_str:<12} {pct_str:<8} {items_str:<8}")
    
    print(f"\n{'-'*50} {'-'*15} {'-'*12} {'-'*8} {'-'*8}")
    print(f"{'TOTAL':<50} {'':<15} {f'{total_size:,} B':<12} {'100.0%':<8} {'':<8}")
    
    # Categorize fields by purpose
    print(f"\n{'='*80}")
    print("CATEGORIZATION BY PURPOSE")
    print(f"{'='*80}\n")
    
    categories = {
        'Core Chart Data': ['birth_details', 'ascendant_info', 'd1_chart', 'planetary_analysis', 'd9_planetary_analysis'],
        'Divisional Charts': ['divisional_charts'],
        'Dasha Systems': ['current_dashas', 'chara_dasha', 'kalchakra_dasha', 'shoola_dasha', 'yogini_dasha', 'sudarshana_dasha'],
        'Jaimini System': ['jaimini_points', 'jaimini_full_analysis', 'chara_karakas'],
        'Special Points': ['special_points', 'sniper_points', 'yogi_points'],
        'Nadi & Advanced': ['nadi_links', 'nadi_age_activation'],
        'Sudarshana': ['sudarshana_chakra'],
        'Pushkara': ['pushkara_navamsa'],
        'Kota Chakra': ['kota_chakra'],
        'Transits': ['macro_transits_timeline', 'transit_activations', 'transit_data_availability', 'navatara_warnings'],
        'Ashtakavarga': ['ashtakavarga'],
        'Yogas & Analysis': ['yogas', 'advanced_analysis', 'relationships'],
        'Remedies': ['nakshatra_remedies'],
        'Other': ['house_lordships', 'birth_panchang', 'indu_lagna_analysis', 'varshphal', 
                  'dasha_conflicts', 'bhavat_bhavam', 'prediction_matrix', 'comprehensive_transit_analysis',
                  'RESPONSE_STRUCTURE_REQUIRED', 'requested_dasha_summary']
    }
    
    for cat_name, cat_fields in categories.items():
        cat_size = sum(field['size'] for field in field_analysis if field['key'] in cat_fields)
        cat_pct = (cat_size / total_size * 100) if total_size > 0 else 0
        cat_count = sum(1 for field in field_analysis if field['key'] in cat_fields)
        
        print(f"{cat_name:<30} {cat_count:>3} fields  {cat_size:>10,} B  ({cat_pct:>5.1f}%)")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total fields: {len(field_analysis)}")
    print(f"Total size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print(f"\nTop 10 largest fields:")
    for i, field in enumerate(field_analysis[:10], 1):
        print(f"  {i}. {field['key']}: {field['size']:,} B ({field['percentage']:.1f}%)")

if __name__ == "__main__":
    analyze_context_structure()
