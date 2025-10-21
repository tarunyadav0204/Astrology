# Formula explanation functions for Classical Shadbala

def get_sthana_bala_formulas(planet: str, planet_data: dict, jd: float) -> dict:
    """Get detailed formulas for Sthana Bala calculation with actual values"""
    current_longitude = planet_data.get('longitude', 0)
    current_sign = planet_data.get('sign', 0)
    current_degree = planet_data.get('degree', 0)
    house = planet_data.get('house', 1)
    
    # Import calculation functions to get actual values
    try:
        from classical_shadbala import (
            calculate_authentic_uccha_bala, calculate_saptavargaja_bala, 
            calculate_ojhayugmarasyamsa_bala, calculate_kendra_bala, calculate_drekkana_bala,
            EXALTATION_DATA
        )
        
        # Calculate actual values
        uccha_value = calculate_authentic_uccha_bala(planet, planet_data)
        saptavargaja_value = calculate_saptavargaja_bala(planet, planet_data, jd)
        ojha_value = calculate_ojhayugmarasyamsa_bala(planet, planet_data)
        kendra_value = calculate_kendra_bala(planet_data)
        drekkana_value = calculate_drekkana_bala(planet, planet_data)
        
        total_sthana = uccha_value + saptavargaja_value + ojha_value + kendra_value + drekkana_value
        
    except ImportError:
        # Fallback if import fails
        uccha_value = saptavargaja_value = ojha_value = kendra_value = drekkana_value = 0
        total_sthana = 0
    
    formulas = {
        'total_formula': f'Sthana Bala = {uccha_value:.1f} + {saptavargaja_value:.1f} + {ojha_value:.1f} + {kendra_value:.1f} + {drekkana_value:.1f} = {total_sthana:.1f}',
        'components': {}
    }
    
    # Uccha Bala with actual calculation
    if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        exalt_data = {
            'Sun': {'sign': 'Aries', 'degree': 10, 'sign_num': 0},
            'Moon': {'sign': 'Taurus', 'degree': 3, 'sign_num': 1},
            'Mars': {'sign': 'Capricorn', 'degree': 28, 'sign_num': 9},
            'Mercury': {'sign': 'Virgo', 'degree': 15, 'sign_num': 5},
            'Jupiter': {'sign': 'Cancer', 'degree': 5, 'sign_num': 3},
            'Venus': {'sign': 'Pisces', 'degree': 27, 'sign_num': 11},
            'Saturn': {'sign': 'Libra', 'degree': 20, 'sign_num': 6}
        }[planet]
        
        exalt_longitude = exalt_data['sign_num'] * 30 + exalt_data['degree']
        diff = abs(current_longitude - exalt_longitude)
        if diff > 180:
            diff = 360 - diff
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        current_sign_name = sign_names[current_sign]
        
        formulas['components']['uccha_bala'] = {
            'formula': f'Uccha Bala = 60 × (1 - {diff:.1f}°/180°) = {uccha_value:.1f}',
            'explanation': f'{planet} exalts at {exalt_data["sign"]} {exalt_data["degree"]}°, currently at {current_sign_name} {current_degree:.1f}°',
            'current_position': f'Current: {current_sign_name} {current_degree:.1f}° ({current_longitude:.2f}°)',
            'distance': f'Distance from exaltation: {diff:.1f}°',
            'calculated_value': f'{uccha_value:.1f} points'
        }
    else:
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        current_sign_name = sign_names[current_sign]
        
        formulas['components']['uccha_bala'] = {
            'formula': 'Uccha Bala = 0 (No exaltation data)',
            'current_position': f'Current: {current_sign_name} {current_degree:.1f}°',
            'calculated_value': '0 points'
        }
    
    # Saptavargaja Bala with honest implementation note
    formulas['components']['saptavargaja_bala'] = {
        'formula': f'Saptavargaja Bala = {saptavargaja_value:.1f} points',
        'explanation': 'Only Rasi + Hora + Drekkana properly calculated',
        'implementation_status': 'Rasi(calculated) + Hora(calculated) + Drekkana(calculated) + Others(NA - given average 8.5)',
        'calculated_value': f'{saptavargaja_value:.1f} points',
        'note': 'Saptamsa, Navamsa, Dwadasamsa, Trimsamsa = NA (not implemented, average used)'
    }
    
    # Ojhayugmarasyamsa Bala with actual calculation
    sign_type = 'Odd' if current_sign % 2 == 0 else 'Even'  # 0-indexed
    planet_gender = {
        'Sun': 'Male', 'Mars': 'Male', 'Jupiter': 'Male',
        'Moon': 'Female', 'Venus': 'Female',
        'Mercury': 'Neutral', 'Saturn': 'Neutral'
    }.get(planet, 'Neutral')
    
    gets_points = ((planet_gender == 'Male' and sign_type == 'Odd') or 
                   (planet_gender == 'Female' and sign_type == 'Even') or 
                   planet_gender == 'Neutral')
    
    formulas['components']['ojhayugmarasyamsa_bala'] = {
        'formula': f'Ojhayugmarasyamsa Bala = {"15" if gets_points else "0"} points',
        'explanation': f'{planet} is {planet_gender} planet, current sign is {sign_type}',
        'rule': 'Male planets strong in odd signs, Female planets strong in even signs',
        'calculation': f'{planet_gender} planet in {sign_type} sign = {ojha_value:.1f} points',
        'calculated_value': f'{ojha_value:.1f} points'
    }
    
    # Kendra Bala with actual calculation
    house_type = 'Kendra' if house in [1,4,7,10] else 'Panapara' if house in [2,5,8,11] else 'Apoklima'
    
    formulas['components']['kendra_bala'] = {
        'formula': f'Kendra Bala = {kendra_value:.1f} points',
        'explanation': f'House {house} is {house_type} house',
        'classification': 'Kendra: 1,4,7,10 (60pts) | Panapara: 2,5,8,11 (30pts) | Apoklima: 3,6,9,12 (15pts)',
        'calculation': f'House {house} ({house_type}) = {kendra_value:.1f} points',
        'calculated_value': f'{kendra_value:.1f} points'
    }
    
    # Drekkana Bala with actual calculation
    drekkana_num = int(current_degree / 10) + 1
    formulas['components']['drekkana_bala'] = {
        'formula': f'Drekkana Bala = {drekkana_value:.1f} points',
        'explanation': f'Current degree {current_degree:.2f}° falls in {drekkana_num} drekkana',
        'rule': 'Each sign divided into 3 drekkanas of 10° each',
        'calculation': f'Drekkana {drekkana_num} strength = {drekkana_value:.1f} points',
        'calculated_value': f'{drekkana_value:.1f} points'
    }
    
    return formulas

