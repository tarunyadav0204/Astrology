#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.dasha_calculator import DashaCalculator
from datetime import datetime

# Test data
birth_data = {
    "name": "Ruchi",
    "date": "1978-06-02",
    "time": "03:50:00",
    "latitude": 26.8651375,
    "longitude": 75.7119952,
    "timezone": "UTC+5:30",
    "place": "Jaipur, Rajasthan, India"
}

target_date = datetime(2025, 12, 5)

print("Testing DashaCalculator...")
print(f"Birth data: {birth_data}")
print(f"Target date: {target_date}")

calculator = DashaCalculator()

try:
    result = calculator.calculate_current_dashas(birth_data, target_date)
    print(f"\nResult keys: {list(result.keys())}")
    print(f"Maha dashas count: {len(result.get('maha_dashas', []))}")
    
    if result.get('maha_dashas'):
        print(f"First maha dasha: {result['maha_dashas'][0]}")
    else:
        print("No maha dashas returned")
        
    print(f"Current mahadasha: {result.get('mahadasha', {})}")
    print(f"Moon nakshatra: {result.get('moon_nakshatra', 'N/A')}")
    print(f"Moon lord: {result.get('moon_lord', 'N/A')}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()