#!/usr/bin/env python3
"""
Test script to verify career analysis planetary placements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.career_ai_context_generator import CareerAIContextGenerator
import json

# Test birth data
birth_data = {
    'name': 'Test User',
    'date': '1990-01-15',
    'time': '10:30',
    'place': 'New Delhi',
    'latitude': 28.6139,
    'longitude': 77.2090,
    'timezone': 'Asia/Kolkata',
    'gender': 'male'
}

print("="*80)
print("🔍 TESTING CAREER ANALYSIS PLANETARY PLACEMENTS")
print("="*80)
print(f"\n📅 Birth Data:")
print(f"  Date: {birth_data['date']}")
print(f"  Time: {birth_data['time']}")
print(f"  Place: {birth_data['place']}")
print(f"  Coordinates: {birth_data['latitude']}, {birth_data['longitude']}")

# Generate career context
print("\n🔄 Generating career context...")
career_context_generator = CareerAIContextGenerator()
context = career_context_generator.build_career_context(birth_data)

print("\n" + "="*80)
print("📊 D1 CHART PLANETARY POSITIONS")
print("="*80)

if 'd1_chart' in context and 'planets' in context['d1_chart']:
    for planet, data in sorted(context['d1_chart']['planets'].items()):
        print(f"\n{planet}:")
        print(f"  House: {data.get('house')}")
        print(f"  Sign: {data.get('sign')} ({data.get('sign_name', 'N/A')})")
        print(f"  Longitude: {data.get('longitude', 0):.4f}°")
        print(f"  Retrograde: {data.get('retrograde', False)}")

print("\n" + "="*80)
print("📊 D10 CHART PLANETARY POSITIONS")
print("="*80)

if 'd10_detailed' in context and 'planets' in context['d10_detailed']:
    for planet, data in sorted(context['d10_detailed']['planets'].items()):
        print(f"\n{planet}:")
        print(f"  House: {data.get('house')}")
        print(f"  Sign: {data.get('sign')} ({data.get('sign_name', 'N/A')})")

print("\n" + "="*80)
print("🏠 10TH HOUSE ANALYSIS")
print("="*80)

if 'tenth_house_analysis' in context:
    tenth = context['tenth_house_analysis']
    print(f"\nSign: {tenth.get('sign_name')}")
    print(f"Lord: {tenth.get('lord')}")
    print(f"Planets in 10th: {tenth.get('planets_in_house')}")
    if 'lord_nakshatra' in tenth:
        print(f"Lord Nakshatra: {tenth['lord_nakshatra'].get('name')} (ruled by {tenth['lord_nakshatra'].get('lord')})")

print("\n" + "="*80)
print("👑 CHARA KARAKAS")
print("="*80)

if 'chara_karakas' in context:
    for karaka, planet in sorted(context['chara_karakas'].items()):
        print(f"{karaka}: {planet}")

print("\n" + "="*80)
print("🎯 AMATYAKARAKA ANALYSIS")
print("="*80)

if 'amatyakaraka_career' in context:
    amk = context['amatyakaraka_career']
    print(f"\nPlanet: {amk.get('planet')}")
    print(f"House: {amk.get('house')}")
    print(f"Sign: {amk.get('sign_name')}")
    print(f"Significance: {amk.get('career_significance')}")

print("\n" + "="*80)
print("✅ TEST COMPLETE")
print("="*80)
print("\n💡 Instructions:")
print("1. Run this script: python test_career_placements.py")
print("2. Compare the planetary positions with what mobile app shows")
print("3. Check if houses, signs, and nakshatras match")
print("4. If they don't match, the issue is in the AI interpretation, not the data")