def get_dig_bala_formula(planet: str, planet_data: dict) -> dict:
    """Get Dig Bala formula explanation with actual values"""
    house = planet_data.get('house', 1)
    
    directional_houses = {
        'Sun': 10, 'Moon': 4, 'Mars': 10, 'Mercury': 1,
        'Jupiter': 1, 'Venus': 4, 'Saturn': 7
    }
    
    if planet not in directional_houses:
        return {
            'formula': 'Dig Bala = 0 (Not applicable for this planet)',
            'calculated_value': '0 points'
        }
    
    # Calculate actual Dig Bala value
    try:
        from classical_shadbala import calculate_authentic_dig_bala
        dig_value = calculate_authentic_dig_bala(planet, planet_data)
    except ImportError:
        dig_value = 0
    
    directional_house = directional_houses[planet]
    opposite_house = ((directional_house + 6 - 1) % 12) + 1
    
    if house == directional_house:
        status = "Full strength (own direction)"
    elif house == opposite_house:
        status = "No strength (opposite direction)"
    else:
        distance = min(abs(house - directional_house), 12 - abs(house - directional_house))
        status = f"Proportional strength (distance {distance} from best direction)"
    
    return {
        'formula': f'Dig Bala = {dig_value:.1f} points',
        'explanation': f'{planet} gets directional strength in house {directional_house}',
        'current_position': f'Currently in house {house}',
        'directional_house': f'Best direction: House {directional_house}',
        'opposite_house': f'Worst direction: House {opposite_house}',
        'calculation': f'House {house}: {status} = {dig_value:.1f} points',
        'calculated_value': f'{dig_value:.1f} points'
    }

