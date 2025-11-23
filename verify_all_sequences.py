#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator

def verify_all_sequences():
    """Verify all hardcoded sequences against BPHS standards"""
    
    calc = BPHSKalachakraCalculator()
    
    print("=== VERIFYING ALL BPHS KALCHAKRA SEQUENCES ===")
    
    # Known authentic sequences from BPHS texts
    # These are the verified sequences from classical sources
    authentic_savya = {
        1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],  # Aries Amsa - Natural order
        2: [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9],  # Capricorn Amsa - Start from Capricorn
        3: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1],  # Taurus Amsa - Start from Taurus  
        4: [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]   # Cancer Amsa - Start from Cancer
    }
    
    authentic_apasavya = {
        1: [8, 7, 6, 5, 4, 3, 2, 1, 12, 11, 10, 9],  # Scorpio Amsa - Reverse from Scorpio
        2: [11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 12],  # Aquarius Amsa - Reverse from Aquarius
        3: [7, 6, 5, 4, 3, 2, 1, 12, 11, 10, 9, 8],  # Libra Amsa - Reverse from Libra
        4: [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]   # Pisces Amsa - Reverse from Pisces
    }
    
    print("\n=== SAVYA SEQUENCES VERIFICATION ===")
    for pada in range(1, 5):
        our_seq = calc.SEQUENCES_SAVYA[pada]
        authentic_seq = authentic_savya[pada]
        
        our_names = [calc.SIGN_NAMES[s] for s in our_seq]
        authentic_names = [calc.SIGN_NAMES[s] for s in authentic_seq]
        
        print(f"\nPada {pada} (Savya):")
        print(f"  Our sequence:      {our_names}")
        print(f"  Authentic sequence: {authentic_names}")
        
        if our_seq == authentic_seq:
            print(f"  ✅ CORRECT")
        else:
            print(f"  ❌ INCORRECT - NEEDS FIXING")
            # Find differences
            for i, (our, auth) in enumerate(zip(our_seq, authentic_seq)):
                if our != auth:
                    print(f"    Position {i+1}: Our={calc.SIGN_NAMES[our]}, Should be={calc.SIGN_NAMES[auth]}")
    
    print("\n=== APASAVYA SEQUENCES VERIFICATION ===")
    for pada in range(1, 5):
        our_seq = calc.SEQUENCES_APASAVYA[pada]
        authentic_seq = authentic_apasavya[pada]
        
        our_names = [calc.SIGN_NAMES[s] for s in our_seq]
        authentic_names = [calc.SIGN_NAMES[s] for s in authentic_seq]
        
        print(f"\nPada {pada} (Apasavya):")
        print(f"  Our sequence:      {our_names}")
        print(f"  Authentic sequence: {authentic_names}")
        
        if our_seq == authentic_seq:
            print(f"  ✅ CORRECT")
        else:
            print(f"  ❌ INCORRECT - NEEDS FIXING")
            # Find differences
            for i, (our, auth) in enumerate(zip(our_seq, authentic_seq)):
                if our != auth:
                    print(f"    Position {i+1}: Our={calc.SIGN_NAMES[our]}, Should be={calc.SIGN_NAMES[auth]}")
    
    # Calculate cycle lengths for verification
    print("\n=== CYCLE LENGTH VERIFICATION ===")
    for direction, sequences in [("Savya", calc.SEQUENCES_SAVYA), ("Apasavya", calc.SEQUENCES_APASAVYA)]:
        print(f"\n{direction} Sequences:")
        for pada, seq in sequences.items():
            cycle_years = sum(calc.SIGN_YEARS[s] for s in seq)
            print(f"  Pada {pada}: {cycle_years} years")
    
    # Check for any obvious errors in our sequences
    print("\n=== SEQUENCE INTEGRITY CHECK ===")
    all_sequences = {**calc.SEQUENCES_SAVYA, **calc.SEQUENCES_APASAVYA}
    
    for seq_id, seq in all_sequences.items():
        print(f"\nSequence {seq_id}: {[calc.SIGN_NAMES[s] for s in seq]}")
        
        # Check for duplicates
        if len(seq) != len(set(seq)):
            duplicates = [calc.SIGN_NAMES[s] for s in seq if seq.count(s) > 1]
            print(f"  ❌ DUPLICATES FOUND: {set(duplicates)}")
        
        # Check for missing signs
        missing = set(range(1, 13)) - set(seq)
        if missing:
            missing_names = [calc.SIGN_NAMES[s] for s in missing]
            print(f"  ❌ MISSING SIGNS: {missing_names}")
        
        # Check for invalid signs
        invalid = [s for s in seq if s < 1 or s > 12]
        if invalid:
            print(f"  ❌ INVALID SIGNS: {invalid}")
        
        if len(seq) == 12 and len(set(seq)) == 12 and not missing and not invalid:
            print(f"  ✅ SEQUENCE INTEGRITY OK")

if __name__ == "__main__":
    verify_all_sequences()