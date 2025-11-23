#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator
import swisseph as swe
from datetime import datetime, timedelta

def debug_balance_calculation():
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
    
    print("=== DEBUGGING BALANCE CALCULATION ===")
    print(f"Birth: {birth_data['date']} {birth_data['time']} New Delhi")
    print(f"Birth JD: {birth_jd}")
    
    # Get moon position and nakshatra info
    moon_lon = calc._moon_longitude_sidereal(birth_jd)
    nak_info = calc._nakshatra_pada(moon_lon)
    
    print(f"\nMoon longitude: {moon_lon:.8f}°")
    print(f"Nakshatra: {nak_info['nakshatra']} (Shravana)")
    print(f"Pada: {nak_info['pada']}")
    print(f"Degrees in nakshatra: {nak_info['deg_in_nak']:.8f}°")
    print(f"Nakshatra span: {nak_info['nak_span']:.8f}°")
    
    # Get sequence info
    seq_data = calc._get_sequence(nak_info['nakshatra'], nak_info['pada'])
    sequence = seq_data['seq']
    is_savya = seq_data['is_savya']
    start_sign = sequence[0]
    
    print(f"\nDirection: {'Savya' if is_savya else 'Apasavya'}")
    print(f"Starting sign: {calc.SIGN_NAMES[start_sign]} (sign {start_sign})")
    print(f"Sign years: {calc.SIGN_YEARS[start_sign]}")
    
    # Our current balance calculation
    pada_span = nak_info['nak_span'] / 4.0
    deg_in_pada = nak_info['deg_in_nak'] % pada_span
    
    print(f"\n=== OUR CURRENT METHOD ===")
    print(f"Pada span: {pada_span:.8f}°")
    print(f"Degrees in pada: {deg_in_pada:.8f}°")
    
    if is_savya:
        balance_frac = (pada_span - deg_in_pada) / pada_span
        print(f"Savya balance fraction: ({pada_span:.8f} - {deg_in_pada:.8f}) / {pada_span:.8f} = {balance_frac:.8f}")
    else:
        balance_frac = deg_in_pada / pada_span
        print(f"Apasavya balance fraction: {deg_in_pada:.8f} / {pada_span:.8f} = {balance_frac:.8f}")
    
    our_balance = calc.SIGN_YEARS[start_sign] * balance_frac
    print(f"Our balance years: {calc.SIGN_YEARS[start_sign]} × {balance_frac:.8f} = {our_balance:.8f}")
    
    # Calculate end date with our method
    our_balance_days = our_balance * 365.2425
    our_end_jd = birth_jd + our_balance_days
    our_end_date = swe.revjul(our_end_jd)
    print(f"Our end date: {int(our_end_date[0])}-{int(our_end_date[1]):02d}-{int(our_end_date[2]):02d}")
    
    # Alternative method 1: Use full nakshatra instead of pada
    print(f"\n=== ALTERNATIVE METHOD 1: Full Nakshatra ===")
    if is_savya:
        alt1_balance_frac = (nak_info['nak_span'] - nak_info['deg_in_nak']) / nak_info['nak_span']
        print(f"Savya balance fraction: ({nak_info['nak_span']:.8f} - {nak_info['deg_in_nak']:.8f}) / {nak_info['nak_span']:.8f} = {alt1_balance_frac:.8f}")
    else:
        alt1_balance_frac = nak_info['deg_in_nak'] / nak_info['nak_span']
        print(f"Apasavya balance fraction: {nak_info['deg_in_nak']:.8f} / {nak_info['nak_span']:.8f} = {alt1_balance_frac:.8f}")
    
    alt1_balance = calc.SIGN_YEARS[start_sign] * alt1_balance_frac
    print(f"Alt1 balance years: {calc.SIGN_YEARS[start_sign]} × {alt1_balance_frac:.8f} = {alt1_balance:.8f}")
    
    alt1_balance_days = alt1_balance * 365.2425
    alt1_end_jd = birth_jd + alt1_balance_days
    alt1_end_date = swe.revjul(alt1_end_jd)
    print(f"Alt1 end date: {int(alt1_end_date[0])}-{int(alt1_end_date[1]):02d}-{int(alt1_end_date[2]):02d}")
    
    # Alternative method 2: Reverse logic for Apasavya
    print(f"\n=== ALTERNATIVE METHOD 2: Reverse Apasavya Logic ===")
    if is_savya:
        alt2_balance_frac = deg_in_pada / pada_span
        print(f"Savya balance fraction: {deg_in_pada:.8f} / {pada_span:.8f} = {alt2_balance_frac:.8f}")
    else:
        alt2_balance_frac = (pada_span - deg_in_pada) / pada_span
        print(f"Apasavya balance fraction: ({pada_span:.8f} - {deg_in_pada:.8f}) / {pada_span:.8f} = {alt2_balance_frac:.8f}")
    
    alt2_balance = calc.SIGN_YEARS[start_sign] * alt2_balance_frac
    print(f"Alt2 balance years: {calc.SIGN_YEARS[start_sign]} × {alt2_balance_frac:.8f} = {alt2_balance:.8f}")
    
    alt2_balance_days = alt2_balance * 365.2425
    alt2_end_jd = birth_jd + alt2_balance_days
    alt2_end_date = swe.revjul(alt2_end_jd)
    print(f"Alt2 end date: {int(alt2_end_date[0])}-{int(alt2_end_date[1]):02d}-{int(alt2_end_date[2]):02d}")
    
    # Check what Gemini's 4.04 years would be
    print(f"\n=== GEMINI'S CALCULATION (4.04 years) ===")
    gemini_years = 4.04
    gemini_days = gemini_years * 365.2425
    gemini_end_jd = birth_jd + gemini_days
    gemini_end_date = swe.revjul(gemini_end_jd)
    print(f"Gemini balance years: {gemini_years}")
    print(f"Gemini end date: {int(gemini_end_date[0])}-{int(gemini_end_date[1]):02d}-{int(gemini_end_date[2]):02d}")
    
    # Calculate what fraction would give Gemini's result
    gemini_fraction = gemini_years / calc.SIGN_YEARS[start_sign]
    print(f"Gemini fraction: {gemini_years} / {calc.SIGN_YEARS[start_sign]} = {gemini_fraction:.8f}")
    
    # Check if this matches any of our alternative methods
    print(f"\n=== COMPARISON ===")
    print(f"Our method:     {our_balance:.6f} years → {int(our_end_date[0])}-{int(our_end_date[1]):02d}-{int(our_end_date[2]):02d}")
    print(f"Alt1 (full nak): {alt1_balance:.6f} years → {int(alt1_end_date[0])}-{int(alt1_end_date[1]):02d}-{int(alt1_end_date[2]):02d}")
    print(f"Alt2 (reverse):  {alt2_balance:.6f} years → {int(alt2_end_date[0])}-{int(alt2_end_date[1]):02d}-{int(alt2_end_date[2]):02d}")
    print(f"Gemini:         {gemini_years:.6f} years → {int(gemini_end_date[0])}-{int(gemini_end_date[1]):02d}-{int(gemini_end_date[2]):02d}")
    
    # Check if Alt1 matches Gemini
    if abs(alt1_balance - gemini_years) < 0.1:
        print("*** ALT1 (FULL NAKSHATRA) MATCHES GEMINI! ***")
    if abs(alt2_balance - gemini_years) < 0.1:
        print("*** ALT2 (REVERSE LOGIC) MATCHES GEMINI! ***")

if __name__ == "__main__":
    debug_balance_calculation()