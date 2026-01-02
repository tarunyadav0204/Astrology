#!/usr/bin/env python3
"""
Reverse engineer the correct Dasha calculation by working backwards from AstroSage result
AstroSage: Rahu Mahadasha ends Nov 4, 1995
Birth: April 2, 1980, 2:55 PM, Hisar
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import swisseph as swe

def reverse_engineer_calculation():
    # Known facts
    birth_datetime = datetime(1980, 4, 2, 14, 55)  # April 2, 1980, 2:55 PM
    astrosage_end = datetime(1995, 11, 4)  # Nov 4, 1995
    
    # Calculate total Rahu period from birth to AstroSage end
    total_days = (astrosage_end - birth_datetime).days
    print(f"=== REVERSE ENGINEERING FROM ASTROSAGE RESULT ===")
    print(f"Birth: {birth_datetime.strftime('%B %d, %Y at %H:%M')}")
    print(f"AstroSage Rahu end: {astrosage_end.strftime('%B %d, %Y')}")
    print(f"Total days: {total_days}")
    print()
    
    # Test different year lengths to see which gives 18 years
    year_lengths = [365, 365.25, 365.2422, 365.256363004]
    
    print("TESTING DIFFERENT YEAR LENGTHS:")
    for year_length in year_lengths:
        years = total_days / year_length
        print(f"  {year_length:12.6f} days/year = {years:.6f} years")
        if abs(years - 18) < 0.1:
            print(f"    *** CLOSE TO 18 YEARS! ***")
    print()
    
    # Calculate Moon position at birth
    birth_data = {
        'date': '1980-04-02',
        'time': '14:55',
        'timezone': 5.5
    }
    
    time_parts = birth_data['time'].split(':')
    hour = float(time_parts[0]) + float(time_parts[1])/60
    utc_hour = hour - birth_data['timezone']
    
    jd = swe.julday(1980, 4, 2, utc_hour)
    # Set Lahiri Ayanamsa for accurate Vedic calculations

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
    
    print(f"MOON ANALYSIS:")
    print(f"Moon position: {moon_pos:.6f}°")
    
    # Calculate nakshatra details
    nakshatra_index = int(moon_pos / 13.333333333333334)
    nakshatra_start = nakshatra_index * 13.333333333333334
    elapsed_degrees = moon_pos - nakshatra_start
    
    print(f"Nakshatra index: {nakshatra_index} (Swati)")
    print(f"Elapsed in nakshatra: {elapsed_degrees:.6f}°")
    print()
    
    # Work backwards to find what balance fraction gives us Nov 4, 1995
    print("REVERSE CALCULATING BALANCE FRACTION:")
    
    for year_length in [365.25, 365.2422]:
        required_years = total_days / year_length
        balance_fraction = required_years / 18.0
        
        # Calculate what elapsed degrees this would require
        required_elapsed = (1 - balance_fraction) * 13.333333333333334
        required_moon_pos = nakshatra_start + required_elapsed
        
        print(f"Year length {year_length}:")
        print(f"  Required years: {required_years:.6f}")
        print(f"  Balance fraction: {balance_fraction:.6f}")
        print(f"  Required elapsed: {required_elapsed:.6f}°")
        print(f"  Required Moon pos: {required_moon_pos:.6f}°")
        print(f"  Actual Moon pos: {moon_pos:.6f}°")
        print(f"  Difference: {abs(required_moon_pos - moon_pos):.6f}°")
        print()
    
    # Test if there's a different nakshatra calculation method
    print("TESTING ALTERNATIVE NAKSHATRA DIVISIONS:")
    
    # Test exact 13.333333... vs other divisions
    divisions = [
        (13.333333333333334, "Standard (13.333333...)"),
        (13.33333333, "Rounded (13.33333333)"),
        (800/60, "Exact (800'/60)"),
        (40/3, "Fraction (40/3)")
    ]
    
    for division, name in divisions:
        nak_index = int(moon_pos / division)
        nak_start = nak_index * division
        elapsed = moon_pos - nak_start
        balance = 1 - (elapsed / division)
        years = 18 * balance
        end_date = birth_datetime + timedelta(days=years * 365.25)
        
        print(f"{name:20s}: Balance {balance:.6f}, End {end_date.strftime('%b %d, %Y')}")
        if abs((end_date - astrosage_end).days) < 10:
            print(f"    *** CLOSE MATCH! Difference: {(end_date - astrosage_end).days} days ***")
    
    print()
    
    # Test if there's a time zone or time calculation issue
    print("TESTING TIME VARIATIONS:")
    
    # Test different birth times around 2:55 PM
    base_time = datetime(1980, 4, 2, 14, 55)
    
    for minutes_offset in [-30, -15, -5, 0, 5, 15, 30]:
        test_time = base_time + timedelta(minutes=minutes_offset)
        test_hour = test_time.hour + test_time.minute/60
        test_utc_hour = test_hour - 5.5
        
        test_jd = swe.julday(1980, 4, 2, test_utc_hour)
        test_moon_pos = swe.calc_ut(test_jd, 1, swe.FLG_SIDEREAL)[0][0]
        
        test_nak_index = int(test_moon_pos / 13.333333333333334)
        test_nak_start = test_nak_index * 13.333333333333334
        test_elapsed = test_moon_pos - test_nak_start
        test_balance = 1 - (test_elapsed / 13.333333333333334)
        test_years = 18 * test_balance
        test_end = base_time + timedelta(days=test_years * 365.25)
        
        time_str = test_time.strftime('%H:%M')
        print(f"Time {time_str}: Moon {test_moon_pos:.4f}°, End {test_end.strftime('%b %d, %Y')}")
        
        if abs((test_end - astrosage_end).days) < 7:
            print(f"    *** MATCH! Difference: {(test_end - astrosage_end).days} days ***")

if __name__ == "__main__":
    reverse_engineer_calculation()