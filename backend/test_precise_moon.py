#!/usr/bin/env python3
"""
Precise test to find the exact Moon position that gives AstroSage's Nov 4, 1995 result
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.dasha_calculator import DashaCalculator
from datetime import datetime, timedelta
import swisseph as swe

def test_exact_moon_position():
    birth_data = {
        'date': '1980-04-02',
        'time': '14:55',
        'latitude': 29.1492,
        'longitude': 75.7217,
        'timezone': 5.5
    }
    
    print("=== FINDING EXACT MOON POSITION FOR ASTROSAGE MATCH ===")
    
    # AstroSage target: Nov 4, 1995
    astrosage_target = datetime(1995, 11, 4)
    birth_datetime = datetime(1980, 4, 2, 14, 55)
    
    # Calculate what Moon position would give us Nov 4, 1995
    target_days = (astrosage_target - birth_datetime).days
    target_years = target_days / 365.25
    target_balance = target_years / 18.0
    
    print(f"Target end date: {astrosage_target.strftime('%B %d, %Y')}")
    print(f"Target days: {target_days}")
    print(f"Target years: {target_years:.6f}")
    print(f"Target balance fraction: {target_balance:.6f}")
    
    # Calculate what elapsed degrees this requires
    target_elapsed = (1 - target_balance) * 13.333333333333334
    
    # Swati starts at 186.666667°
    nakshatra_start = 14 * 13.333333333333334  # Swati is 15th nakshatra (index 14)
    target_moon_pos = nakshatra_start + target_elapsed
    
    print(f"Target elapsed in nakshatra: {target_elapsed:.6f}°")
    print(f"Target Moon position: {target_moon_pos:.6f}°")
    
    # Now test our calculator with different Moon positions
    calculator = DashaCalculator()
    
    print(f"\n=== TESTING DIFFERENT MOON POSITIONS ===")
    
    # Test a range around the target
    for offset in [-0.02, -0.01, -0.005, 0, 0.005, 0.01, 0.02]:
        test_moon_pos = target_moon_pos + offset
        
        # Calculate what this gives us
        test_nakshatra_index = int(test_moon_pos / 13.333333333333334)
        test_nakshatra_start = test_nakshatra_index * 13.333333333333334
        test_elapsed = test_moon_pos - test_nakshatra_start
        test_balance = 1 - (test_elapsed / 13.333333333333334)
        test_years = 18 * test_balance
        test_end = birth_datetime + timedelta(days=test_years * 365.25)
        
        diff_days = (test_end - astrosage_target).days
        
        print(f"Moon {test_moon_pos:8.4f}°: Balance {test_balance:.6f}, End {test_end.strftime('%b %d, %Y')}, Diff {diff_days:+3d} days")
        
        if abs(diff_days) <= 1:
            print(f"  *** CLOSE MATCH! ***")
    
    # Test our actual calculator
    print(f"\n=== OUR CALCULATOR RESULT ===")
    dashas = calculator.calculate_current_dashas(birth_data)
    
    if dashas['maha_dashas']:
        first_dasha = dashas['maha_dashas'][0]
        print(f"Our calculator: {first_dasha['planet']} ends {first_dasha['end'].strftime('%B %d, %Y')}")
        our_diff = (first_dasha['end'] - astrosage_target).days
        print(f"Difference from AstroSage: {our_diff:+d} days")
    
    # Calculate actual Moon position used by our calculator
    time_parts = birth_data['time'].split(':')
    hour = float(time_parts[0]) + float(time_parts[1])/60
    utc_hour = hour - birth_data['timezone']
    jd = swe.julday(1980, 4, 2, utc_hour)
    
    # Test both Ayanamsa modes
    print(f"\n=== AYANAMSA COMPARISON ===")
    
    for mode, name in [(0, "Lahiri"), (27, "True Chitra")]:
        swe.set_sid_mode(mode, 0, 0)
        moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
        
        nakshatra_index = int(moon_pos / 13.333333333333334)
        nakshatra_start = nakshatra_index * 13.333333333333334
        elapsed = moon_pos - nakshatra_start
        balance = 1 - (elapsed / 13.333333333333334)
        years = 18 * balance
        end_date = birth_datetime + timedelta(days=years * 365.25)
        
        diff_days = (end_date - astrosage_target).days
        
        print(f"{name:12s} (Mode {mode:2d}): Moon {moon_pos:8.4f}°, End {end_date.strftime('%b %d, %Y')}, Diff {diff_days:+3d} days")

if __name__ == "__main__":
    test_exact_moon_position()