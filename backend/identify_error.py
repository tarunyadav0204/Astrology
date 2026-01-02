#!/usr/bin/env python3
"""
Identify the exact calculation error in our Dasha system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import swisseph as swe

def identify_calculation_error():
    birth_datetime = datetime(1980, 4, 2, 14, 55)
    correct_rahu_end = datetime(1995, 11, 4)
    
    print("=== IDENTIFYING CALCULATION ERROR ===")
    print(f"Birth: {birth_datetime}")
    print(f"Correct Rahu end: {correct_rahu_end}")
    print()
    
    # Calculate Moon position
    hour = 14 + 55/60
    utc_hour = hour - 5.5
    jd = swe.julday(1980, 4, 2, utc_hour)
    moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
    
    print(f"Moon position: {moon_pos:.6f}°")
    
    # Our current calculation
    nakshatra_index = int(moon_pos / 13.333333333333334)
    nakshatra_start = nakshatra_index * 13.333333333333334
    elapsed_degrees = moon_pos - nakshatra_start
    our_balance_fraction = 1 - (elapsed_degrees / 13.333333333333334)
    
    print(f"Nakshatra index: {nakshatra_index} (Swati)")
    print(f"Nakshatra start: {nakshatra_start:.6f}°")
    print(f"Elapsed degrees: {elapsed_degrees:.6f}°")
    print(f"Our balance fraction: {our_balance_fraction:.6f}")
    
    our_years = 18 * our_balance_fraction
    our_end_date = birth_datetime + timedelta(days=our_years * 365.25)
    
    print(f"Our calculated years: {our_years:.6f}")
    print(f"Our end date: {our_end_date}")
    print()
    
    # What should the balance fraction be for correct result?
    total_days_correct = (correct_rahu_end - birth_datetime).days
    correct_years = total_days_correct / 365.25
    correct_balance_fraction = correct_years / 18
    
    print(f"Correct total days: {total_days_correct}")
    print(f"Correct years: {correct_years:.6f}")
    print(f"Correct balance fraction: {correct_balance_fraction:.6f}")
    print()
    
    # What elapsed degrees would give us the correct balance?
    correct_elapsed = (1 - correct_balance_fraction) * 13.333333333333334
    correct_moon_pos = nakshatra_start + correct_elapsed
    
    print(f"Required elapsed degrees: {correct_elapsed:.6f}°")
    print(f"Required Moon position: {correct_moon_pos:.6f}°")
    print(f"Actual Moon position: {moon_pos:.6f}°")
    print(f"Difference: {abs(correct_moon_pos - moon_pos):.6f}°")
    print()
    
    # The issue might be in the nakshatra calculation
    # Let's check if there's a different way to calculate nakshatra boundaries
    
    print("TESTING DIFFERENT NAKSHATRA CALCULATION METHODS:")
    print()
    
    # Method 1: Our current method (360° / 27 = 13.333333...)
    method1_size = 360 / 27
    print(f"Method 1 - Simple division: {method1_size:.10f}° per nakshatra")
    
    # Method 2: Exact fraction (40/3)
    method2_size = 40/3
    print(f"Method 2 - Exact fraction (40/3): {method2_size:.10f}° per nakshatra")
    
    # Method 3: Minutes-based (800 minutes / 60)
    method3_size = 800/60
    print(f"Method 3 - Minutes (800'/60): {method3_size:.10f}° per nakshatra")
    
    print()
    
    # Test each method
    for i, (size, name) in enumerate([(method1_size, "Simple"), (method2_size, "Fraction"), (method3_size, "Minutes")], 1):
        nak_index = int(moon_pos / size)
        nak_start = nak_index * size
        elapsed = moon_pos - nak_start
        balance = 1 - (elapsed / size)
        years = 18 * balance
        end_date = birth_datetime + timedelta(days=years * 365.25)
        
        print(f"Method {i} ({name}):")
        print(f"  Nakshatra size: {size:.10f}°")
        print(f"  Balance: {balance:.6f}")
        print(f"  Years: {years:.6f}")
        print(f"  End date: {end_date.strftime('%b %d, %Y')}")
        print(f"  Difference from correct: {(end_date - correct_rahu_end).days} days")
        print()
    
    # Check if the issue is with Ayanamsa
    print("TESTING DIFFERENT AYANAMSA VALUES:")
    
    # Our current uses Lahiri, but let's test slight variations
    ayanamsa_variations = [
        (swe.SIDM_LAHIRI, "Lahiri"),
        (swe.SIDM_RAMAN, "Raman"),
        (swe.SIDM_KRISHNAMURTI, "KP"),
    ]
    
    for ayanamsa_id, name in ayanamsa_variations:
        swe.set_sid_mode(ayanamsa_id)
        test_moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
        
        test_nak_index = int(test_moon_pos / 13.333333333333334)
        test_nak_start = test_nak_index * 13.333333333333334
        test_elapsed = test_moon_pos - test_nak_start
        test_balance = 1 - (test_elapsed / 13.333333333333334)
        test_years = 18 * test_balance
        test_end = birth_datetime + timedelta(days=test_years * 365.25)
        
        print(f"{name:15s}: Moon {test_moon_pos:.4f}°, End {test_end.strftime('%b %d, %Y')}, Diff {(test_end - correct_rahu_end).days:4d} days")
    
    # Reset to Lahiri
    swe.set_sid_mode(swe.SIDM_LAHIRI)

if __name__ == "__main__":
    identify_calculation_error()