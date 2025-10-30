#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import swisseph as swe
from datetime import datetime

def test_sunrise():
    date = "2024-01-15"
    lat = 28.6139  # Delhi
    lon = 77.2090
    
    print(f"Testing sunrise/sunset for {date} at {lat}, {lon}")
    
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    julian_day = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 12.0)
    
    print(f"Julian Day: {julian_day}")
    
    geopos = [float(lon), float(lat), 0.0]
    print(f"Geopos: {geopos}")
    
    sunrise_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_RISE, geopos)
    sunset_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_SET, geopos)
    
    print(f"Sunrise result: {sunrise_result}")
    print(f"Sunset result: {sunset_result}")
    
    if sunrise_result[0] == 0 and sunset_result[0] == 0:
        sunrise_jd = sunrise_result[1][0]
        sunset_jd = sunset_result[1][0]
        
        print(f"Sunrise JD: {sunrise_jd}")
        print(f"Sunset JD: {sunset_jd}")
        print(f"Sunset > Sunrise: {sunset_jd > sunrise_jd}")
        
        # Convert to readable time
        year, month, day, hour, minute, second = swe.jdut1_to_utc(sunrise_jd, 1)
        sunrise_dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        
        year, month, day, hour, minute, second = swe.jdut1_to_utc(sunset_jd, 1)
        sunset_dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        
        print(f"Sunrise: {sunrise_dt}")
        print(f"Sunset: {sunset_dt}")

if __name__ == "__main__":
    test_sunrise()