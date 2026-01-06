#!/usr/bin/env python3
"""
Test if nadi_links and sudarshana_chakra make it to final context
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from chat.chat_context_builder import ChatContextBuilder

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
print("🧪 CONTEXT BUILDER TEST - NADI & SUDARSHANA")
print("="*80)

# Build complete context
builder = ChatContextBuilder()
context = builder.build_complete_context(birth_data, "Test question about career")

print(f"\n📊 CONTEXT KEYS: {list(context.keys())[:20]}...")

# Check nadi_links
if 'nadi_links' in context:
    nadi_data = context['nadi_links']
    if nadi_data:
        print(f"\n✅ nadi_links PRESENT: {len(nadi_data)} planets")
        for planet in ['Saturn', 'Jupiter', 'Venus']:
            if planet in nadi_data:
                links = nadi_data[planet].get('all_links', [])
                print(f"   {planet}: {len(links)} links - {links}")
    else:
        print(f"\n❌ nadi_links is EMPTY dict")
else:
    print(f"\n❌ nadi_links NOT in context")

# Check sudarshana_chakra
if 'sudarshana_chakra' in context:
    sud_data = context['sudarshana_chakra']
    if sud_data:
        print(f"\n✅ sudarshana_chakra PRESENT: {list(sud_data.keys())}")
    else:
        print(f"\n❌ sudarshana_chakra is EMPTY dict")
else:
    print(f"\n❌ sudarshana_chakra NOT in context")

print(f"\n{'='*80}")
print("✅ TEST COMPLETE")
print("="*80)
