#!/usr/bin/env python3
"""
Test D60 calculation with exact DrikPanchang coordinates
Birth Details: 29th July 2007, 8:49 AM
Location: 28°27'36"N, 77°1'35"E (Gurgaon, India)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from calculators.chart_calculator import ChartCalculator
from charts.routes import get_divisional_sign

class TestBirthData:
    def __init__(self):
        # Convert DMS to decimal - DrikPanchang coordinates
        self.latitude = 28 + 27/60 + 36/3600  # 28.46°
        self.longitude = 77 + 1/60 + 35/3600  # 77.0264°
        self.date = '2007-07-29'
        self.time = '08:49'
        self.timezone = 'UTC+5:30'
        self.name = 'Test'
        self.place = 'Gurgaon'
        self.gender = 'M'
        self.relation = 'self'

def test_d60_calculation():
    print("=" * 80)
    print("D60 CALCULATION TEST - With Exact DrikPanchang Coordinates")
    print("=" * 80)
    print(f"\nBirth Details:")
    print(f"  Date: 29th July 2007")
    print(f"  Time: 8:49:00 AM IST")
    print(f"  Location: 28°27'36\"N, 77°1'35\"E")
    print(f"  Decimal: {28 + 27/60 + 36/3600:.6f}°N, {77 + 1/60 + 35/3600:.6f}°E")
    
    # Create birth data
    birth_data = TestBirthData()
    
    # Calculate D1 chart
    print(f"\n{'='*80}")
    print("STEP 1: D1 Chart")
    print("=" * 80)
    
    calculator = ChartCalculator({})
    chart_data = calculator.calculate_chart(birth_data)
    
    sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    print(f"\nD1 Positions:")
    for planet in ['Sun', 'Moon', 'Mars']:
        p_data = chart_data['planets'][planet]
        print(f"  {planet:<8} {p_data['degree']:>6.2f}° in {sign_names[p_data['sign']]}")
    
    # Calculate D60
    print(f"\n{'='*80}")
    print("STEP 2: D60 Chart - BOTH METHODS")
    print("=" * 80)
    
    division_number = 60
    
    print(f"\nComparing Two D60 Calculation Methods:")
    print(f"{'Planet':<10} {'D1 Deg':<10} {'Method 1 (Ratio)':<20} {'Method 2 (Keep D1)':<20}")
    print("-" * 65)
    
    for planet in ['Sun', 'Moon', 'Mars']:
        planet_data = chart_data['planets'][planet]
        planet_sign = int(planet_data['longitude'] / 30)
        planet_degree = planet_data['longitude'] % 30
        
        # Calculate D60 sign
        EPS = 1e-9
        part_size = 30.0 / division_number  # 0.5°
        part_index = int((planet_degree + EPS) / part_size)
        degree_within_part = (planet_degree + EPS) - (part_index * part_size)
        divisional_sign = get_divisional_sign(planet_sign, planet_degree, division_number)
        
        # Method 1: Ratio/Scaling (0.5° real = 30° sub-space)
        scaled_degree = (degree_within_part / part_size) * 30.0
        
        # Method 2: Keep D1 degree
        keep_d1_degree = planet_degree
        
        print(f"{planet:<10} {planet_degree:>8.2f}°  {sign_names[divisional_sign]} {scaled_degree:>6.2f}°  {sign_names[divisional_sign]} {keep_d1_degree:>6.2f}°")
    
    print(f"\n{'='*80}")
    print("Summary:")
    print("=" * 80)
    print(f"Method 1 (Ratio): Each 0.5° of real space = 30° of sub-space")
    print(f"  - Sun at 11.70° → part 23, within 0.215° → scales to 12.92°")
    print(f"\nMethod 2 (Keep D1): Keep the original D1 degree")
    print(f"  - Sun at 11.70° → stays at 11.70° in D60")
    print(f"\nDrikPanchang shows: 11.41° (closer to Method 2)")
    print(f"Our current implementation: Method 2")
    print("=" * 80)

if __name__ == '__main__':
    test_d60_calculation()
