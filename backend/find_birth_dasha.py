#!/usr/bin/env python3
"""
Determine the correct birth Mahadasha by working backwards from AstroSage result
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import swisseph as swe

def find_correct_birth_dasha():
    birth_datetime = datetime(1980, 4, 2, 14, 55)
    astrosage_rahu_end = datetime(1995, 11, 4)
    
    print("=== FINDING CORRECT BIRTH MAHADASHA ===")
    print(f"Birth: {birth_datetime.strftime('%B %d, %Y at %H:%M')}")
    print(f"Known: Rahu Mahadasha ends {astrosage_rahu_end.strftime('%B %d, %Y')}")
    print()
    
    # Dasha periods and order
    dasha_periods = {'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7, 'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17}
    planet_order = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
    
    # Calculate Moon nakshatra to verify
    time_parts = '14:55'.split(':')
    hour = float(time_parts[0]) + float(time_parts[1])/60
    utc_hour = hour - 5.5
    
    jd = swe.julday(1980, 4, 2, utc_hour)
    # Set Lahiri Ayanamsa for accurate Vedic calculations

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
    
    nakshatra_index = int(moon_pos / 13.333333333333334)
    nakshatra_lords = [
        'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',
        'Saturn', 'Mercury', 'Ketu', 'Venus', 'Sun', 'Moon', 'Mars',
        'Rahu', 'Jupiter', 'Saturn', 'Mercury', 'Ketu', 'Venus',
        'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
    ]
    
    moon_lord = nakshatra_lords[nakshatra_index]
    print(f"Moon nakshatra lord: {moon_lord} (Swati nakshatra)")
    print()
    
    # Work backwards from Rahu end to find what Mahadasha was running at birth
    print("WORKING BACKWARDS FROM RAHU END DATE:")
    
    # If Rahu ended on Nov 4, 1995, when did it start?
    rahu_start = astrosage_rahu_end - timedelta(days=18 * 365.25)
    print(f"If Rahu was full 18 years: Started {rahu_start.strftime('%B %d, %Y')}")
    print(f"Birth was {birth_datetime.strftime('%B %d, %Y')} - that's {(birth_datetime - rahu_start).days} days after Rahu start")
    print()
    
    # This means birth was NOT at Rahu start, so what Mahadasha was running?
    # Let's check each possible scenario
    
    print("TESTING EACH POSSIBLE BIRTH MAHADASHA:")
    print()
    
    for birth_planet in planet_order:
        print(f"SCENARIO: Born in {birth_planet.upper()} Mahadasha")
        
        # Find when this planet's dasha would have started
        # Work backwards from known Rahu end
        
        # Find Rahu's position in sequence starting from birth_planet
        birth_index = planet_order.index(birth_planet)
        rahu_index = planet_order.index('Rahu')
        
        # How many planets between birth_planet and Rahu?
        if rahu_index >= birth_index:
            planets_between = rahu_index - birth_index
        else:
            planets_between = (9 - birth_index) + rahu_index
        
        # Calculate when birth_planet dasha would have started
        total_years_before_rahu = 0
        current_index = birth_index
        
        for i in range(planets_between):
            if i == 0:
                # Skip birth planet (we'll calculate its balance)
                continue
            else:
                current_index = (current_index + 1) % 9
                planet = planet_order[current_index]
                total_years_before_rahu += dasha_periods[planet]
        
        # When did the planet before Rahu end (= when Rahu started)?
        rahu_start_calc = astrosage_rahu_end - timedelta(days=18 * 365.25)
        birth_planet_start = rahu_start_calc - timedelta(days=total_years_before_rahu * 365.25)
        
        print(f"  {birth_planet} dasha would start: {birth_planet_start.strftime('%b %d, %Y')}")
        print(f"  Birth date: {birth_datetime.strftime('%b %d, %Y')}")
        
        # Check if birth falls within this planet's period
        birth_planet_end = birth_planet_start + timedelta(days=dasha_periods[birth_planet] * 365.25)
        print(f"  {birth_planet} dasha would end: {birth_planet_end.strftime('%b %d, %Y')}")
        
        if birth_planet_start <= birth_datetime <= birth_planet_end:
            # Calculate balance
            elapsed_days = (birth_datetime - birth_planet_start).days
            total_days = dasha_periods[birth_planet] * 365.25
            balance_fraction = 1 - (elapsed_days / total_days)
            remaining_years = dasha_periods[birth_planet] * balance_fraction
            
            print(f"  *** MATCH! Birth falls in {birth_planet} period ***")
            print(f"  Elapsed: {elapsed_days} days")
            print(f"  Balance: {balance_fraction:.6f} ({remaining_years:.2f} years remaining)")
            
            # Verify: does this lead to correct Rahu end?
            remaining_end = birth_datetime + timedelta(days=remaining_years * 365.25)
            
            # Add intermediate dashas
            verification_date = remaining_end
            current_idx = (birth_index + 1) % 9
            
            while planet_order[current_idx] != 'Rahu':
                planet = planet_order[current_idx]
                verification_date += timedelta(days=dasha_periods[planet] * 365.25)
                current_idx = (current_idx + 1) % 9
            
            # Add full Rahu period
            final_rahu_end = verification_date + timedelta(days=18 * 365.25)
            
            print(f"  Verification: Rahu would end {final_rahu_end.strftime('%b %d, %Y')}")
            print(f"  AstroSage says: {astrosage_rahu_end.strftime('%b %d, %Y')}")
            print(f"  Difference: {(final_rahu_end - astrosage_rahu_end).days} days")
            
        print()

if __name__ == "__main__":
    find_correct_birth_dasha()