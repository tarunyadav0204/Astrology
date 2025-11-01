#!/usr/bin/env python3
"""
Test script to verify house calculation logic for all 12 houses
Run with: python test_house_calculations.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from calculators.house_analyzer import HouseAnalyzer

# Sample chart data for testing
test_chart_data = {
    'houses': [
        {'sign': 0, 'cusp_longitude': 15.0},   # 1st house - Aries
        {'sign': 1, 'cusp_longitude': 45.0},   # 2nd house - Taurus  
        {'sign': 2, 'cusp_longitude': 75.0},   # 3rd house - Gemini
        {'sign': 3, 'cusp_longitude': 105.0},  # 4th house - Cancer
        {'sign': 4, 'cusp_longitude': 135.0},  # 5th house - Leo
        {'sign': 5, 'cusp_longitude': 165.0},  # 6th house - Virgo
        {'sign': 6, 'cusp_longitude': 195.0},  # 7th house - Libra
        {'sign': 7, 'cusp_longitude': 225.0},  # 8th house - Scorpio
        {'sign': 8, 'cusp_longitude': 255.0},  # 9th house - Sagittarius
        {'sign': 9, 'cusp_longitude': 285.0},  # 10th house - Capricorn
        {'sign': 10, 'cusp_longitude': 315.0}, # 11th house - Aquarius
        {'sign': 11, 'cusp_longitude': 345.0}  # 12th house - Pisces
    ],
    'planets': {
        'Sun': {'longitude': 255.0, 'house': 9, 'sign': 8, 'retrograde': False},
        'Moon': {'longitude': 45.0, 'house': 2, 'sign': 1, 'retrograde': False},
        'Mars': {'longitude': 255.0, 'house': 9, 'sign': 8, 'retrograde': False},
        'Mercury': {'longitude': 225.0, 'house': 8, 'sign': 7, 'retrograde': False},
        'Jupiter': {'longitude': 255.0, 'house': 9, 'sign': 8, 'retrograde': False},
        'Venus': {'longitude': 165.0, 'house': 6, 'sign': 5, 'retrograde': False},
        'Saturn': {'longitude': 255.0, 'house': 9, 'sign': 8, 'retrograde': False},
        'Rahu': {'longitude': 165.0, 'house': 6, 'sign': 5, 'retrograde': False},
        'Ketu': {'longitude': 345.0, 'house': 12, 'sign': 11, 'retrograde': False}
    }
}

class BirthData:
    def __init__(self):
        self.date = '1990-01-01'
        self.time = '12:00'
        self.place = 'New Delhi'
        self.latitude = 28.6139
        self.longitude = 77.2090
        self.timezone = 'UTC+5:30'

test_birth_data = BirthData()

def test_all_houses():
    """Test house calculations for all 12 houses"""
    print("=" * 80)
    print("HOUSE CALCULATION TEST RESULTS")
    print("=" * 80)
    
    analyzer = HouseAnalyzer(test_chart_data, test_birth_data)
    
    for house_num in range(1, 13):
        print(f"\n{'='*20} HOUSE {house_num} {'='*20}")
        
        try:
            analysis = analyzer.analyze_house(house_num)
            assessment = analysis['overall_house_assessment']
            
            print(f"House: {house_num}th")
            print(f"Sign: {analysis['basic_info']['house_sign_name']}")
            print(f"Lord: {analysis['basic_info']['house_lord']}")
            print(f"Types: {', '.join(analysis['basic_info']['house_types'])}")
            print(f"Final Grade: {assessment['classical_grade']}")
            print(f"Score: {assessment['overall_strength_score']}/100")
            
            print(f"\nAssessment Factors:")
            for factor_name, factor_data in assessment['assessment_factors'].items():
                grade = factor_data.get('grade', 'N/A')
                value = factor_data.get('value', 'N/A')
                reasoning = factor_data.get('reasoning', 'No reasoning provided')[:100] + "..."
                print(f"  {factor_name}: {grade} (Value: {value}) - {reasoning}")
            
            print(f"\nKey Strengths: {assessment.get('key_strengths', [])}")
            print(f"Key Weaknesses: {assessment.get('key_weaknesses', [])}")
            
        except Exception as e:
            print(f"ERROR analyzing house {house_num}: {str(e)}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

def test_specific_issues():
    """Test specific issues we identified"""
    print("\n" + "=" * 60)
    print("TESTING SPECIFIC ISSUES")
    print("=" * 60)
    
    analyzer = HouseAnalyzer(test_chart_data, test_birth_data)
    
    # Test 9th house (Sun as lord in own house - should be strong)
    print("\n1. Testing 9th House (Sun lord in 9th house):")
    analysis = analyzer.analyze_house(9)
    lord_pos_strength = analysis['overall_house_assessment']['assessment_factors']['lord_positional_strength']
    print(f"   Lord Positional Strength: {lord_pos_strength['grade']} (Expected: Uttama)")
    print(f"   Reasoning: {lord_pos_strength['reasoning']}")
    
    # Test house with Rahu (6th house)
    print("\n2. Testing 6th House (has Rahu):")
    analysis = analyzer.analyze_house(6)
    resident_strength = analysis['overall_house_assessment']['assessment_factors']['resident_planets_strength']
    print(f"   Resident Planets Strength: {resident_strength['grade']}")
    print(f"   Reasoning: {resident_strength['reasoning']}")
    
    # Test Maraka house (2nd house)
    print("\n3. Testing 2nd House (Maraka type):")
    analysis = analyzer.analyze_house(2)
    house_type_strength = analysis['overall_house_assessment']['assessment_factors']['house_type_strength']
    print(f"   House Type Strength: {house_type_strength['grade']}")
    print(f"   Reasoning: {house_type_strength['reasoning']}")

if __name__ == "__main__":
    test_all_houses()
    test_specific_issues()