def get_kala_bala_formulas(planet: str, planet_data: dict, birth_data: dict, jd: float) -> dict:
    """Get Kala Bala formula explanations with actual values"""
    birth_time = birth_data.get('time', '12:00')
    hour = int(birth_time.split(':')[0])
    is_day = 6 <= hour <= 18
    
    # Calculate actual Kala Bala components
    try:
        from classical_shadbala import (
            calculate_natonnata_bala, calculate_paksha_bala, calculate_tribhaga_bala,
            calculate_temporal_lords_bala, calculate_ayana_bala
        )
        
        natonnata_value = calculate_natonnata_bala(planet, birth_data)
        paksha_value = calculate_paksha_bala(planet, jd)
        tribhaga_value = calculate_tribhaga_bala(planet, birth_data)
        temporal_value = calculate_temporal_lords_bala(planet, birth_data, jd)
        ayana_value = calculate_ayana_bala(planet, jd)
        
        total_kala = natonnata_value + paksha_value + tribhaga_value + temporal_value + ayana_value
        
    except ImportError:
        natonnata_value = paksha_value = tribhaga_value = temporal_value = ayana_value = 0
        total_kala = 0
    
    # Determine if planet gets Natonnata strength
    day_planets = ['Sun', 'Jupiter', 'Venus']
    night_planets = ['Moon', 'Mars', 'Saturn']
    gets_natonnata = ((planet in day_planets and is_day) or (planet in night_planets and not is_day))
    
    return {
        'total_formula': f'Kala Bala = {natonnata_value:.1f} + {paksha_value:.1f} + {tribhaga_value:.1f} + {temporal_value:.1f} + {ayana_value:.1f} = {total_kala:.1f}',
        'components': {
            'natonnata_bala': {
                'formula': f'Natonnata Bala = {natonnata_value:.1f} points',
                'explanation': f'Birth time: {birth_time} ({"Day" if is_day else "Night"})',
                'day_planets': 'Sun, Jupiter, Venus strong during day',
                'night_planets': 'Moon, Mars, Saturn strong during night',
                'calculation': f'{planet} ({"day" if planet in day_planets else "night" if planet in night_planets else "neutral"} planet) at {"day" if is_day else "night"} = {natonnata_value:.1f} points',
                'calculated_value': f'{natonnata_value:.1f} points'
            },
            'paksha_bala': {
                'formula': f'Paksha Bala = {paksha_value:.1f} points',
                'explanation': 'Based on lunar phase (Moon-Sun angular distance)',
                'calculation': f'Calculated from Moon-Sun distance = {paksha_value:.1f} points',
                'rule': 'Waxing Moon (0-180°): Increasing strength | Waning Moon (180-360°): Decreasing strength',
                'calculated_value': f'{paksha_value:.1f} points'
            },
            'tribhaga_bala': {
                'formula': f'Tribhaga Bala = {tribhaga_value:.1f} points',
                'explanation': 'Day divided into periods with ruling planets',
                'periods': 'Morning (6-10): Sun, Jupiter | Noon (10-14): Sun, Mars | Afternoon (14-18): Venus, Mercury | Night: Moon, Saturn',
                'calculation': f'Time {birth_time}: {planet} gets {tribhaga_value:.1f} points',
                'calculated_value': f'{tribhaga_value:.1f} points'
            },
            'temporal_lords_bala': {
                'formula': f'Temporal Lords Bala = {temporal_value:.1f} points',
                'explanation': 'Strength from Year/Month/Day/Hour lords',
                'note': 'Simplified calculation (complex ephemeris calculations required for exact values)',
                'calculated_value': f'{temporal_value:.1f} points (average)'
            },
            'ayana_bala': {
                'formula': f'Ayana Bala = {ayana_value:.1f} points',
                'explanation': 'Based on Sun\'s declination (Uttarayana/Dakshinayana)',
                'calculation': f'Sun\'s seasonal strength affects all planets = {ayana_value:.1f} points',
                'calculated_value': f'{ayana_value:.1f} points'
            }
        }
    }

