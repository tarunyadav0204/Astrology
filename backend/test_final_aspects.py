#!/usr/bin/env python3

def test_final_aspect_calculation():
    print("Testing FINAL corrected aspect calculation:")
    print("=" * 50)
    
    # Mars aspects: [1, 4, 7, 8]
    mars_aspects = [1, 4, 7, 8]
    
    def calculate_aspect(aspecting_house, target_house, available_aspects):
        """Calculate which aspect (if any) reaches target from aspecting house"""
        for test_aspect in available_aspects:
            if test_aspect == 1:
                # Conjunction - same house
                if aspecting_house == target_house:
                    return 1
            else:
                # Calculate target house for this aspect
                calculated_target = ((aspecting_house + test_aspect - 2) % 12) + 1
                if calculated_target == target_house:
                    return test_aspect
        return None
    
    # Test cases
    test_cases = [
        # (mars_house, target_house, expected_result)
        (1, 1, 1),    # Mars 1st → 1st = 1st aspect (conjunction)
        (1, 4, 4),    # Mars 1st → 4th = 4th aspect
        (1, 7, 7),    # Mars 1st → 7th = 7th aspect
        (1, 8, 8),    # Mars 1st → 8th = 8th aspect
        (1, 5, None), # Mars 1st → 5th = no valid aspect
        (5, 5, 1),    # Mars 5th → 5th = 1st aspect (conjunction)
        (5, 8, 4),    # Mars 5th → 8th = 4th aspect
        (5, 11, 7),   # Mars 5th → 11th = 7th aspect
        (5, 12, 8),   # Mars 5th → 12th = 8th aspect
        (5, 9, None), # Mars 5th → 9th = no valid aspect
    ]
    
    print("Mars aspects:", mars_aspects)
    print()
    
    all_correct = True
    for mars_house, target_house, expected in test_cases:
        result = calculate_aspect(mars_house, target_house, mars_aspects)
        is_correct = result == expected
        all_correct = all_correct and is_correct
        
        status = "✓ CORRECT" if is_correct else "✗ WRONG"
        print(f"Mars {mars_house}th → {target_house}th = {result}th aspect (expected: {expected}) {status}")
    
    print()
    print("=" * 50)
    print(f"Overall result: {'✓ ALL CORRECT' if all_correct else '✗ SOME ERRORS'}")
    
    # Show what Mars in 5th house can aspect
    print()
    print("Mars in 5th house can aspect:")
    mars_house = 5
    for aspect in mars_aspects:
        if aspect == 1:
            target = mars_house
        else:
            target = ((mars_house + aspect - 2) % 12) + 1
        print(f"  {aspect}th aspect → {target}th house")

if __name__ == "__main__":
    test_final_aspect_calculation()