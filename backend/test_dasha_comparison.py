#!/usr/bin/env python3
"""
Test Dasha calculations using BirthData model vs dictionary
"""
import sys
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from shared.dasha_calculator import DashaCalculator
from main import BirthData
from datetime import datetime

def test_dasha_with_model():
    calculator = DashaCalculator()
    
    # Test with BirthData model (like the API does)
    print("=== TESTING WITH BIRTHDATA MODEL ===\n")
    
    tarun_model = BirthData(
        name='Tarun Yadav',
        date='1980-04-02',
        time='14:55',
        latitude=29.2396596,
        longitude=75.8174505,
        timezone='UTC+5:30',
        place='Hisar, Haryana, India'
    )
    
    dadasd_model = BirthData(
        name='Dadasd',
        date='1980-04-02',
        time='14:55:00',  # This will be normalized to 14:55
        latitude=29.2396596,
        longitude=75.8174505,
        timezone='UTC+5:30',
        place='Hisar, Haryana, India'
    )
    
    print(f"Tarun time after validation: {tarun_model.time}")
    print(f"Dadasd time after validation: {dadasd_model.time}")
    print()
    
    # Convert to dict (like calculate_accurate_dasha does)
    tarun_dict = tarun_model.model_dump()
    dadasd_dict = dadasd_model.model_dump()
    
    print("TARUN DASHAS (via BirthData model):")
    tarun_dashas = calculator.calculate_current_dashas(tarun_dict)
    print(f"  Mahadasha: {tarun_dashas['mahadasha']['planet']}")
    print(f"  Antardasha: {tarun_dashas['antardasha']['planet']}")
    print(f"  Moon Lord: {tarun_dashas['moon_lord']}")
    print()
    
    print("DADASD DASHAS (via BirthData model):")
    dadasd_dashas = calculator.calculate_current_dashas(dadasd_dict)
    print(f"  Mahadasha: {dadasd_dashas['mahadasha']['planet']}")
    print(f"  Antardasha: {dadasd_dashas['antardasha']['planet']}")
    print(f"  Moon Lord: {dadasd_dashas['moon_lord']}")
    print()
    
    if (tarun_dashas['antardasha']['planet'] != dadasd_dashas['antardasha']['planet']):
        print("❌ DASHAS ARE DIFFERENT AFTER MODEL VALIDATION!")
        print("The BirthData model validation is causing the issue.")
    else:
        print("✅ DASHAS ARE IDENTICAL AFTER MODEL VALIDATION!")
        print("The issue is elsewhere.")

if __name__ == "__main__":
    test_dasha_with_model()