#!/usr/bin/env python3
"""Verify Jupiter position on specific dates"""

import swisseph as swe
from datetime import datetime

swe.set_sid_mode(swe.SIDM_LAHIRI)

dates_to_check = [
    '2026-06-01',
    '2026-06-02',
    '2026-10-29',
    '2026-10-30',
    '2026-10-31'
]

sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
              'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

print("Jupiter Position Verification:")
print("=" * 80)

for date_str in dates_to_check:
    date = datetime.strptime(date_str, '%Y-%m-%d')
    jd = swe.julday(date.year, date.month, date.day, 12.0)
    
    result = swe.calc_ut(jd, swe.JUPITER, swe.FLG_SIDEREAL)
    longitude = result[0][0]
    sign_idx = int(longitude / 30)
    degree = longitude % 30
    
    print(f"{date_str}: {sign_names[sign_idx]} {degree:.2f}° (longitude: {longitude:.2f}°)")

print("=" * 80)
print("\nConclusion:")
print("If Jupiter is in Gemini on 2026-06-01 and Cancer on 2026-06-02,")
print("then the transit data is CORRECT.")