def get_chesta_bala_formula(planet: str, planet_data: dict, all_planets: dict, jd: float) -> dict:
    """Get Chesta Bala formula explanation with actual values"""
    
    # Calculate actual Chesta Bala value
    try:
        from classical_shadbala import calculate_authentic_chesta_bala
        chesta_value = calculate_authentic_chesta_bala(planet, planet_data, all_planets, jd)
    except ImportError:
        chesta_value = 0
    
    if planet == 'Sun':
        return {
            'formula': f'Chesta Bala = {chesta_value:.1f} points (Sun always gets full strength)',
            'explanation': 'Sun is always considered to be in motion',
            'calculation': f'{chesta_value:.1f} points (maximum)',
            'calculated_value': f'{chesta_value:.1f} points'
        }
    elif planet == 'Moon':
        # Calculate Moon-Sun distance
        sun_data = all_planets.get('Sun', {})
        moon_longitude = planet_data.get('longitude', 0)
        sun_longitude = sun_data.get('longitude', 0)
        
        distance = abs(moon_longitude - sun_longitude)
        if distance > 180:
            distance = 360 - distance
        
        return {
            'formula': f'Chesta Bala = 60 × ({distance:.1f}° / 180°) = {chesta_value:.1f}',
            'explanation': 'Moon\'s strength based on angular distance from Sun',
            'calculation': f'Distance from Sun: {distance:.1f}° = {chesta_value:.1f} points',
            'rule': 'Farther from Sun = stronger Moon (Max at Full Moon 180°)',
            'calculated_value': f'{chesta_value:.1f} points'
        }
    else:
        avg_motions = {
            'Mars': 0.5, 'Mercury': 1.0, 'Jupiter': 0.083,
            'Venus': 1.0, 'Saturn': 0.033
        }
        
        avg_motion = avg_motions.get(planet, 0.5)
        
        return {
            'formula': f'Chesta Bala = {chesta_value:.1f} points',
            'explanation': f'Based on actual daily motion vs average motion',
            'average_motion': f'{planet} average: {avg_motion}°/day',
            'calculation': f'Actual motion compared to {avg_motion}°/day average = {chesta_value:.1f} points',
            'rule': 'Faster motion = higher strength | Retrograde = maximum strength',
            'calculated_value': f'{chesta_value:.1f} points'
        }

def get_naisargika_bala_formula(planet: str) -> dict:
    """Get Naisargika Bala formula explanation with actual values"""
    natural_strengths = {
        'Sun': 60.0, 'Moon': 51.43, 'Mars': 17.14, 'Mercury': 25.71,
        'Jupiter': 34.29, 'Venus': 42.86, 'Saturn': 8.57
    }
    
    planet_value = natural_strengths.get(planet, 0)
    
    return {
        'formula': f'Naisargika Bala = {planet_value} points (fixed classical value)',
        'explanation': 'Inherent strength of each planet as per Brihat Parashara Hora Shastra',
        'classical_ranking': 'Sun(60) > Moon(51.43) > Venus(42.86) > Jupiter(34.29) > Mercury(25.71) > Mars(17.14) > Saturn(8.57)',
        'current_planet': f'{planet} = {planet_value} points',
        'calculated_value': f'{planet_value} points',
        'source': 'Brihat Parashara Hora Shastra, Chapter on Planetary Strengths'
    }

def get_drik_bala_formula(planet: str, planet_data: dict, all_planets: dict) -> dict:
    """Get Drik Bala formula explanation with actual values"""
    
    # Calculate actual Drik Bala value
    try:
        from classical_shadbala import calculate_authentic_drik_bala
        drik_value = calculate_authentic_drik_bala(planet, planet_data, all_planets)
    except ImportError:
        drik_value = 0
    
    return {
        'formula': f'Drik Bala = {drik_value:.1f} points',
        'explanation': 'Strength gained/lost from planetary aspects',
        'aspects': {
            'all_planets': 'Full aspect on 7th house',
            'mars_special': '4th and 8th house aspects (75% strength)',
            'jupiter_special': '5th and 9th house aspects (75% strength)',
            'saturn_special': '3rd and 10th house aspects (75% strength)'
        },
        'calculation': f'Net aspectual influence = {drik_value:.1f} points',
        'benefics': 'Jupiter, Venus, Mercury (add strength)',
        'malefics': 'Mars, Saturn, Sun (reduce strength)',
        'orbs': 'Conjunction: 15° | Opposition: 12° | Trine: 8° | Square: 8° | Sextile: 6°',
        'range': 'Drik Bala ranges from -30 to +30 points',
        'calculated_value': f'{drik_value:.1f} points'
    }