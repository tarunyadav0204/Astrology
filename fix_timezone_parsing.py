#!/usr/bin/env python3
"""
Script to replace timezone parsing code with centralized utility function
"""

import re

files_to_fix = [
    'backend/calculators/friendship_calculator.py',
    'backend/calculators/kalachakra_dasha_calculator.py',
    'backend/calculators/real_transit_calculator.py',
    'backend/calculators/transit_calculator.py',
    'backend/calculators/yogi_calculator.py',
    'backend/career_analysis/career_significator_analyzer.py',
    'backend/event_prediction/dasha_integration.py',
    'backend/event_prediction/yogi_analyzer.py',
    'backend/main.py',
    'backend/marriage_analysis/marriage_analyzer.py',
]

# Pattern to find and replace
old_pattern = r'''            if 6\.0 <= .*?latitude.*? <= 37\.0 and 68\.0 <= .*?longitude.*? <= 97\.0:
                tz_offset = 5\.5
            else:
                tz_offset = 0
                if .*?\.get\('timezone', ''\)\.startswith\('UTC'\):
                    tz_str = .*?\['timezone'\]\[3:\]
                    if tz_str and ':' in tz_str:
                        sign = 1 if tz_str\[0\] == '\+' else -1
                        parts = tz_str\[1:\]\.split\(':'\)
                        tz_offset = sign \* \(float\(parts\[0\]\) \+ float\(parts\[1\]\)/60\)'''

new_code = '''            # Get timezone offset using centralized utility
            from utils.timezone_service import parse_timezone_offset
            tz_offset = parse_timezone_offset(
                birth_data.get('timezone', ''),
                birth_data.get('latitude'),
                birth_data.get('longitude')
            )'''

print("Files to update:")
for f in files_to_fix:
    print(f"  - {f}")

print("\nRun this script to apply the fix to all files.")
print("Or manually update each file to use: from utils.timezone_service import parse_timezone_offset")
