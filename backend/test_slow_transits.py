#!/usr/bin/env python3
"""Test script for slow planet transits"""

import sys
import json
from calculators.real_transit_calculator import RealTransitCalculator

# Sample birth data
birth_data = {
    'date': '1990-01-15',
    'time': '10:30',
    'latitude': 28.6139,
    'longitude': 77.2090,
    'timezone': '+05:30'
}

print("Testing 5-year slow planet transits...")
print(f"Birth Data: {birth_data['date']} at {birth_data['time']}")
print(f"Location: {birth_data['latitude']}, {birth_data['longitude']}")
print("=" * 80)

calc = RealTransitCalculator()
transits = calc.get_slow_planet_transits(birth_data, years=5)

for planet, periods in transits.items():
    print(f"\n{planet.upper()} TRANSITS ({len(periods)} periods):")
    print("-" * 80)
    for period in periods:
        retrograde_flag = " [RETROGRADE RETURN]" if period['retrograde_return'] else ""
        print(f"  {period['start_date']} to {period['end_date']}")
        print(f"    Sign: {period['sign']} | House: {period['house']} | Segment: {period['segment']}{retrograde_flag}")

print("\n" + "=" * 80)
print(f"Total transit periods: {sum(len(p) for p in transits.values())}")

# Calculate total characters
json_output = json.dumps(transits, indent=2)
print(f"JSON size: {len(json_output)} characters ({len(json_output)/1024:.2f} KB)")
