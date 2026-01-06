#!/usr/bin/env python3
"""
Test script to check Nadi Links and Sudarshana Chakra data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from calculators.chart_calculator import ChartCalculator
from calculators.nadi_linkage_calculator import NadiLinkageCalculator
from calculators.sudarshana_chakra_calculator import SudarshanaChakraCalculator
from types import SimpleNamespace
import json

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
print("🧪 NADI LINKS & SUDARSHANA TEST")
print("="*80)

# Calculate chart
birth_obj = SimpleNamespace(**birth_data)
chart_calc = ChartCalculator(birth_obj)
chart_data = chart_calc.calculate_chart(birth_obj)
print(f"\n✅ Chart calculated")

# Test Nadi Links
print(f"\n📊 NADI LINKS TEST:")
try:
    nadi_calc = NadiLinkageCalculator(chart_data)
    nadi_links = nadi_calc.get_nadi_links()
    
    if nadi_links:
        print(f"   ✅ Nadi links calculated: {len(nadi_links)} planets")
        for planet, links in nadi_links.items():
            if links.get('all_links'):
                print(f"   {planet}: {len(links['all_links'])} links")
    else:
        print(f"   ❌ Nadi links EMPTY")
        
    print(f"\n   Sample data: {json.dumps(nadi_links, indent=2, default=str)[:500]}...")
except Exception as e:
    print(f"   ❌ Nadi calculation failed: {e}")
    import traceback
    traceback.print_exc()

# Test Sudarshana
print(f"\n🔄 SUDARSHANA CHAKRA TEST:")
try:
    sudarshana_calc = SudarshanaChakraCalculator(chart_data)
    sudarshana_data = sudarshana_calc.get_sudarshana_view()
    
    if sudarshana_data:
        print(f"   ✅ Sudarshana calculated: {len(sudarshana_data)} perspectives")
        for perspective, data in sudarshana_data.items():
            print(f"   {perspective}: {type(data)}")
    else:
        print(f"   ❌ Sudarshana EMPTY")
        
    print(f"\n   Sample data: {json.dumps(sudarshana_data, indent=2, default=str)[:500]}...")
except Exception as e:
    print(f"   ❌ Sudarshana calculation failed: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("✅ TEST COMPLETE")
print("="*80)
