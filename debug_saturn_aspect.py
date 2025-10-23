#!/usr/bin/env python3
"""Debug Saturn 3rd house aspect calculation for Nov 18, 2005"""

import swisseph as swe
from datetime import datetime

def debug_saturn_aspect():
    """Debug Saturn's position and aspect calculation for Nov 18, 2005"""
    
    # Set Lahiri Ayanamsa
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Test date: Nov 18, 2005
    test_date = datetime(2005, 11, 18, 12, 0, 0)
    jd = swe.julday(test_date.year, test_date.month, test_date.day, 12.0)
    
    print(f"=== DEBUGGING SATURN ASPECT FOR {test_date.strftime('%Y-%m-%d')} ===")
    
    # Calculate Saturn's position
    result = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)
    saturn_longitude = result[0][0]
    saturn_sign = int(saturn_longitude / 30)
    
    print(f"Saturn longitude: {saturn_longitude:.2f}°")
    print(f"Saturn sign: {saturn_sign} (0=Aries, 1=Taurus, etc.)")
    print(f"Saturn degree in sign: {saturn_longitude % 30:.2f}°")
    
    # Test with different ascendant signs to find which gives 12th house placement
    print(f"\n=== TESTING HOUSE PLACEMENTS ===")
    for asc_sign in range(12):
        saturn_house = ((saturn_sign - asc_sign) % 12) + 1
        print(f"Ascendant in sign {asc_sign}: Saturn in house {saturn_house}")
        
        if saturn_house == 12:
            print(f"*** FOUND: With ascendant in sign {asc_sign}, Saturn is in 12th house ***")
            
            # Now test the aspect calculation
            natal_saturn_house = 2  # Given: natal Saturn in 2nd house
            
            # Calculate aspect
            house_diff = (natal_saturn_house - saturn_house + 12) % 12
            aspect_number = 1 if house_diff == 0 else house_diff + 1
            
            print(f"Transit Saturn house: {saturn_house}")
            print(f"Natal Saturn house: {natal_saturn_house}")
            print(f"House difference: ({natal_saturn_house} - {saturn_house} + 12) % 12 = {house_diff}")
            print(f"Aspect number: {aspect_number}")
            
            # Check if Saturn can make this aspect
            saturn_aspects = [1, 3, 7, 10]
            can_make_aspect = aspect_number in saturn_aspects
            
            print(f"Saturn can make aspects: {saturn_aspects}")
            print(f"Can make {aspect_number}th aspect: {can_make_aspect}")
            
            if can_make_aspect and aspect_number == 3:
                print(f"✓ VALID: Saturn 3rd house aspect from house {saturn_house} to house {natal_saturn_house}")
            else:
                print(f"✗ INVALID: Saturn cannot make {aspect_number}th aspect")
    
    print(f"\n=== SIGN NAMES FOR REFERENCE ===")
    sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    print(f"Saturn is in {sign_names[saturn_sign]} ({saturn_sign})")

if __name__ == "__main__":
    debug_saturn_aspect()