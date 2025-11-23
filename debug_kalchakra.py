#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator
import swisseph as swe

def debug_birth_chart():
    # Test data: 26th June 1975, 13:35, New Delhi
    birth_data = {
        'date': '1975-06-26',
        'time': '13:35',
        'timezone_offset': 5.5,  # IST
        'latitude': 28.6139,
        'longitude': 77.2090
    }
    
    print("=== DEBUGGING KALCHAKRA DISCREPANCY ===")
    print(f"Birth: {birth_data['date']} {birth_data['time']} New Delhi")
    
    calc = BPHSKalachakraCalculator()
    
    # Manual calculation for debugging
    birth_jd = calc._parse_birth_jd(birth_data)
    print(f"Birth JD: {birth_jd}")
    
    # Get moon position
    moon_lon = calc._moon_longitude_sidereal(birth_jd)
    print(f"Sidereal Moon longitude: {moon_lon:.6f}°")
    
    # Get nakshatra info
    nak_info = calc._nakshatra_pada(moon_lon)
    print(f"Nakshatra: {nak_info['nakshatra']}")
    print(f"Pada: {nak_info['pada']}")
    print(f"Degrees in nakshatra: {nak_info['deg_in_nak']:.6f}")
    
    # Check Savya/Apasavya classification
    is_savya = nak_info['nakshatra'] in calc.SAVYA_NAKSHATRAS
    print(f"Is Savya: {is_savya}")
    print(f"Direction: {'Savya' if is_savya else 'Apasavya'}")
    
    # Get sequence
    seq_data = calc._get_sequence(nak_info['nakshatra'], nak_info['pada'])
    sequence = seq_data['seq']
    print(f"Sequence: {[calc.SIGN_NAMES[s] for s in sequence]}")
    print(f"First sign (starting dasha): {calc.SIGN_NAMES[sequence[0]]}")
    
    # Calculate balance
    balance_years = calc._balance_first_dasha(
        nak_info['deg_in_nak'], 
        nak_info['nak_span'], 
        nak_info['pada'], 
        sequence[0], 
        is_savya
    )
    print(f"Balance years for first dasha: {balance_years:.6f}")
    
    # Full calculation
    result = calc.calculate_kalchakra_dasha(birth_data)
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return
    
    print(f"\n=== FINAL RESULT ===")
    print(f"System: {result['system']}")
    print(f"Nakshatra: {result['nakshatra']}")
    print(f"Pada: {result['pada']}")
    print(f"Direction: {result['direction']}")
    print(f"Cycle length: {result['cycle_len']} years")
    print(f"First mahadasha: {result['mahadashas'][0]['name']} ({result['mahadashas'][0]['years']:.2f} years)")
    print(f"Deha: {result['deha']}")
    print(f"Jeeva: {result['jeeva']}")
    
    print(f"\n=== MAHADASHA SEQUENCE ===")
    for i, maha in enumerate(result['mahadashas'][:5]):  # First 5 only
        print(f"{i+1}. {maha['name']} - {maha['years']:.2f}y ({maha['start'][:10]} to {maha['end'][:10]}) - {maha['gati']}")

if __name__ == "__main__":
    debug_birth_chart()