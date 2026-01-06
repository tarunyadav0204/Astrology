#!/usr/bin/env python3
"""
Test the transit loop antardasha_sign fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from chat.chat_context_builder import ChatContextBuilder
from datetime import datetime

# Your birth data
birth_data = {
    'name': 'Test User',
    'date': '1980-04-02',
    'time': '14:55',
    'latitude': 29.1492,
    'longitude': 75.7217,
    'timezone': 'Asia/Kolkata'
}

print("="*80)
print("🧪 TRANSIT LOOP ANTARDASHA TEST")
print("="*80)

# Build context with transit request
builder = ChatContextBuilder()

# Simulate intent result for 2026
intent_result = {
    'transit_request': {
        'startYear': 2026,
        'endYear': 2026
    }
}

context = builder.build_complete_context(birth_data, "What about 2026?", None, None, intent_result)

# Check if transit activations exist
if 'transit_activations' in context:
    transits = context['transit_activations']
    print(f"\n✅ Transit activations: {len(transits)} found")
    
    # Check first transit's chara_sequence
    if transits and len(transits) > 0:
        first_transit = transits[0]
        comp_dashas = first_transit.get('comprehensive_dashas', {})
        chara_seq = comp_dashas.get('chara_sequence', [])
        
        print(f"\n📅 CHARA SEQUENCE in transit:")
        for period in chara_seq[:3]:  # Show first 3
            md = period.get('mahadasha_sign', 'Unknown')
            ad = period.get('antardasha_sign', 'Unknown')
            print(f"   MD: {md}, AD: {ad}")
            
            if ad == 'Unknown':
                print(f"   ❌ BUG: Antardasha still showing Unknown!")
            else:
                print(f"   ✅ Antardasha properly extracted")
else:
    print(f"\n⚠️ No transit activations (might need actual transit data)")

print(f"\n{'='*80}")
print("✅ TEST COMPLETE")
print("="*80)
