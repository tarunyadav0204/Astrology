def validate_ascendant_calculation(birth_data, calculated_ascendant):
    """Validate ascendant calculation"""
    import swisseph as swe
    
    # CRITICAL: Set Lahiri Ayanamsa before any calculation
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    date_parts = birth_data['date'].split('-')
    time_parts = birth_data['time'].split(':')
    
    year = int(date_parts[0])
    month = int(date_parts[1])
    day = int(date_parts[2])
    hour = float(time_parts[0]) + float(time_parts[1])/60
    
    # Use same timezone logic as main chart calculator
    tz_offset = 0
    if 'timezone' in birth_data and birth_data['timezone']:
        tz_str = str(birth_data['timezone']).strip()
        
        # Remove UTC/GMT prefix if present
        if tz_str.upper().startswith('UTC'):
            tz_str = tz_str[3:]
        elif tz_str.upper().startswith('GMT'):
            tz_str = tz_str[3:]
            
        tz_str = tz_str.strip()
        
        if tz_str:
            try:
                if ':' in tz_str:
                    # Fix: Default to positive unless explicitly negative
                    sign = -1 if tz_str.startswith('-') else 1
                    clean_str = tz_str.lstrip('+-')
                    parts = clean_str.split(':')
                    tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
                else:
                    tz_offset = float(tz_str)
            except (ValueError, IndexError):
                print(f"Warning: Could not parse timezone '{tz_str}'. Defaulting to UTC.")
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