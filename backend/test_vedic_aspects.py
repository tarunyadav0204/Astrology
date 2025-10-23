#!/usr/bin/env python3

def test_vedic_aspect_logic():
    print("Understanding Vedic Aspect Logic:")
    print("=" * 40)
    
    # Mars aspects: 1st (conjunction), 4th, 7th, 8th
    mars_aspects = [1, 4, 7, 8]
    
    print("Mars in 1st house can aspect:")
    mars_house = 1
    for aspect in mars_aspects:
        if aspect == 1:
            target_house = mars_house  # Conjunction = same house
        else:
            # Calculate target house: (mars_house + aspect - 1) with wraparound
            target_house = ((mars_house + aspect - 2) % 12) + 1
        print(f"  {aspect}th aspect → {target_house}th house")
    
    print()
    print("Mars in 5th house can aspect:")
    mars_house = 5
    for aspect in mars_aspects:
        if aspect == 1:
            target_house = mars_house  # Conjunction = same house
        else:
            # Calculate target house: (mars_house + aspect - 1) with wraparound
            target_house = ((mars_house + aspect - 2) % 12) + 1
        print(f"  {aspect}th aspect → {target_house}th house")
    
    print()
    print("Reverse calculation - given Mars position and target, find aspect:")
    
    test_cases = [
        (1, 1),   # Mars 1st → 1st = 1st aspect (conjunction)
        (1, 4),   # Mars 1st → 4th = 4th aspect
        (1, 7),   # Mars 1st → 7th = 7th aspect
        (1, 8),   # Mars 1st → 8th = 8th aspect
        (5, 5),   # Mars 5th → 5th = 1st aspect (conjunction)
        (5, 8),   # Mars 5th → 8th = 4th aspect
        (5, 11),  # Mars 5th → 11th = 7th aspect
        (5, 12),  # Mars 5th → 12th = 8th aspect
    ]
    
    for mars_pos, target_pos in test_cases:
        # Calculate which aspect this represents
        if mars_pos == target_pos:
            aspect_num = 1  # Conjunction
        else:
            # Find which aspect number produces this target
            aspect_num = None
            for test_aspect in mars_aspects:
                if test_aspect == 1:
                    continue
                calculated_target = ((mars_pos + test_aspect - 2) % 12) + 1
                if calculated_target == target_pos:
                    aspect_num = test_aspect
                    break
        
        is_valid = aspect_num in mars_aspects if aspect_num else False
        print(f"Mars {mars_pos}th → {target_pos}th = {aspect_num}th aspect, Valid: {is_valid}")

if __name__ == "__main__":
    test_vedic_aspect_logic()