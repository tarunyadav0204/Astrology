#!/usr/bin/env python3
"""
Comprehensive test for Jaimini Relative Views and Varshphal integration
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
from calculators.varshphal_calculator import VarshphalCalculator
from types import SimpleNamespace
import json

# Your actual birth data
birth_data = {
    'name': 'Test User',
    'date': '1980-04-02',
    'time': '14:55',
    'latitude': 29.1492,
    'longitude': 75.7217,
    'timezone': 'Asia/Kolkata'
}

print("="*80)
print("🧪 COMPREHENSIVE JAIMINI + VARSHPHAL TEST")
print("="*80)

# 1. Calculate chart
birth_obj = SimpleNamespace(**birth_data)
chart_calc = ChartCalculator(birth_obj)
chart_data = chart_calc.calculate_chart(birth_obj)
print(f"\n✅ Chart calculated - Ascendant: {chart_data['ascendant']:.2f}°")

# 2. Calculate Chara Dasha
chara_calc = CharaDashaCalculator(chart_data)
dob_dt = datetime.strptime(birth_data['date'], '%Y-%m-%d')
chara_dasha_data = chara_calc.calculate_dasha(dob_dt)

print(f"\n📅 CHARA DASHA (Current Period):")
for period in chara_dasha_data['periods']:
    if period['is_current']:
        print(f"   MD: {period['sign_name']} - {period['start_date']} to {period['end_date']}")
        if period['antardashas']:
            for ad in period['antardashas']:
                if ad['is_current']:
                    print(f"   AD: {ad['sign_name']} - {ad['start_date']} to {ad['end_date']}")

# 3. Calculate Karakas
karaka_calc = CharaKarakaCalculator(chart_data)
karaka_data = karaka_calc.calculate_chara_karakas()

# 4. Calculate Jaimini Points
div_calc = DivisionalChartCalculator(chart_data)
d9_chart = div_calc.calculate_divisional_chart(9)
ak_planet = karaka_data['chara_karakas']['Atmakaraka']['planet']
jaimini_calc = JaiminiPointCalculator(chart_data, d9_chart, ak_planet)
jaimini_points = jaimini_calc.calculate_jaimini_points()

# 5. Run Jaimini Full Analyzer
jaimini_analyzer = JaiminiFullAnalyzer(chart_data, karaka_data, jaimini_points, chara_dasha_data)
jaimini_report = jaimini_analyzer.get_jaimini_report()

print(f"\n🏛️ JAIMINI RELATIVE VIEWS:")
for view_name, view_data in jaimini_report['relative_views'].items():
    base_sign = view_data.get('base_sign')
    base_name = view_data.get('base_sign_name', 'None')
    print(f"   {view_name}: {base_name} (ID: {base_sign})")

# 6. Test Varshphal for 2026
print(f"\n📅 VARSHPHAL TEST (Year 2026):")
try:
    vp_calc = VarshphalCalculator(chart_calc)
    varshphal_data = vp_calc.calculate_varshphal(birth_data, 2026)
    
    muntha_sign = varshphal_data['muntha']['sign']
    sign_lords = {
        1: 'Mars', 2: 'Venus', 3: 'Mercury', 4: 'Moon', 5: 'Sun', 6: 'Mercury',
        7: 'Venus', 8: 'Mars', 9: 'Jupiter', 10: 'Saturn', 11: 'Saturn', 12: 'Jupiter'
    }
    muntha_lord = sign_lords.get(muntha_sign, 'Unknown')
    
    print(f"   ✅ Muntha House: {varshphal_data['muntha']['house']}")
    print(f"   ✅ Muntha Sign: {muntha_sign}")
    print(f"   ✅ Muntha Lord: {muntha_lord}")
    print(f"   ✅ Year Lord: {varshphal_data['year_lord']}")
    print(f"   ✅ Mudda Dasha periods: {len(varshphal_data['mudda_dasha'])}")
except Exception as e:
    print(f"   ❌ Varshphal failed: {e}")

print(f"\n{'='*80}")
print("✅ ALL TESTS COMPLETE")
print("="*80)
