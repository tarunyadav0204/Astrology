#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator
import swisseph as swe

def investigate_pada_issue():
    # Test data: 26th June 1975, 13:35, New Delhi
    birth_data = {
        'date': '1975-06-26',
        'time': '13:35',
        'timezone_offset': 5.5,  # IST
        'latitude': 28.6139,
        'longitude': 77.2090
    }
    
    calc = BPHSKalachakraCalculator()
    birth_jd = calc._parse_birth_jd(birth_data)
    
    # Get exact moon position
    pos_sidereal, flag = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)
    sidereal_lon = pos_sidereal[0] % 360.0
    
    print("=== INVESTIGATING PADA CALCULATION ISSUE ===")
    print(f"Sidereal Moon: {sidereal_lon:.8f}°")
    
    # Check if there's a different nakshatra start point
    # Some software might use different nakshatra boundaries
    
    # Standard calculation
    nak_span = 360.0 / 27.0  # 13.333333°
    nak_start_standard = 21 * nak_span  # Shravana starts at 21 * 13.333333 = 280°
    deg_in_nak_standard = sidereal_lon - nak_start_standard
    
    print(f"\nStandard method:")
    print(f"  Shravana starts at: {nak_start_standard:.6f}°")
    print(f"  Degrees in Shravana: {deg_in_nak_standard:.6f}°")
    
    # Check if moon is actually in previous nakshatra (Uttara Ashadha)
    if deg_in_nak_standard < 0:
        print("  *** Moon is in previous nakshatra! ***")
        deg_in_nak_standard += nak_span
        nak_number = 21  # Uttara Ashadha
    else:
        nak_number = 22  # Shravana
    
    # Alternative: Check if there's a different ayanamsa or calculation method
    print(f"\n=== TESTING DIFFERENT SCENARIOS ===")
    
    # Scenario 1: What if Gemini uses a different ayanamsa?
    # Let's see what happens with slightly different moon positions
    for offset in [-0.5, -0.25, 0, 0.25, 0.5]:
        test_lon = (sidereal_lon + offset) % 360.0
        test_nak_index = int(test_lon // nak_span)
        test_nak_number = test_nak_index + 1
        test_deg_in_nak = test_lon - (test_nak_index * nak_span)
        test_pada = int(test_deg_in_nak // (nak_span / 4.0)) + 1
        
        nakshatra_names = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
            "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
            "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
            "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
            "Uttara Bhadrapada", "Revati"
        ]
        
        if 1 <= test_nak_number <= 27:
            seq_data = calc._get_sequence(test_nak_number, test_pada)
            sequence = seq_data['seq']
            starting_sign = calc.SIGN_NAMES[sequence[0]]
            
            print(f"Offset {offset:+.2f}°: {nakshatra_names[test_nak_number-1]} Pada {test_pada} → {starting_sign}")
            if starting_sign == "Pisces":
                print(f"  *** MATCHES GEMINI! Moon at {test_lon:.6f}°, {test_deg_in_nak:.6f}° in nakshatra")
    
    # Scenario 2: What if there's a different pada numbering system?
    print(f"\n=== TESTING REVERSE PADA NUMBERING ===")
    # Some systems might number padas in reverse
    deg_in_nak = deg_in_nak_standard
    pada_span = nak_span / 4.0
    
    # Normal pada (1-4)
    normal_pada = int(deg_in_nak // pada_span) + 1
    
    # Reverse pada (4-1)
    reverse_pada = 4 - int(deg_in_nak // pada_span)
    
    print(f"Normal pada: {normal_pada}")
    print(f"Reverse pada: {reverse_pada}")
    
    for test_pada in [normal_pada, reverse_pada]:
        seq_data = calc._get_sequence(22, test_pada)  # Shravana
        sequence = seq_data['seq']
        starting_sign = calc.SIGN_NAMES[sequence[0]]
        print(f"  Pada {test_pada}: {starting_sign}")
        if starting_sign == "Pisces":
            print(f"    *** MATCHES GEMINI SOFTWARE! ***")
    
    # Scenario 3: Check exact degree boundaries
    print(f"\n=== EXACT DEGREE ANALYSIS ===")
    print(f"Moon at {deg_in_nak:.8f}° in Shravana")
    print(f"Pada boundaries:")
    for i in range(4):
        start_deg = i * pada_span
        end_deg = (i + 1) * pada_span
        print(f"  Pada {i+1}: {start_deg:.6f}° to {end_deg:.6f}°")
        if start_deg <= deg_in_nak < end_deg:
            print(f"    *** MOON IS HERE ***")

if __name__ == "__main__":
    investigate_pada_issue()