#!/usr/bin/env python3

"""Test D3 ascendant calculation to match AstroSage"""

def get_divisional_sign(sign, degree_in_sign, division):
    """Calculate divisional sign using proper Vedic formulas with boundary buffer"""
    EPS = 1e-9  # Prevent 10.0 becoming 9.999
    part = int((degree_in_sign + EPS) / (30.0/division))
    
    if division == 3:  # Drekkana (D3) - Parashara
        # 0-10: Self, 10-20: 5th, 20-30: 9th
        if part == 0: return sign
        elif part == 1: return (sign + 4) % 12
        else: return (sign + 8) % 12
    
    return sign  # Default

def test_d3_ascendant():
    """Test D3 ascendant calculation"""
    
    # Test case: If D1 ascendant is Cancer (sign 3) at some degree
    # Let's test different degrees to see the pattern
    
    print("D3 (Drekkana) Ascendant Test:")
    print("=" * 40)
    
    # Test Cancer ascendant at different degrees
    cancer_sign = 3  # Cancer
    
    test_degrees = [5, 15, 25]  # Different parts of the sign
    
    for degree in test_degrees:
        d3_sign = get_divisional_sign(cancer_sign, degree, 3)
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        part = int(degree / 10)  # Which part (0, 1, or 2)
        
        print(f"Cancer {degree}° -> Part {part} -> D3: {sign_names[d3_sign]} (Sign {d3_sign})")
    
    print("\nExpected for Cancer ascendant:")
    print("0-10°: Cancer (same sign)")
    print("10-20°: Scorpio (5th from Cancer)")  
    print("20-30°: Pisces (9th from Cancer)")
    
    # If AstroSage shows Pisces ascendant in D3, the D1 ascendant should be in the 20-30° range

if __name__ == "__main__":
    test_d3_ascendant()