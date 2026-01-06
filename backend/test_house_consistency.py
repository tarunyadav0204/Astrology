#!/usr/bin/env python3
"""
Test house calculation consistency
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
print("🧪 HOUSE CALCULATION CONSISTENCY TEST")
print("="*80)

# Build complete context
builder = ChatContextBuilder()
context = builder.build_complete_context(birth_data, "Test question")

# Get Jupiter house from different sources
d1_chart = context.get('d1_chart', {})
d1_planets = d1_chart.get('planets', {})
current_dashas = context.get('current_dashas', {})

print(f"\n🪐 JUPITER HOUSE COMPARISON:")

# From d1_chart
if 'Jupiter' in d1_planets:
    jup_d1 = d1_planets['Jupiter']
    print(f"   d1_chart: House {jup_d1.get('house')}, Sign {jup_d1.get('sign_name')}")

# From planetary_analysis
planetary_analysis = context.get('planetary_analysis', {})
if 'Jupiter' in planetary_analysis:
    jup_pa = planetary_analysis['Jupiter']
    basic_info = jup_pa.get('basic_info', {})
    print(f"   planetary_analysis: House {basic_info.get('house')}, Sign {basic_info.get('sign_name')}")

# From current_dashas (if Jupiter is a dasha lord)
for level in ['mahadasha', 'antardasha', 'pratyantardasha']:
    dasha_info = current_dashas.get(level, {})
    if dasha_info.get('planet') == 'Jupiter':
        print(f"   current_dashas[{level}]: House {dasha_info.get('house')}, Sign {dasha_info.get('sign')}")
        print(f"   analysis_hint: {dasha_info.get('analysis_hint')}")

print(f"\n{'='*80}")
print("✅ TEST COMPLETE")
print("="*80)
