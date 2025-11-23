#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator
import swisseph as swe

def verify_nakshatra_calculation():
    # Test data: 26th June 1975, 13:35, New Delhi
    birth_data = {
        'date': '1975-06-26',
        'time': '13:35',
        'timezone_offset': 5.5,  # IST
        'latitude': 28.6139,
        'longitude': 77.2090
    }
    
    calc = BPHSKalachakraCalculator()
    
    # Manual calculation
    birth_jd = calc._parse_birth_jd(birth_data)
    
    # Check both tropical and sidereal moon positions
    pos_tropical, flag = swe.calc_ut(birth_jd, swe.MOON, 0)  # Tropical
    pos_sidereal, flag = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)  # Sidereal
    
    print("=== MOON POSITION VERIFICATION ===")
    print(f"Tropical Moon: {pos_tropical[0]:.6f}°")
    print(f"Sidereal Moon: {pos_sidereal[0]:.6f}°")
    print(f"Ayanamsa: {pos_tropical[0] - pos_sidereal[0]:.6f}°")
    
    # Manual nakshatra calculation
    sidereal_lon = pos_sidereal[0] % 360.0
    nak_span = 360.0 / 27.0  # 13.333...°
    nak_index = int(sidereal_lon // nak_span)
    nak_number = nak_index + 1
    deg_in_nak = sidereal_lon - (nak_index * nak_span)
    pada = int(deg_in_nak // (nak_span / 4.0)) + 1
    
    nakshatra_names = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
        "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
        "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
        "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
        "Uttara Bhadrapada", "Revati"
    ]
    
    print(f"\n=== NAKSHATRA DETAILS ===")
    print(f"Nakshatra number: {nak_number}")
    print(f"Nakshatra name: {nakshatra_names[nak_index]}")
    print(f"Pada: {pada}")
    print(f"Degrees in nakshatra: {deg_in_nak:.6f}°")
    
    # Check our classification
    print(f"\n=== SAVYA/APASAVYA CHECK ===")
    print(f"Our SAVYA_NAKSHATRAS: {sorted(calc.SAVYA_NAKSHATRAS)}")
    is_savya = nak_number in calc.SAVYA_NAKSHATRAS
    print(f"Nakshatra {nak_number} ({nakshatra_names[nak_index]}) is {'Savya' if is_savya else 'Apasavya'}")
    
    # Check sequence selection
    print(f"\n=== SEQUENCE SELECTION ===")
    if is_savya:
        print("Using SAVYA sequences:")
        for i, seq in calc.SEQUENCES_SAVYA.items():
            print(f"  Pada {i}: {[calc.SIGN_NAMES[s] for s in seq]}")
        selected_seq = calc.SEQUENCES_SAVYA[pada]
    else:
        print("Using APASAVYA sequences:")
        for i, seq in calc.SEQUENCES_APASAVYA.items():
            print(f"  Pada {i}: {[calc.SIGN_NAMES[s] for s in seq]}")
        selected_seq = calc.SEQUENCES_APASAVYA[pada]
    
    print(f"\nSelected sequence for Pada {pada}: {[calc.SIGN_NAMES[s] for s in selected_seq]}")
    print(f"Starting sign: {calc.SIGN_NAMES[selected_seq[0]]}")
    
    # Check if Gemini software might be using different logic
    print(f"\n=== POSSIBLE DISCREPANCY SOURCES ===")
    print("1. Different Ayanamsa (we use Lahiri)")
    print("2. Different Savya/Apasavya classification")
    print("3. Different sequence assignments")
    print("4. Different pada calculation method")
    
    # Test with different pada to see if that gives Pisces
    print(f"\n=== TESTING OTHER PADAS ===")
    for test_pada in [1, 2, 3, 4]:
        if is_savya:
            test_seq = calc.SEQUENCES_SAVYA[test_pada]
        else:
            test_seq = calc.SEQUENCES_APASAVYA[test_pada]
        print(f"Pada {test_pada}: {calc.SIGN_NAMES[test_seq[0]]} (sequence: {[calc.SIGN_NAMES[s] for s in test_seq]})")

if __name__ == "__main__":
    verify_nakshatra_calculation()