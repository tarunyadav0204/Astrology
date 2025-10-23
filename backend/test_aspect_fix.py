#!/usr/bin/env python3

def test_corrected_aspect_calculation():
    print("Testing CORRECTED Mars aspect calculation:")
    print("Mars aspects: [1, 4, 7, 8]")
    print()
    
    # Test cases with correct logic
    test_cases = [
        # (mars_house, target_house, expected_aspect, should_be_valid)
        (1, 1, 1, True),   # Mars in 1st aspecting 1st = conjunction (1st aspect)
        (1, 4, 4, True),   # Mars in 1st aspecting 4th = 4th aspect
        (1, 7, 7, True),   # Mars in 1st aspecting 7th = 7th aspect  
        (1, 8, 8, True),   # Mars in 1st aspecting 8th = 8th aspect
        (1, 5, 5, False),  # Mars in 1st aspecting 5th = 5th aspect (invalid)
        (2, 5, 4, True),   # Mars in 2nd aspecting 5th = 4th aspect (2+4-1=5)
        (2, 8, 7, True),   # Mars in 2nd aspecting 8th = 7th aspect (2+7-1=8)
        (2, 9, 8, True),   # Mars in 2nd aspecting 9th = 8th aspect (2+8-1=9)
        (2, 11, 10, False), # Mars in 2nd aspecting 11th = 10th aspect (invalid)
    ]
    
    mars_aspects = [1, 4, 7, 8]
    
    for mars_house, target_house, expected_aspect, should_be_valid in test_cases:
        # Calculate aspect using corrected logic
        house_diff = (target_house - mars_house + 12) % 12
        if house_diff == 0:
            actual_aspect = 1  # Same house = conjunction
        else:
            actual_aspect = house_diff  # Direct house difference
        
        is_valid = actual_aspect in mars_aspects
        
        print(f"Mars in house {mars_house}, Target in house {target_house}")
        print(f"House difference: ({target_house} - {mars_house} + 12) % 12 = {house_diff}")
        print(f"Aspect number: {actual_aspect}")
        print(f"Expected: {expected_aspect}, Valid: {is_valid}, Should be valid: {should_be_valid}")
        print(f"✓ CORRECT" if (actual_aspect == expected_aspect and is_valid == should_be_valid) else "✗ WRONG")
        print()

if __name__ == "__main__":
    test_corrected_aspect_calculation()