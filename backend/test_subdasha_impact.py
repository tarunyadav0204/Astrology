#!/usr/bin/env python3
"""
Test how the 6-day Mahadasha difference affects Sookshma and Prana dasha accuracy
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.dasha_calculator import DashaCalculator
from datetime import datetime, timedelta

def test_subdasha_impact():
    birth_data = {
        'date': '1980-04-02',
        'time': '14:55',
        'latitude': 29.1492,
        'longitude': 75.7217,
        'timezone': 5.5
    }
    
    print("=== IMPACT OF 6-DAY DIFFERENCE ON SUB-DASHAS ===")
    
    calculator = DashaCalculator()
    
    # Test a date in the middle of Rahu Mahadasha
    test_date = datetime(1990, 1, 1)  # Middle of Rahu period
    
    dashas = calculator.calculate_current_dashas(birth_data, test_date)
    
    print(f"Test date: {test_date.strftime('%B %d, %Y')}")
    print(f"Current Mahadasha: {dashas['mahadasha']['planet']}")
    print(f"Current Antardasha: {dashas['antardasha']['planet']}")
    print(f"Current Pratyantardasha: {dashas['pratyantardasha']['planet']}")
    print(f"Current Sookshma: {dashas['sookshma']['planet']}")
    print(f"Current Prana: {dashas['prana']['planet']}")
    print()
    
    # Test how the 6-day shift affects sub-dashas
    shifted_date = test_date + timedelta(days=6)
    shifted_dashas = calculator.calculate_current_dashas(birth_data, shifted_date)
    
    print(f"Shifted date (+6 days): {shifted_date.strftime('%B %d, %Y')}")
    print(f"Shifted Mahadasha: {shifted_dashas['mahadasha']['planet']}")
    print(f"Shifted Antardasha: {shifted_dashas['antardasha']['planet']}")
    print(f"Shifted Pratyantardasha: {shifted_dashas['pratyantardasha']['planet']}")
    print(f"Shifted Sookshma: {shifted_dashas['sookshma']['planet']}")
    print(f"Shifted Prana: {shifted_dashas['prana']['planet']}")
    print()
    
    # Check if any sub-dashas changed
    changes = []
    if dashas['antardasha']['planet'] != shifted_dashas['antardasha']['planet']:
        changes.append('Antardasha')
    if dashas['pratyantardasha']['planet'] != shifted_dashas['pratyantardasha']['planet']:
        changes.append('Pratyantardasha')
    if dashas['sookshma']['planet'] != shifted_dashas['sookshma']['planet']:
        changes.append('Sookshma')
    if dashas['prana']['planet'] != shifted_dashas['prana']['planet']:
        changes.append('Prana')
    
    if changes:
        print(f"⚠️  SUB-DASHA CHANGES DUE TO 6-DAY SHIFT: {', '.join(changes)}")
    else:
        print(f"✅ NO SUB-DASHA CHANGES - 6-day difference is acceptable")
    
    print()
    
    # Test near the end of Rahu Mahadasha where precision matters most
    print("=== TESTING NEAR RAHU MAHADASHA END ===")
    
    # Test dates around the end of Rahu Mahadasha
    rahu_end_our = datetime(1995, 10, 29)  # Our calculation
    rahu_end_astrosage = datetime(1995, 11, 4)  # AstroSage
    
    test_dates = [
        rahu_end_our - timedelta(days=30),
        rahu_end_our - timedelta(days=7),
        rahu_end_our,
        rahu_end_astrosage,
        rahu_end_astrosage + timedelta(days=7)
    ]
    
    for test_date in test_dates:
        dashas = calculator.calculate_current_dashas(birth_data, test_date)
        
        print(f"{test_date.strftime('%b %d, %Y')}: {dashas['mahadasha']['planet']}-{dashas['antardasha']['planet']}-{dashas['pratyantardasha']['planet']}-{dashas['sookshma']['planet']}-{dashas['prana']['planet']}")
        
        # Check if we're still in Rahu or moved to Jupiter
        if dashas['mahadasha']['planet'] != 'Rahu':
            print(f"  *** MAHADASHA CHANGED TO {dashas['mahadasha']['planet']} ***")
    
    print()
    
    # Calculate the precision impact
    print("=== PRECISION IMPACT ANALYSIS ===")
    
    # Rahu Mahadasha is 18 years = 6574.4 days (using 365.242199)
    rahu_total_days = 18 * 365.242199
    
    # 6-day error as percentage
    error_percentage = (6 / rahu_total_days) * 100
    
    print(f"Rahu Mahadasha total days: {rahu_total_days:.1f}")
    print(f"6-day error percentage: {error_percentage:.4f}%")
    
    # Impact on sub-dashas
    # Antardasha periods are much shorter, so 6-day error has bigger impact
    typical_antar_days = (18 * 16) / 120 * 365.242199  # Rahu-Jupiter antardasha
    antar_error_percentage = (6 / typical_antar_days) * 100
    
    print(f"Typical Antardasha days: {typical_antar_days:.1f}")
    print(f"6-day error impact on Antardasha: {antar_error_percentage:.2f}%")
    
    # Pratyantardasha impact
    typical_pratyantar_days = typical_antar_days * 16 / 120  # Rahu-Jupiter-Jupiter
    pratyantar_error_percentage = (6 / typical_pratyantar_days) * 100
    
    print(f"Typical Pratyantardasha days: {typical_pratyantar_days:.1f}")
    print(f"6-day error impact on Pratyantardasha: {pratyantar_error_percentage:.2f}%")
    
    # Sookshma impact
    typical_sookshma_days = typical_pratyantar_days * 16 / 120
    sookshma_error_percentage = (6 / typical_sookshma_days) * 100
    
    print(f"Typical Sookshma days: {typical_sookshma_days:.1f}")
    print(f"6-day error impact on Sookshma: {sookshma_error_percentage:.2f}%")
    
    print()
    print("CONCLUSION:")
    if error_percentage < 0.1:
        print("✅ 6-day difference is acceptable for Mahadasha calculations")
    if antar_error_percentage < 2:
        print("✅ Impact on Antardasha is manageable")
    if pratyantar_error_percentage < 10:
        print("⚠️  Pratyantardasha accuracy is affected but still usable")
    if sookshma_error_percentage > 20:
        print("❌ Sookshma dasha accuracy is significantly impacted")

if __name__ == "__main__":
    test_subdasha_impact()