#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from panchang.muhurat_calculator import MuhuratCalculator
import swisseph as swe
from datetime import datetime

def test_muhurat():
    calc = MuhuratCalculator()
    
    # Test with a specific date and location
    date = "2024-01-15"
    lat = 28.6139  # Delhi
    lon = 77.2090
    
    print(f"Testing muhurat for {date} at {lat}, {lon}")
    
    try:
        result = calc.calculate_vivah_muhurat(date, lat, lon)
        
        print(f"Sunrise: {result.get('sunrise', 'N/A')}")
        print(f"Sunset: {result.get('sunset', 'N/A')}")
        print(f"Day duration: {result.get('day_duration_hours', 'N/A')} hours")
        print(f"Muhurta duration: {result.get('muhurta_duration_minutes', 'N/A')} minutes")
        print("\nMuhurtas:")
        
        for muhurta in result['muhurtas']:
            print(f"  {muhurta['name']}: {muhurta['start_time']} - {muhurta['end_time']} ({muhurta['duration_minutes']} min)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_muhurat()