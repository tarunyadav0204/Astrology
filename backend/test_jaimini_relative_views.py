#!/usr/bin/env python3
"""
Test script to debug Jaimini Relative Views and Chara Dasha extraction
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from calculators.chart_calculator import ChartCalculator
from calculators.chara_dasha_calculator import CharaDashaCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.jaimini_point_calculator import JaiminiPointCalculator
from calculators.jaimini_full_analyzer import JaiminiFullAnalyzer
from calculators.divisional_chart_calculator import DivisionalChartCalculator
import json

# Test birth data - Your actual birth details
birth_data = {
    'name': 'Test',
    'date': '1980-04-02',
    'time': '14:55',
    'latitude': 29.1492,  # Hisar, Haryana
    'longitude': 75.7217,
    'timezone': 'Asia/Kolkata'
}

print("="*80)
print("🧪 JAIMINI RELATIVE VIEWS TEST")
print("="*80)

# 1. Calculate chart
from types import SimpleNamespace
birth_obj = SimpleNamespace(**birth_data)
chart_calc = ChartCalculator(birth_obj)
chart_data = chart_calc.calculate_chart(birth_obj)
print(f"\n✅ Chart calculated - Ascendant: {chart_data['ascendant']:.2f}° ({int(chart_data['ascendant']/30)})")

# 2. Calculate Chara Dasha
chara_calc = CharaDashaCalculator(chart_data)
dob_dt = datetime.strptime(birth_data['date'], '%Y-%m-%d')
chara_dasha_data = chara_calc.calculate_dasha(dob_dt)

print(f"\n📅 CHARA DASHA PERIODS:")
for period in chara_dasha_data['periods']:
    if period['is_current']:
        print(f"   ✅ CURRENT MD: {period['sign_name']} (ID: {period['sign_id']}) - {period['start_date']} to {period['end_date']}")
        if period['antardashas']:
            print(f"   📊 Antardashas ({len(period['antardashas'])} total):")
            for ad in period['antardashas']:
                marker = "   ✅ CURRENT AD:" if ad['is_current'] else "      "
                print(f"{marker} {ad['sign_name']} (ID: {ad['sign_id']}) - {ad['start_date']} to {ad['end_date']}")

# 3. Calculate Karakas
karaka_calc = CharaKarakaCalculator(chart_data)
karaka_data = karaka_calc.calculate_chara_karakas()

print(f"\n🎯 CHARA KARAKAS:")
for karaka_name, karaka_info in karaka_data['chara_karakas'].items():
    print(f"   {karaka_name}: {karaka_info['planet']} in {karaka_info.get('sign')} (Sign ID)")

# 4. Calculate D9
div_calc = DivisionalChartCalculator(chart_data)
d9_chart = div_calc.calculate_divisional_chart(9)

# 5. Calculate Jaimini Points
ak_planet = karaka_data['chara_karakas']['Atmakaraka']['planet']
jaimini_calc = JaiminiPointCalculator(chart_data, d9_chart, ak_planet)
jaimini_points = jaimini_calc.calculate_jaimini_points()

print(f"\n🏛️ JAIMINI POINTS:")
for point_name, point_data in jaimini_points.items():
    print(f"   {point_name}: {point_data['sign_name']} (ID: {point_data['sign_id']})")

# 6. Run Jaimini Full Analyzer
jaimini_analyzer = JaiminiFullAnalyzer(chart_data, karaka_data, jaimini_points, chara_dasha_data)
jaimini_report = jaimini_analyzer.get_jaimini_report()

print(f"\n🔍 RELATIVE VIEWS EXTRACTED:")
for view_name, view_data in jaimini_report['relative_views'].items():
    base_sign = view_data.get('base_sign')
    base_name = view_data.get('base_sign_name', 'None')
    print(f"   {view_name}: {base_name} (ID: {base_sign})")

print(f"\n📊 COMPARISON (for January 2026):")
print(f"   Expected MD: Aquarius (10) vs Extracted: {jaimini_report['relative_views']['mahadasha_lagna'].get('base_sign_name')} ({jaimini_report['relative_views']['mahadasha_lagna'].get('base_sign')})")
print(f"   Expected AD: Capricorn (9) vs Extracted: {jaimini_report['relative_views']['antardasha_lagna'].get('base_sign_name')} ({jaimini_report['relative_views']['antardasha_lagna'].get('base_sign')})")

print(f"\n{'='*80}")
print("✅ TEST COMPLETE")
print("="*80)
