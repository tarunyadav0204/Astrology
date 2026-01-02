#!/usr/bin/env python3
"""
Find exact parameters (time/ayanamsa) that match AstroSage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import swisseph as swe

def find_astrosage_parameters():
    print("=== FINDING ASTROSAGE PARAMETERS ===")
    
    # Target: Moon position that gives Nov 4, 1995 end date
    target_moon_pos = 188.4544  # From previous test - gives Nov 3 (closest)
    
    # Base parameters
    base_date = '1980-04-02'
    base_time = '14:55'
    base_lat = 29.1492
    base_lon = 75.7217
    base_tz = 5.5
    
    print(f"Target Moon position: {target_moon_pos:.4f}°")
    print(f"Base parameters: {base_date} {base_time} IST, {base_lat}°N {base_lon}°E")
    
    # Test different times around 14:55
    print(f"\n=== TESTING DIFFERENT BIRTH TIMES ===")
    
    base_datetime = datetime(1980, 4, 2, 14, 55)
    
    for minutes_offset in [-10, -5, -2, -1, 0, 1, 2, 5, 10]:
        test_time = base_datetime + timedelta(minutes=minutes_offset)
        test_hour = test_time.hour + test_time.minute/60.0
        utc_hour = test_hour - base_tz
        
        jd = swe.julday(1980, 4, 2, utc_hour)
        swe.set_sid_mode(27, 0, 0)  # True Chitra
        moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
        
        diff = abs(moon_pos - target_moon_pos)
        time_str = test_time.strftime('%H:%M')
        
        print(f"Time {time_str}: Moon {moon_pos:.4f}°, Diff {diff:.4f}°")
        
        if diff < 0.002:  # Very close match
            print(f"  *** EXCELLENT MATCH! ***")
    
    # Test different Ayanamsa modes
    print(f"\n=== TESTING DIFFERENT AYANAMSA MODES ===")
    
    # Standard time: 14:55
    hour = 14 + 55/60.0
    utc_hour = hour - base_tz
    jd = swe.julday(1980, 4, 2, utc_hour)
    
    ayanamsa_modes = [
        (0, "Lahiri"),
        (1, "De Luce"),
        (2, "Raman"),
        (3, "Ushashashi"),
        (4, "Krishnamurti"),
        (5, "Djwhal Khul"),
        (6, "Yukteshwar"),
        (7, "JN Bhasin"),
        (27, "True Chitra"),
        (28, "True Lahiri"),
        (29, "True Pushya"),
    ]
    
    for mode, name in ayanamsa_modes:
        try:
            swe.set_sid_mode(mode, 0, 0)
            moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
            diff = abs(moon_pos - target_moon_pos)
            
            print(f"Mode {mode:2d} ({name:15s}): Moon {moon_pos:.4f}°, Diff {diff:.4f}°")
            
            if diff < 0.002:
                print(f"  *** EXCELLENT MATCH! ***")
        except:
            print(f"Mode {mode:2d} ({name:15s}): ERROR")
    
    # Test custom Ayanamsa offset
    print(f"\n=== TESTING CUSTOM AYANAMSA OFFSETS ===")
    
    # Use True Chitra as base and add small offsets
    base_mode = 27
    
    for offset_arcsec in [-30, -20, -10, -5, 0, 5, 10, 20, 30]:
        offset_deg = offset_arcsec / 3600.0  # Convert arcseconds to degrees
        
        try:
            swe.set_sid_mode(base_mode, 0, offset_deg)
            moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
            diff = abs(moon_pos - target_moon_pos)
            
            print(f"True Chitra + {offset_arcsec:+3d}\": Moon {moon_pos:.4f}°, Diff {diff:.4f}°")
            
            if diff < 0.002:
                print(f"  *** EXCELLENT MATCH! ***")
        except:
            print(f"True Chitra + {offset_arcsec:+3d}\": ERROR")
    
    # Test if seconds matter in birth time
    print(f"\n=== TESTING BIRTH TIME WITH SECONDS ===")
    
    base_hour = 14 + 55/60.0
    
    for seconds in [0, 15, 30, 45]:
        test_hour = base_hour + seconds/3600.0
        utc_hour = test_hour - base_tz
        
        jd = swe.julday(1980, 4, 2, utc_hour)
        swe.set_sid_mode(27, 0, 0)
        moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
        diff = abs(moon_pos - target_moon_pos)
        
        time_str = f"14:55:{seconds:02d}"
        print(f"Time {time_str}: Moon {moon_pos:.4f}°, Diff {diff:.4f}°")
        
        if diff < 0.002:
            print(f"  *** EXCELLENT MATCH! ***")

if __name__ == "__main__":
    find_astrosage_parameters()