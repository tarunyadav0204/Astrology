#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator
import swisseph as swe

def check_pada_methods():
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
    
    # Get sidereal moon position
    pos_sidereal, flag = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)
    sidereal_lon = pos_sidereal[0] % 360.0
    
    print("=== PADA CALCULATION METHODS ===")
    print(f"Sidereal Moon: {sidereal_lon:.6f}°")
    
    # Method 1: Our current method
    nak_span = 360.0 / 27.0  # 13.333...°
    nak_index = int(sidereal_lon // nak_span)
    nak_number = nak_index + 1
    deg_in_nak = sidereal_lon - (nak_index * nak_span)
    pada_span = nak_span / 4.0  # 3.333...°
    pada_method1 = int(deg_in_nak // pada_span) + 1
    
    print(f"\nMethod 1 (Our current):")
    print(f"  Nakshatra span: {nak_span:.6f}°")
    print(f"  Degrees in nakshatra: {deg_in_nak:.6f}°")
    print(f"  Pada span: {pada_span:.6f}°")
    print(f"  Pada calculation: int({deg_in_nak:.6f} / {pada_span:.6f}) + 1 = {pada_method1}")
    
    # Method 2: Alternative rounding
    pada_method2 = min(4, int(deg_in_nak / pada_span) + 1)
    print(f"\nMethod 2 (With min constraint):")
    print(f"  Pada: min(4, int({deg_in_nak:.6f} / {pada_span:.6f}) + 1) = {pada_method2}")
    
    # Method 3: Different boundary handling
    if deg_in_nak == 0:
        pada_method3 = 1
    else:
        pada_method3 = min(4, int((deg_in_nak - 0.000001) / pada_span) + 1)
    print(f"\nMethod 3 (Boundary adjustment):")
    print(f"  Pada: {pada_method3}")
    
    # Method 4: Check if close to boundary
    boundary_tolerance = 0.01  # 1 arcminute
    pada_boundaries = [0, pada_span, 2*pada_span, 3*pada_span, nak_span]
    
    print(f"\nPada boundaries:")
    for i, boundary in enumerate(pada_boundaries):
        if i < 4:
            print(f"  Pada {i+1}: {boundary:.6f}° to {pada_boundaries[i+1]:.6f}°")
            if abs(deg_in_nak - boundary) < boundary_tolerance:
                print(f"    *** CLOSE TO BOUNDARY! Difference: {abs(deg_in_nak - boundary):.6f}°")
    
    # Test what happens if we're in different padas
    print(f"\n=== TESTING ALL PADA RESULTS ===")
    for test_pada in [1, 2, 3, 4]:
        seq_data = calc._get_sequence(22, test_pada)  # Shravana
        sequence = seq_data['seq']
        starting_sign = calc.SIGN_NAMES[sequence[0]]
        print(f"Pada {test_pada}: {starting_sign}")
        if starting_sign == "Pisces":
            print(f"  *** MATCHES GEMINI SOFTWARE! ***")
    
    # Check if there's a different nakshatra interpretation
    print(f"\n=== CHECKING ADJACENT NAKSHATRAS ===")
    for nak_offset in [-1, 0, 1]:
        test_nak = 22 + nak_offset
        if 1 <= test_nak <= 27:
            nakshatra_names = [
                "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
                "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
                "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
                "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
                "Uttara Bhadrapada", "Revati"
            ]
            print(f"Nakshatra {test_nak} ({nakshatra_names[test_nak-1]}):")
            for test_pada in [1, 2, 3, 4]:
                seq_data = calc._get_sequence(test_nak, test_pada)
                sequence = seq_data['seq']
                starting_sign = calc.SIGN_NAMES[sequence[0]]
                print(f"  Pada {test_pada}: {starting_sign}")
                if starting_sign == "Pisces":
                    print(f"    *** MATCHES GEMINI SOFTWARE! ***")

if __name__ == "__main__":
    check_pada_methods()