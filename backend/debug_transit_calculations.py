#!/usr/bin/env python3
"""
Debug script to test the exact same calculation logic as the backend API
"""

import swisseph as swe
from datetime import datetime
import json

def calculate_transits_debug(transit_date=None):
    """
    Replicate the exact logic from the backend calculate_transits function
    """
    if transit_date is None:
        transit_date = datetime.now().strftime('%Y-%m-%d')
    
    # Parse date (same as backend)
    date_parts = transit_date.split('-')
    jd = swe.julday(
        int(date_parts[0]),
        int(date_parts[1]), 
        int(date_parts[2]),
        12.0
    )
    
    print(f"Calculating transits for: {transit_date}")
    print(f"Julian Day: {jd}")
    
    # Set Lahiri Ayanamsa (same as backend)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Calculate transit planetary positions (exact backend logic)
    planets = {}
    planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    
    for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):  # Swiss Ephemeris planet numbers
        if planet <= 6:  # Regular planets
            # CRITICAL: Add FLG_SWIEPH for high-precision Swiss Ephemeris (not Moshier)
            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH)
        else:  # Lunar nodes - always use mean for transits
            pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH)
        
        pos_array = pos[0]
        longitude = pos_array[0]
        
        # Use index 3 for speed (standard Swiss Ephemeris)
        speed = pos_array[3] if len(pos_array) > 3 else 0.0
        
        if planet == 12:  # Ketu - add 180 degrees to Rahu
            longitude = (longitude + 180) % 360
        
        is_retrograde = speed < 0 if planet <= 6 else False
        
        planets[planet_names[i]] = {
            'longitude': longitude,
            'sign': int(longitude / 30),
            'degree': longitude % 30,
            'retrograde': is_retrograde
        }
    
    return planets

def main():
    """Main test function"""
    
    print("="*80)
    print("DEBUGGING TRANSIT CALCULATIONS")
    print("="*80)
    
    # Test current date
    current_planets = calculate_transits_debug()
    
    sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    print("\nCURRENT PLANETARY TRANSITS (Backend Logic):")
    print("-" * 60)
    
    for planet, data in current_planets.items():
        sign_name = sign_names[data['sign']]
        retro_symbol = " ℞" if data['retrograde'] else ""
        
        print(f"{planet:8} | {sign_name:12} | {data['degree']:6.2f}°{retro_symbol}")
    
    # Test a few specific dates to see if there are any obvious errors
    test_dates = [
        '2025-01-01',  # New Year
        '2025-06-21',  # Summer Solstice
        '2025-12-21'   # Winter Solstice
    ]
    
    print("\n" + "="*80)
    print("TESTING SPECIFIC DATES")
    print("="*80)
    
    for test_date in test_dates:
        print(f"\nDate: {test_date}")
        print("-" * 40)
        
        test_planets = calculate_transits_debug(test_date)
        
        for planet, data in test_planets.items():
            sign_name = sign_names[data['sign']]
            print(f"{planet:8} | {sign_name:12} | {data['degree']:6.2f}°")
    
    # Save current results for comparison
    result_data = {
        'timestamp': datetime.now().isoformat(),
        'current_date': datetime.now().strftime('%Y-%m-%d'),
        'planets': current_planets
    }
    
    with open('debug_transit_results.json', 'w') as f:
        json.dump(result_data, f, indent=2)
    
    print(f"\n✅ Results saved to: debug_transit_results.json")
    
    # Instructions for verification
    print("\n" + "="*80)
    print("VERIFICATION INSTRUCTIONS")
    print("="*80)
    print("1. Compare these positions with:")
    print("   - Astro.com (set Ayanamsa to 'Lahiri')")
    print("   - Jagannatha Hora software")
    print("   - Any other Vedic astrology app")
    print()
    print("2. If positions are WRONG, possible issues:")
    print("   - Mobile app is caching old data")
    print("   - API is not being called correctly")
    print("   - Time zone conversion issues")
    print("   - User's birth data is affecting transit calculation")
    print()
    print("3. If positions are CORRECT, the issue is likely:")
    print("   - Mobile app display bug")
    print("   - API response formatting issue")
    print("   - Frontend sign mapping error")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()