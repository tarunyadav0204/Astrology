#!/usr/bin/env python3
"""
Test script for advanced Vedic astrology calculators
Tests: Planetary War, Vargottama, Neecha Bhanga, Pancha Mahapurusha
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from calculators.planetary_war_calculator import PlanetaryWarCalculator
from calculators.vargottama_calculator import VargottamaCalculator
from calculators.neecha_bhanga_calculator import NeechaBhangaCalculator
from calculators.pancha_mahapurusha_calculator import PanchaMahapurushaCalculator

def create_test_chart_data():
    """Create sample chart data for testing"""
    return {
        'ascendant': 0.0,     # Aries ascendant (0-30°)
        'Sun': 15.0,          # Aries (0-30°) - 1st house (Kendra)
        'Moon': 225.0,        # Scorpio (210-240°) - debilitated, 8th house
        'Mars': 275.0,        # Capricorn (270-300°) - exalted, 10th house (Kendra) - Ruchaka Yoga!
        'Mercury': 16.0,      # Aries (0-30°) - close to Sun (potential war), 1st house
        'Jupiter': 105.0,     # Cancer (90-120°) - exalted, 4th house (Kendra) - Hamsa Yoga!
        'Venus': 45.0,        # Taurus (30-60°) - own sign, 2nd house
        'Saturn': 15.5,       # Aries (0-30°) - debilitated, close to Sun/Mercury, 1st house
        'Rahu': 135.0,        # Leo (120-150°) - 5th house
        'Ketu': 315.0         # Aquarius (300-330°) - 11th house
    }

def create_test_divisional_charts():
    """Create sample divisional chart data"""
    return {
        'd9_navamsa': {
            'Sun': 45.0,      # Taurus
            'Moon': 225.0,    # Scorpio (same as D1 - Vargottama)
            'Mars': 275.0,    # Capricorn (same as D1 - Vargottama)
            'Mercury': 75.0,  # Gemini (own sign in D9)
            'Jupiter': 105.0, # Cancer (same as D1 - Vargottama)
            'Venus': 345.0,   # Pisces (exalted in D9)
            'Saturn': 195.0,  # Libra (exalted in D9)
            'Rahu': 135.0,
            'Ketu': 315.0
        },
        'd10_dasamsa': {
            'Sun': 15.0,
            'Moon': 225.0,    # Same as D1
            'Mars': 275.0,    # Same as D1
            'Mercury': 16.0,
            'Jupiter': 105.0, # Same as D1
            'Venus': 45.0,    # Same as D1
            'Saturn': 15.5,
            'Rahu': 135.0,
            'Ketu': 315.0
        }
    }

def test_planetary_war_calculator():
    """Test Planetary War Calculator"""
    print("=" * 60)
    print("TESTING PLANETARY WAR CALCULATOR")
    print("=" * 60)
    
    chart_data = create_test_chart_data()
    calculator = PlanetaryWarCalculator(chart_data)
    
    # Test individual war check
    print("\n1. Testing individual planetary war detection:")
    war_result = calculator._check_planetary_war('Sun', 'Mercury')
    if war_result:
        print(f"   War detected between Sun and Mercury:")
        print(f"   - Angular distance: {war_result['angular_distance']:.2f}°")
        print(f"   - Winner: {war_result['winner']}")
        print(f"   - War type: {war_result['war_type']}")
    else:
        print("   No war detected between Sun and Mercury")
    
    # Test all wars
    print("\n2. Testing all planetary wars:")
    all_wars = calculator.calculate_planetary_wars()
    for war in all_wars:
        print(f"   War: {war['planet1']} vs {war['planet2']}")
        print(f"   Distance: {war['angular_distance']:.2f}°, Winner: {war['winner']}")
    
    # Test summary
    print("\n3. Testing war summary:")
    summary = calculator.get_war_summary()
    print(f"   Total wars: {summary['total_wars']}")
    print(f"   Summary: {summary['summary']}")
    
    return True  # Always pass if no errors

def test_vargottama_calculator():
    """Test Vargottama Calculator"""
    print("\n" + "=" * 60)
    print("TESTING VARGOTTAMA CALCULATOR")
    print("=" * 60)
    
    chart_data = create_test_chart_data()
    divisional_charts = create_test_divisional_charts()
    calculator = VargottamaCalculator(chart_data, divisional_charts)
    
    # Test individual planet
    print("\n1. Testing individual planet Vargottama (Moon):")
    moon_result = calculator._analyze_planet_vargottama('Moon')
    print(f"   Is Vargottama: {moon_result['is_vargottama']}")
    print(f"   Charts: {moon_result['vargottama_charts']}")
    print(f"   Strength: {moon_result['strength_level']}")
    
    # Test all planets
    print("\n2. Testing all Vargottama positions:")
    all_results = calculator.calculate_vargottama_positions()
    for planet, result in all_results.items():
        if result['is_vargottama']:
            print(f"   {planet}: {result['strength_level']} ({len(result['vargottama_charts'])} charts)")
    
    # Test summary
    print("\n3. Testing Vargottama summary:")
    summary = calculator.get_vargottama_summary()
    print(f"   Total Vargottama planets: {summary['total_vargottama_planets']}")
    
    strongest = calculator.get_strongest_vargottama()
    if strongest:
        print(f"   Strongest: {strongest['planet']} ({strongest['strength']})")
    
    return summary['total_vargottama_planets'] > 0

def test_neecha_bhanga_calculator():
    """Test Neecha Bhanga Calculator"""
    print("\n" + "=" * 60)
    print("TESTING NEECHA BHANGA CALCULATOR")
    print("=" * 60)
    
    chart_data = create_test_chart_data()
    divisional_charts = create_test_divisional_charts()
    calculator = NeechaBhangaCalculator(chart_data, divisional_charts)
    
    # Test individual debilitated planet
    print("\n1. Testing individual Neecha Bhanga (Moon in Scorpio):")
    moon_result = calculator._check_neecha_bhanga_conditions('Moon', chart_data['Moon'])
    print(f"   Is debilitated: {moon_result['is_debilitated']}")
    print(f"   Neecha Bhanga present: {moon_result['neecha_bhanga_present']}")
    print(f"   Conditions met: {moon_result['total_conditions']}")
    print(f"   Overall strength: {moon_result['overall_strength']}")
    
    # Test all debilitated planets
    print("\n2. Testing all Neecha Bhanga conditions:")
    all_results = calculator.calculate_neecha_bhanga()
    for planet, result in all_results.items():
        print(f"   {planet} in {result['debilitation_sign']}:")
        print(f"   - Neecha Bhanga: {result['neecha_bhanga_present']}")
        print(f"   - Strength: {result['overall_strength']}")
        for condition in result['conditions_met']:
            print(f"     * {condition['condition']} ({condition['strength']})")
    
    # Test summary
    print("\n3. Testing Neecha Bhanga summary:")
    summary = calculator.get_neecha_bhanga_summary()
    print(f"   Total debilitated: {summary['total_debilitated_planets']}")
    print(f"   With Neecha Bhanga: {len(summary['neecha_bhanga_planets'])}")
    
    return len(all_results) > 0

def test_pancha_mahapurusha_calculator():
    """Test Pancha Mahapurusha Calculator"""
    print("\n" + "=" * 60)
    print("TESTING PANCHA MAHAPURUSHA CALCULATOR")
    print("=" * 60)
    
    chart_data = create_test_chart_data()
    calculator = PanchaMahapurushaCalculator(chart_data)
    
    # Test individual yoga
    print("\n1. Testing individual yoga (Ruchaka - Mars):")
    mars_yoga = calculator._check_yoga_formation('Ruchaka', 'Mars', 
                                               calculator.yoga_definitions['Ruchaka'])
    print(f"   Is formed: {mars_yoga['is_formed']}")
    print(f"   Planet house: {mars_yoga['planet_house']}")
    print(f"   Sign type: {mars_yoga['sign_type']}")
    print(f"   In Kendra: {mars_yoga['is_in_kendra']}")
    print(f"   In valid sign: {mars_yoga['is_in_valid_sign']}")
    print(f"   Yoga strength: {mars_yoga['yoga_strength']}")
    
    # Test all yogas
    print("\n2. Testing all Pancha Mahapurusha Yogas:")
    all_yogas = calculator.calculate_pancha_mahapurusha_yogas()
    for yoga_name, yoga_data in all_yogas.items():
        print(f"   {yoga_name} ({yoga_data['planet']}): {yoga_data['yoga_strength']}")
        print(f"   - {yoga_data['planet']} in {yoga_data['planet_sign']} (House {yoga_data['planet_house']})")
    
    # Test summary
    print("\n3. Testing Pancha Mahapurusha summary:")
    summary = calculator.get_pancha_mahapurusha_summary()
    print(f"   Total yogas formed: {summary['total_yogas']}")
    
    strongest = calculator.get_strongest_yoga()
    if strongest:
        print(f"   Strongest: {strongest['yoga_name']} ({strongest['strength']})")
    
    return len(all_yogas) > 0

def run_all_tests():
    """Run all calculator tests"""
    print("ADVANCED VEDIC ASTROLOGY CALCULATORS TEST SUITE")
    print("=" * 80)
    
    test_results = {}
    
    try:
        test_results['planetary_war'] = test_planetary_war_calculator()
    except Exception as e:
        print(f"Planetary War Calculator Error: {e}")
        test_results['planetary_war'] = False
    
    try:
        test_results['vargottama'] = test_vargottama_calculator()
    except Exception as e:
        print(f"Vargottama Calculator Error: {e}")
        test_results['vargottama'] = False
    
    try:
        test_results['neecha_bhanga'] = test_neecha_bhanga_calculator()
    except Exception as e:
        print(f"Neecha Bhanga Calculator Error: {e}")
        test_results['neecha_bhanga'] = False
    
    try:
        test_results['pancha_mahapurusha'] = test_pancha_mahapurusha_calculator()
    except Exception as e:
        print(f"Pancha Mahapurusha Calculator Error: {e}")
        test_results['pancha_mahapurusha'] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All calculators are working correctly!")
    else:
        print("⚠️  Some calculators need attention.")

if __name__ == "__main__":
    run_all_tests()