#!/usr/bin/env python3
"""
Test script to investigate Dasha calculation differences
Birth: April 2, 1980, 2:55 PM, Hisar
Our app: Rahu Mahadasha ends Oct 29, 1995
AstroSage: Rahu Mahadasha ends Nov 4, 1995
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.dasha_calculator import DashaCalculator
from datetime import datetime
import swisseph as swe

def test_dasha_calculation():
    # Birth details
    birth_data = {
        'date': '1980-04-02',
        'time': '14:55',  # 2:55 PM
        'place': 'Hisar',
        'latitude': 29.1492,
        'longitude': 75.7217,
        'timezone': 5.5  # IST
    }
    
    print("=== DASHA CALCULATION ANALYSIS ===")
    print(f"Birth: {birth_data['date']} at {birth_data['time']} in {birth_data['place']}")
    print(f"Coordinates: {birth_data['latitude']}°N, {birth_data['longitude']}°E")
    print()
    
    # Calculate Moon position at birth
    time_parts = birth_data['time'].split(':')
    hour = float(time_parts[0]) + float(time_parts[1])/60
    utc_hour = hour - birth_data['timezone']
    
    jd = swe.julday(1980, 4, 2, utc_hour)
    # Set Lahiri Ayanamsa for accurate Vedic calculations

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
    
    print(f"Moon position at birth: {moon_pos:.6f}°")
    
    # Calculate nakshatra
    nakshatra_index = int(moon_pos / 13.333333333333334)
    nakshatra_start = nakshatra_index * 13.333333333333334
    elapsed_degrees = moon_pos - nakshatra_start
    
    nakshatra_names = [
        'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
        'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
        'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
        'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
        'Uttara Bhadrapada', 'Revati'
    ]
    
    nakshatra_lords = [
        'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',
        'Saturn', 'Mercury', 'Ketu', 'Venus', 'Sun', 'Moon', 'Mars',
        'Rahu', 'Jupiter', 'Saturn', 'Mercury', 'Ketu', 'Venus',
        'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
    ]
    
    print(f"Nakshatra: {nakshatra_names[nakshatra_index]} ({nakshatra_index + 1})")
    print(f"Nakshatra lord: {nakshatra_lords[nakshatra_index]}")
    print(f"Elapsed in nakshatra: {elapsed_degrees:.6f}° out of 13.333333°")
    
    # Calculate balance of first dasha
    balance_fraction = 1 - (elapsed_degrees / 13.333333333333334)
    print(f"Balance fraction: {balance_fraction:.6f}")
    
    # Rahu dasha period is 18 years
    rahu_total_years = 18
    rahu_balance_years = rahu_total_years * balance_fraction
    
    print(f"Rahu Mahadasha total period: {rahu_total_years} years")
    print(f"Rahu Mahadasha balance at birth: {rahu_balance_years:.6f} years")
    print(f"Rahu Mahadasha balance in days: {rahu_balance_years * 365.25:.2f} days")
    
    # Calculate end date
    birth_datetime = datetime(1980, 4, 2, 14, 55)
    from datetime import timedelta
    
    # Method 1: Using exact days
    rahu_end_date1 = birth_datetime + timedelta(days=rahu_balance_years * 365.25)
    print(f"\nMethod 1 (365.25 days/year): Rahu ends on {rahu_end_date1.strftime('%B %d, %Y at %H:%M')}")
    
    # Method 2: Using 365.2422 days (tropical year)
    rahu_end_date2 = birth_datetime + timedelta(days=rahu_balance_years * 365.2422)
    print(f"Method 2 (365.2422 days/year): Rahu ends on {rahu_end_date2.strftime('%B %d, %Y at %H:%M')}")
    
    # Method 3: Using our calculator
    calculator = DashaCalculator()
    dashas = calculator.calculate_current_dashas(birth_data)
    
    print(f"\nOur calculator results:")
    print(f"Moon nakshatra: {dashas['moon_nakshatra']}")
    print(f"Moon lord: {dashas['moon_lord']}")
    
    # Find Rahu mahadasha in the sequence
    for i, maha in enumerate(dashas['maha_dashas']):
        print(f"Mahadasha {i+1}: {maha['planet']} from {maha['start'].strftime('%b %d, %Y')} to {maha['end'].strftime('%b %d, %Y')} ({maha['years']:.2f} years)")
        if maha['planet'] == 'Rahu':
            print(f"  *** RAHU MAHADASHA ENDS: {maha['end'].strftime('%B %d, %Y at %H:%M:%S')} ***")
    
    print(f"\n=== COMPARISON ===")
    print(f"Our app result: October 29, 1995")
    print(f"AstroSage result: November 4, 1995")
    print(f"Difference: ~6 days")
    
    # Test different calculation methods
    print(f"\n=== TESTING DIFFERENT METHODS ===")
    
    # Test with different year lengths
    for year_length, name in [(365, "365 days"), (365.25, "365.25 days"), (365.2422, "365.2422 days"), (365.256363004, "sidereal year")]:
        end_date = birth_datetime + timedelta(days=rahu_balance_years * year_length)
        print(f"{name:15}: {end_date.strftime('%B %d, %Y at %H:%M')}")
    
    # Check if there's a timezone issue
    print(f"\n=== TIMEZONE ANALYSIS ===")
    print(f"Birth time used: {birth_data['time']} IST")
    print(f"UTC time: {utc_hour:.2f} hours = {int(utc_hour)}:{int((utc_hour % 1) * 60):02d}")
    
    # Test with slightly different Moon positions
    print(f"\n=== SENSITIVITY ANALYSIS ===")
    for offset in [-0.01, -0.005, 0, 0.005, 0.01]:
        test_moon_pos = moon_pos + offset
        test_nakshatra_index = int(test_moon_pos / 13.333333333333334)
        test_nakshatra_start = test_nakshatra_index * 13.333333333333334
        test_elapsed = test_moon_pos - test_nakshatra_start
        test_balance = 1 - (test_elapsed / 13.333333333333334)
        test_years = 18 * test_balance
        test_end = birth_datetime + timedelta(days=test_years * 365.25)
        print(f"Moon {moon_pos + offset:8.4f}°: Balance {test_balance:.6f}, End {test_end.strftime('%b %d, %Y')}")

if __name__ == "__main__":
    test_dasha_calculation()