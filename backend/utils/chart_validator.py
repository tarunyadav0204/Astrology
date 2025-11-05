def validate_ascendant_calculation(birth_data, calculated_ascendant):
    """Validate ascendant calculation"""
    import swisseph as swe
    
    date_parts = birth_data['date'].split('-')
    time_parts = birth_data['time'].split(':')
    
    year = int(date_parts[0])
    month = int(date_parts[1])
    day = int(date_parts[2])
    hour = float(time_parts[0]) + float(time_parts[1])/60
    
    if 6.0 <= birth_data['latitude'] <= 37.0 and 68.0 <= birth_data['longitude'] <= 97.0:
        tz_offset = 5.5
    else:
        tz_offset = 0
    
    utc_hour = hour - tz_offset
    jd = swe.julday(year, month, day, utc_hour)
    
    houses_data = swe.houses(jd, birth_data['latitude'], birth_data['longitude'], b'P')
    ayanamsa = swe.get_ayanamsa_ut(jd)
    
    ascendant_tropical = houses_data[1][0]
    ascendant_sidereal = (ascendant_tropical - ayanamsa) % 360
    
    difference = abs(calculated_ascendant - ascendant_sidereal)
    if difference > 180:
        difference = 360 - difference
    
    sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    return {
        'is_valid': difference < 0.1,
        'calculated_ascendant': calculated_ascendant,
        'validated_ascendant': ascendant_sidereal,
        'difference_degrees': difference,
        'calculated_sign': sign_names[int(calculated_ascendant / 30)],
        'validated_sign': sign_names[int(ascendant_sidereal / 30)]
    }