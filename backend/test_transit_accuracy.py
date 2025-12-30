#!/usr/bin/env python3
"""
Test script to verify transit calculations accuracy
"""

import swisseph as swe
from datetime import datetime
import json

def test_current_transits():
    """Test current planetary transits for accuracy"""
    
    # Set Lahiri Ayanamsa (same as backend)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Current date
    current_date = datetime.now()
    jd = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)
    
    print(f"Testing transits for: {current_date.strftime('%Y-%m-%d')}")
    print(f"Julian Day: {jd}")
    
    # Get Ayanamsa
    ayanamsa = swe.get_ayanamsa_ut(jd)
    print(f"Lahiri Ayanamsa: {ayanamsa:.6f}°")
    
    planets = {}
    planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    
    for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):  # Swiss Ephemeris planet numbers
        if planet <= 6:  # Regular planets
            # Use high-precision Swiss Ephemeris with sidereal mode
            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH)
        else:  # Lunar nodes - always use mean for transits
            pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH)
        
        pos_array = pos[0]
        longitude = pos_array[0]
        speed = pos_array[3] if len(pos_array) > 3 else 0.0
        
        if planet == 12:  # Ketu - add 180 degrees to Rahu
            longitude = (longitude + 180) % 360
        
        is_retrograde = speed < 0 if planet <= 6 else False
        
        # Calculate tropical position for comparison
        if planet <= 6:
            tropical_pos = swe.calc_ut(jd, planet, swe.FLG_SPEED | swe.FLG_SWIEPH)
        else:
            tropical_pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SPEED | swe.FLG_SWIEPH)
        
        tropical_longitude = tropical_pos[0][0]
        if planet == 12:  # Ketu
            tropical_longitude = (tropical_longitude + 180) % 360
        
        planets[planet_names[i]] = {
            'sidereal_longitude': longitude,
            'tropical_longitude': tropical_longitude,
            'sign': int(longitude / 30),
            'degree': longitude % 30,
            'retrograde': is_retrograde,
            'speed': speed
        }
    
    # Print results
    sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    print("\n" + "="*80)
    print("CURRENT PLANETARY TRANSITS (Sidereal - Lahiri Ayanamsa)")
    print("="*80)
    
    for planet, data in planets.items():
        sign_name = sign_names[data['sign']]
        retro_symbol = " ℞" if data['retrograde'] else ""
        
        print(f"{planet:8} | {sign_name:12} | {data['degree']:6.2f}° | Speed: {data['speed']:7.4f}°/day{retro_symbol}")
        
        # Show difference between tropical and sidereal
        tropical_sign = int(data['tropical_longitude'] / 30)
        tropical_degree = data['tropical_longitude'] % 30
        tropical_sign_name = sign_names[tropical_sign]
        
        print(f"         | Tropical: {tropical_sign_name:12} | {tropical_degree:6.2f}° | Diff: {ayanamsa:6.2f}°")
        print("-" * 80)
    
    return planets

def compare_with_known_ephemeris():
    """Compare with known ephemeris data for verification"""
    print("\n" + "="*80)
    print("VERIFICATION NOTES:")
    print("="*80)
    print("1. Check these positions against:")
    print("   - Astro.com (use Lahiri Ayanamsa)")
    print("   - Jagannatha Hora")
    print("   - Any other Vedic astrology software")
    print()
    print("2. The difference between Tropical and Sidereal should be ~24°")
    print("   (current Lahiri Ayanamsa value)")
    print()
    print("3. If positions are wrong, possible issues:")
    print("   - Wrong Ayanamsa setting")
    print("   - Using Moshier instead of Swiss Ephemeris")
    print("   - Incorrect sidereal flag usage")
    print("   - Time zone issues")

if __name__ == "__main__":
    try:
        planets = test_current_transits()
        compare_with_known_ephemeris()
        
        # Save results to file for comparison
        with open('transit_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'planets': planets
            }, f, indent=2)
        
        print(f"\nResults saved to: transit_test_results.json")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()