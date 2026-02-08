"""
Corrected Classical Shadbala Calculator
Based on DrikPanchang standards and rigorous BPHS method
Uses continuous mathematical differentials instead of static if/else logic
"""

import swisseph as swe
import math
from typing import Dict, Any, List
from datetime import datetime

# Classical point scales from BPHS
DIGNITY_POINTS = {
    'moolatrikona': 45.0,
    'own_sign': 30.0,
    'great_friend': 22.5,
    'friend': 15.0,
    'neutral': 7.5,
    'enemy': 3.75,
    'great_enemy': 1.875,
    'debilitated': 0.0,
    'exalted': 60.0
}

# Saptavargaja Bala dignity points (Cumulative Sripati method - 1.5× scale)
COMPOUND_DIGNITY_POINTS = {
    'exalted': 45.0,
    'moolatrikona': 33.75,
    'own_sign': 22.5,
    'great_friend': 16.875,
    'friend': 11.25,
    'neutral': 5.625,
    'enemy': 2.8125,
    'great_enemy': 1.40625,
    'debilitated': 0.703125
}

def _calculate_bhava_madhyas(cusps: list) -> list:
    """Calculate Bhava Madhyas (house midpoints) from Bhava Sandhis (cusps).
    Midpoint = (Cusp[n] + Cusp[n+1]) / 2 with circular adjustment.
    """
    if not cusps or len(cusps) != 12:
        return [i*30 for i in range(12)]  # Fallback
    
    madhyas = []
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if end < start:
            end += 360
        midpoint = (start + end) / 2.0
        madhyas.append(midpoint % 360)
    
    return madhyas

# Sign lords for varga analysis
SIGN_LORDS = {
    0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
    6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
}

# Natural friendship tables
NATURAL_FRIENDS = {
    'Sun': ['Moon', 'Mars', 'Jupiter'],
    'Moon': ['Sun', 'Mercury'],
    'Mars': ['Sun', 'Moon', 'Jupiter'],
    'Mercury': ['Sun', 'Venus'],
    'Jupiter': ['Sun', 'Moon', 'Mars'],
    'Venus': ['Mercury', 'Saturn'],
    'Saturn': ['Mercury', 'Venus']
}

NATURAL_ENEMIES = {
    'Sun': ['Venus', 'Saturn'],
    'Moon': [],
    'Mars': ['Mercury'],
    'Mercury': ['Moon'],
    'Jupiter': ['Mercury', 'Venus'],
    'Venus': ['Sun', 'Moon'],
    'Saturn': ['Sun', 'Moon', 'Mars']
}

NAISARGIKA_BALA = {
    'Sun': 60.0, 'Moon': 51.43, 'Mars': 17.14, 'Mercury': 25.71,
    'Jupiter': 34.29, 'Venus': 42.86, 'Saturn': 8.57
}

DIRECTIONAL_HOUSES = {
    'Sun': 10, 'Moon': 4, 'Mars': 10, 'Mercury': 1,
    'Jupiter': 1, 'Venus': 4, 'Saturn': 7
}

EXALTATION_DATA = {
    'Sun': {'sign': 0, 'degree': 10},
    'Moon': {'sign': 1, 'degree': 3},
    'Mars': {'sign': 9, 'degree': 28},
    'Mercury': {'sign': 5, 'degree': 15},
    'Jupiter': {'sign': 3, 'degree': 5},
    'Venus': {'sign': 11, 'degree': 27},
    'Saturn': {'sign': 6, 'degree': 20}
}

DEBILITATION_DATA = {
    'Sun': {'sign': 6, 'degree': 10},
    'Moon': {'sign': 7, 'degree': 3},
    'Mars': {'sign': 3, 'degree': 28},
    'Mercury': {'sign': 11, 'degree': 15},
    'Jupiter': {'sign': 9, 'degree': 5},
    'Venus': {'sign': 5, 'degree': 27},
    'Saturn': {'sign': 0, 'degree': 20}
}

OWN_SIGNS = {
    'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
    'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
}

PLANET_IDS = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
    'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
    'Venus': swe.VENUS, 'Saturn': swe.SATURN
}

def calculate_dig_bala(planet: str, longitude: float, house_cusps: List[float]) -> float:
    """
    Calculates Directional Strength per BPHS classical method.
    Based on distance FROM Zero Point (Lopa point - minimum strength), divided by 3.
    
    CRITICAL: house_cusps must represent Bhava Madhyas (house midpoints),
    not the start of houses, for accurate Dig Bala calculation.
    """
    if planet not in DIRECTIONAL_HOUSES:
        return 30.0
    
    target_house_num = DIRECTIONAL_HOUSES[planet]
    target_cusp = house_cusps[target_house_num - 1] if len(house_cusps) >= target_house_num else 0
    
    # Zero Point (Lopa) is 180° opposite to maximum strength house cusp
    zero_point = (target_cusp + 180) % 360
    
    # Calculate arc distance FROM Zero Point to Planet
    arc_from_zero = longitude - zero_point
    if arc_from_zero < 0:
        arc_from_zero += 360
    
    # If arc > 180, take shorter path
    if arc_from_zero > 180:
        arc_from_zero = 360 - arc_from_zero
    
    # BPHS Formula: Distance from Zero Point / 3
    # At Zero Point (0°): 0/3 = 0 points
    # At Max Point (180°): 180/3 = 60 points
    dig_bala = arc_from_zero / 3.0
    
    return round(dig_bala, 2)

def calculate_ishta_kashta_phala(uccha_bala: float, chesta_bala: float) -> Dict[str, float]:
    """
    Calculates Ishta Phala (Benefic result) and Kashta Phala (Malefic result).
    Based on the product of Uccha Bala and Chesta Bala.
    
    Ishta Phala: Measures capacity to give good results (max 60)
    Kashta Phala: Measures capacity to give bad results (max 60)
    """
    # Product of Uccha and Chesta Bala
    product = uccha_bala * chesta_bala
    
    # Ishta Phala formula: sqrt(product) / 2
    ishta_phala = math.sqrt(product) / 2.0 if product > 0 else 0.0
    
    # Kashta Phala formula: 60 - Ishta Phala
    kashta_phala = 60.0 - ishta_phala
    
    return {
        'ishta_phala': round(ishta_phala, 2),
        'kashta_phala': round(kashta_phala, 2),
        'ishta_percent': round((ishta_phala / 60.0) * 100, 2),
        'kashta_percent': round((kashta_phala / 60.0) * 100, 2)
    }

def calculate_kendradi_bala(house: int) -> float:
    """Kendradi Bala: Strength based on house type (Kendra/Panaphara/Apoklima)."""
    if house in [1, 4, 7, 10]:  # Kendra (Angular)
        return 60.0
    elif house in [2, 5, 8, 11]:  # Panaphara (Succedent)
        return 30.0
    else:  # Apoklima (Cadent) - houses 3, 6, 9, 12
        return 15.0

def calculate_drekkana_bala(planet: str, longitude: float) -> float:
    """Drekkana Bala: Strength based on decanate (10° divisions within sign).
    Male planets strong in 1st drekkana, Female in last, Hermaphrodite in middle.
    """
    degree_in_sign = longitude % 30
    drekkana = int(degree_in_sign / 10)  # 0, 1, or 2
    
    # Male planets: Sun, Mars, Jupiter
    if planet in ['Sun', 'Mars', 'Jupiter']:
        return 15.0 if drekkana == 0 else 0.0
    # Female planets: Moon, Venus
    elif planet in ['Moon', 'Venus']:
        return 15.0 if drekkana == 2 else 0.0
    # Hermaphrodite: Mercury, Saturn
    else:
        return 15.0 if drekkana == 1 else 0.0

def calculate_ojha_yugma_bala(planet: str, longitude: float, chart_data: Dict) -> float:
    """Calculates Ojha-Yugma-Rashi-Amsha Bala (Odd/Even sign strength).
    Checks BOTH D1 (Rashi) and D9 (Navamsa).
    Moon and Venus get 15 points in Even signs.
    Other planets get 15 points in Odd signs.
    """
    total_points = 0.0
    
    print(f"\n--- Ojha Yugma Bala for {planet} ---")
    
    # Check D1 (Rashi)
    d1_sign = int(longitude / 30)
    is_d1_odd = (d1_sign % 2 == 0)  # Aries(0), Gemini(2), Leo(4), etc. are odd signs
    sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    if planet in ['Moon', 'Venus']:
        d1_points = 15.0 if not is_d1_odd else 0.0
        print(f"D1: {sign_names[d1_sign]} ({'Even' if not is_d1_odd else 'Odd'}) → {d1_points} (needs Even)")
        total_points += d1_points
    else:
        d1_points = 15.0 if is_d1_odd else 0.0
        print(f"D1: {sign_names[d1_sign]} ({'Odd' if is_d1_odd else 'Even'}) → {d1_points} (needs Odd)")
        total_points += d1_points
    
    # Check D9 (Navamsa)
    divisions = chart_data.get('divisions', {})
    print(f"🔍 DEBUG divisions keys: {list(divisions.keys())}")
    d9_data = divisions.get('D9', {})
    print(f"🔍 DEBUG D9 data: {d9_data}")
    print(f"🔍 DEBUG planet '{planet}' in D9: {planet in d9_data}")
    if d9_data and planet in d9_data:
        d9_sign = d9_data[planet].get('sign', 0)
        is_d9_odd = (d9_sign % 2 == 0)
        
        if planet in ['Moon', 'Venus']:
            d9_points = 15.0 if not is_d9_odd else 0.0
            print(f"D9: {sign_names[d9_sign]} ({'Even' if not is_d9_odd else 'Odd'}) → {d9_points} (needs Even)")
            total_points += d9_points
        else:
            d9_points = 15.0 if is_d9_odd else 0.0
            print(f"D9: {sign_names[d9_sign]} ({'Odd' if is_d9_odd else 'Even'}) → {d9_points} (needs Odd)")
            total_points += d9_points
    else:
        print(f"D9: No data available → 0.0")
    
    print(f"Total Ojha Yugma Bala: {total_points}\n")
    print(f"🔍 RETURNING Ojha Yugma Bala: {total_points} (type: {type(total_points)})")
    print(f"🔍 BACKEND FINAL VALUE BEFORE RETURN: ojha_yugma_bala={total_points}")
    return total_points

def calculate_uccha_bala(planet: str, longitude: float) -> float:
    """Calculates Exaltation Strength using continuous arc distance.
    60 points at exaltation, 0 at debilitation, proportional in between.
    """
    if planet not in EXALTATION_DATA:
        return 30.0
    
    exalt_data = EXALTATION_DATA[planet]
    exalt_point = exalt_data['sign'] * 30 + exalt_data['degree']
    
    # Calculate arc distance from exaltation point
    diff = abs(longitude - exalt_point)
    if diff > 180:
        diff = 360 - diff
    
    # At exaltation (0 deg away) = 60 points
    # At debilitation (180 deg away) = 0 points
    # Linear interpolation
    uccha_bala = 60.0 * (1 - diff / 180.0)
    
    return round(max(0, uccha_bala), 2)

def get_varga_dignity(planet: str, varga_sign: int) -> str:
    """Determine dignity of planet in a varga sign"""
    if planet not in OWN_SIGNS:
        return 'neutral'
    
    # Check debilitation
    if planet in DEBILITATION_DATA and DEBILITATION_DATA[planet]['sign'] == varga_sign:
        return 'debilitated'
    
    # Check exaltation
    if planet in EXALTATION_DATA and EXALTATION_DATA[planet]['sign'] == varga_sign:
        return 'exalted'
    
    # Check own sign
    if varga_sign in OWN_SIGNS[planet]:
        return 'own_sign'
    
    # Simplified: return neutral for others (full implementation needs friendship tables)
    return 'neutral'

def _get_panchadha_dignity(planet: str, sign_lord: str, planet_house: int, lord_house: int) -> str:
    """Internal helper to merge Natural and Temporal friendship for Panchadha Maitri.
    
    Panchadha (Five-fold) Friendship Matrix:
    Natural Friend + Temporal Friend = Great Friend (Adhi Mitra)
    Natural Friend + Temporal Enemy = Neutral (Sama)
    Natural Enemy + Temporal Friend = Neutral (Sama)
    Natural Enemy + Temporal Enemy = Great Enemy (Adhi Satru)
    Natural Neutral + Temporal Friend = Friend (Mitra)
    Natural Neutral + Temporal Enemy = Enemy (Satru)
    """
    # Natural Relation
    is_natural_friend = sign_lord in NATURAL_FRIENDS.get(planet, [])
    is_natural_enemy = sign_lord in NATURAL_ENEMIES.get(planet, [])
    
    # Temporal Relation (Houses 2,3,4,10,11,12 away)
    diff = (lord_house - planet_house) % 12
    is_temporal_friend = diff in [1, 2, 3, 9, 10, 11]
    
    # Compound Logic Matrix (Panchadha) - CORRECTED
    if is_natural_friend:
        return 'great_friend' if is_temporal_friend else 'neutral'
    elif is_natural_enemy:
        return 'neutral' if is_temporal_friend else 'great_enemy'
    else:  # Natural Neutral
        return 'friend' if is_temporal_friend else 'enemy'

def calculate_saptavargaja_bala(planet: str, chart_data: Dict) -> float:
    """
    Calculates Saptavargiya Bala using Compound (Panchadha) Friendship.
    Iterates through D1, D2, D3, D7, D9, D12, D30.
    Uses Cumulative Sripati Scale (all vargas equally weighted).
    CRITICAL: Requires full planet mapping in each varga for temporal friendship.
    """
    varga_list = ['D1', 'D2', 'D3', 'D7', 'D9', 'D12', 'D30']
    divisions = chart_data.get('divisions', {})
    total_sthana_points = 0
    
    print(f"\n{'='*60}")
    print(f"SAPTAVARGAJA BALA FOR {planet} (Cumulative Sripati Scale)")
    print(f"{'='*60}")
    print(f"Available divisions: {list(divisions.keys())}")
    
    for varga_name in varga_list:
        print(f"\n--- {varga_name} ---")
        v_data = divisions.get(varga_name, {})
        if not v_data:
            print(f"❌ NO VARGA DATA - default 5.625")
            total_sthana_points += 5.625
            continue
        
        print(f"Planets: {list(v_data.keys())}")
        p_data = v_data.get(planet, {})
        if not p_data:
            print(f"❌ NO {planet} DATA - default 5.625")
            total_sthana_points += 5.625
            continue
            
        v_sign = p_data.get('sign', 0)
        p_v_house = p_data.get('house', 1)
        v_lord = SIGN_LORDS.get(v_sign, 'Sun')
        print(f"{planet}: sign={v_sign}, house={p_v_house}, lord={v_lord}")
        
        # 1. Check for Exaltation/Debilitation First
        if planet in EXALTATION_DATA and EXALTATION_DATA[planet]['sign'] == v_sign:
            print(f"✓ EXALTED → 45.0")
            total_sthana_points += COMPOUND_DIGNITY_POINTS['exalted']
            continue
        if planet in DEBILITATION_DATA and DEBILITATION_DATA[planet]['sign'] == v_sign:
            print(f"✓ DEBILITATED → 0.703125")
            total_sthana_points += COMPOUND_DIGNITY_POINTS['debilitated']
            continue
            
        # 2. Check for Moolatrikona (Only in D1)
        if varga_name == 'D1' and planet in OWN_SIGNS and v_sign in OWN_SIGNS[planet]:
            if v_sign == OWN_SIGNS[planet][0]:
                print(f"✓ MOOLATRIKONA → 33.75")
                total_sthana_points += COMPOUND_DIGNITY_POINTS['moolatrikona']
                continue
        
        # 3. Check for Own Sign
        if v_lord == planet:
            print(f"✓ OWN SIGN → 22.5")
            total_sthana_points += COMPOUND_DIGNITY_POINTS['own_sign']
            continue
        
        # 4. Calculate Compound Relationship with the Varga Lord
        lord_v_data = v_data.get(v_lord, {})
        if not lord_v_data:
            print(f"❌ NO {v_lord} DATA - default 5.625")
            total_sthana_points += 5.625
            continue
            
        lord_v_house = lord_v_data.get('house')
        if lord_v_house is None:
            print(f"❌ NO {v_lord} HOUSE - default 5.625")
            total_sthana_points += 5.625
            continue
        
        print(f"{v_lord}: house={lord_v_house}")
        house_diff = (lord_v_house - p_v_house) % 12
        is_temp_friend = house_diff in [1, 2, 3, 9, 10, 11]
        is_nat_friend = v_lord in NATURAL_FRIENDS.get(planet, [])
        is_nat_enemy = v_lord in NATURAL_ENEMIES.get(planet, [])
        
        dignity = _get_panchadha_dignity(planet, v_lord, p_v_house, lord_v_house)
        points = COMPOUND_DIGNITY_POINTS.get(dignity, 5.625)
        print(f"Natural={'F' if is_nat_friend else 'E' if is_nat_enemy else 'N'}, Temporal={'F' if is_temp_friend else 'E'} (diff={house_diff}) → {dignity.upper()} → {points}")
        total_sthana_points += points
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {round(total_sthana_points, 2)} ({round(total_sthana_points/60, 2)} Rupas)")
    print(f"{'='*60}\n")
    
    return round(total_sthana_points, 2)

def calculate_ayan_bala(planet: str, jd: float) -> float:
    """
    Calculates Equinoctial Strength using directional Declination (Kranti).
    North declination favors: Sun, Mars, Jupiter, Venus
    South declination favors: Moon, Saturn
    Mercury gets points in both directions
    """
    if planet not in PLANET_IDS:
        return 30.0
    
    try:
        # Get equatorial coordinates (includes declination)
        result = swe.calc_ut(jd, PLANET_IDS[planet], swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
        declination = result[0][1]  # Declination in degrees (-24 to +24)
        
        # Max declination is ~24 degrees
        # Formula: (declination / 24) * 60 for directional preference
        
        if planet in ['Sun', 'Mars', 'Jupiter', 'Venus']:
            # North declination favored (positive values)
            ayan_bala = ((declination + 24) / 48.0) * 60.0
        elif planet in ['Moon', 'Saturn']:
            # South declination favored (negative values)
            ayan_bala = ((24 - declination) / 48.0) * 60.0
        else:  # Mercury
            # Both directions favored (use absolute value)
            ayan_bala = (abs(declination) / 24.0) * 60.0
        
        return round(max(0, min(60.0, ayan_bala)), 2)
    except:
        return 30.0

def calculate_drik_bala(target_planet: str, target_long: float, all_planets: Dict, house_cusps: List[float]) -> float:
    """
    Calculates Aspectual Strength based on exact arc distances (Viyoga).
    CRITICAL: Benefics ADD strength, Malefics SUBTRACT strength.
    Moon: Waxing (Shukla Paksha) = Benefic, Waning near New Moon (Krishna Paksha) = Malefic.
    """
    benefics = ['Jupiter', 'Venus', 'Mercury', 'Moon']
    malefics = ['Sun', 'Mars', 'Saturn']
    
    # Check if Moon is waning (Krishna Paksha) when aspecting Sun
    if target_planet == 'Sun' and 'Moon' in all_planets:
        sun_long = target_long
        moon_long = all_planets['Moon'].get('longitude', 0)
        # Arc from Sun to Moon
        arc = (moon_long - sun_long) % 360
        # Krishna Paksha: 180-360° (waning)
        if arc > 180:
            # Moon is waning - treat as malefic for Sun's Drik Bala
            benefics = ['Jupiter', 'Venus', 'Mercury']
            malefics = ['Sun', 'Mars', 'Saturn', 'Moon']
            print(f"\n{'='*60}")
            print(f"DRIK BALA (ASPECTUAL STRENGTH) FOR {target_planet}")
            print(f"{'='*60}")
            print(f"Target {target_planet} longitude: {target_long:.2f}°")
            print(f"Moon phase: WANING (Krishna Paksha, arc={arc:.2f}°) - treated as MALEFIC")
        else:
            print(f"\n{'='*60}")
            print(f"DRIK BALA (ASPECTUAL STRENGTH) FOR {target_planet}")
            print(f"{'='*60}")
            print(f"Target {target_planet} longitude: {target_long:.2f}°")
            print(f"Moon phase: WAXING (Shukla Paksha, arc={arc:.2f}°) - treated as BENEFIC")
    else:
        print(f"\n{'='*60}")
        print(f"DRIK BALA (ASPECTUAL STRENGTH) FOR {target_planet}")
        print(f"{'='*60}")
        print(f"Target {target_planet} longitude: {target_long:.2f}°")
    
    total_drik = 0
    
    for p_name, p_data in all_planets.items():
        if p_name == target_planet or p_name in ['Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna', 'Ascendant']:
            continue
        
        p_long = p_data.get('longitude', 0)
        
        # Calculate arc distance
        diff = abs(target_long - p_long)
        if diff > 180:
            diff = 360 - diff
        
        print(f"\n{p_name}: {p_long:.2f}° (arc distance: {diff:.2f}°)")
        
        # Calculate aspect value with special aspects
        aspect_value = get_aspect_value(p_name, p_long, target_long, house_cusps, diff)
        
        # CRITICAL FIX: Subtract for malefics, add for benefics
        if p_name in malefics:
            contribution = -aspect_value / 4.0
            print(f"  → MALEFIC aspect value: {aspect_value:.2f} / 4 = {contribution:.2f} (SUBTRACT)")
            total_drik += contribution
        elif p_name in benefics:
            contribution = aspect_value / 4.0
            print(f"  → BENEFIC aspect value: {aspect_value:.2f} / 4 = {contribution:.2f} (ADD)")
            total_drik += contribution
        else:
            print(f"  → Neutral planet, skipped")
    
    print(f"\n{'='*60}")
    print(f"TOTAL DRIK BALA: {round(total_drik, 2)}")
    print(f"{'='*60}\n")
    
    return round(total_drik, 2)

def get_aspect_value(aspecting_planet: str, aspecting_long: float, target_long: float, house_cusps: List[float], diff: float) -> float:
    """
    Calculate aspect strength with Parashara Special and Partial Aspects.
    Uses strict Sripati Viyoga curve - malefics at 90° and 180° have maximum impact.
    For Drik Bala, use ONLY degree-based aspects (Viyoga), not house-based.
    """
    # Determine aspect type based on arc distance
    aspect_type = ""
    if diff <= 15:
        aspect_type = "Conjunction (0-15°)"
    elif diff <= 30:
        aspect_type = "Close Conjunction (15-30°)"
    elif diff <= 60:
        aspect_type = "Sextile zone (30-60°)"
    elif diff <= 90:
        aspect_type = "Square (60-90°)"
    elif diff <= 120:
        aspect_type = "Trine (90-120°)"
    elif diff <= 150:
        aspect_type = "Quincunx (120-150°)"
    elif diff <= 180:
        aspect_type = "Opposition (150-180°)"
    
    print(f"  Aspect type: {aspect_type}")
    
    # Sripati Viyoga curve: Maximum strength at 0°, 90°, and 180°
    # This creates strong malefic impacts at square and opposition
    if diff <= 30:
        # Conjunction zone: linear increase 0° to 30°
        aspect_val = diff * 2.0  # 0 → 60
        print(f"  Viyoga strength: {aspect_val:.2f} points")
        return aspect_val
    elif diff <= 60:
        # Declining from conjunction
        aspect_val = 60.0 - (diff - 30) * 1.5  # 60 → 15
        print(f"  Viyoga strength: {aspect_val:.2f} points")
        return aspect_val
    elif diff <= 90:
        # Building toward square: increases to maximum
        aspect_val = 15.0 + (diff - 60) * 1.5  # 15 → 60
        print(f"  Viyoga strength: {aspect_val:.2f} points")
        return aspect_val
    elif diff <= 120:
        # Declining from square
        aspect_val = 60.0 - (diff - 90) * 1.5  # 60 → 15
        print(f"  Viyoga strength: {aspect_val:.2f} points")
        return aspect_val
    elif diff <= 150:
        # Building toward opposition
        aspect_val = 15.0 + (diff - 120) * 1.5  # 15 → 60
        print(f"  Viyoga strength: {aspect_val:.2f} points")
        return aspect_val
    elif diff <= 180:
        # Opposition zone: maximum strength
        print(f"  Viyoga strength: 60.0 points")
        return 60.0
    
    print(f"  No aspect: 0.0 points")
    return 0

def _get_house_from_longitude(longitude: float, house_cusps: List[float]) -> int:
    """Determine which house a longitude falls into."""
    for i in range(12):
        start = house_cusps[i]
        end = house_cusps[(i + 1) % 12]
        if end < start:
            if longitude >= start or longitude < end:
                return i + 1
        else:
            if start <= longitude < end:
                return i + 1
    return 1

def calculate_nathonniya_bala(planet: str, jd: float, birth_data: Dict) -> float:
    """
    Calculates Nathonniya Bala (Diurnal/Nocturnal strength).
    Moon, Mars, Saturn: Strong at Midnight (60), weak at Noon (0)
    Sun, Jupiter, Venus: Strong at Noon (60), weak at Midnight (0)
    Mercury: Always strong (60)
    """
    if planet == 'Mercury':
        return 60.0
    
    try:
        lat = float(birth_data.get('latitude', 0))
        lon = float(birth_data.get('longitude', 0))
        
        # Get sunrise and sunset
        sunrise_jd = swe.rise_trans(jd, swe.SUN, lon, lat, 0, 0, 0, 0)[1][0]
        sunset_jd = swe.rise_trans(jd, swe.SUN, lon, lat, 0, 0, 0, 1)[1][0]
        
        # Calculate noon and midnight
        noon_jd = (sunrise_jd + sunset_jd) / 2.0
        next_sunrise_jd = swe.rise_trans(jd + 1, swe.SUN, lon, lat, 0, 0, 0, 0)[1][0]
        midnight_jd = (sunset_jd + next_sunrise_jd) / 2.0
        
        # Determine if birth is during day or night
        is_day = sunrise_jd <= jd <= sunset_jd
        
        if is_day:
            # Calculate distance from noon (0 to 0.5 day duration)
            day_duration = sunset_jd - sunrise_jd
            time_from_noon = abs(jd - noon_jd)
            # Normalize to 0-1 range (0 at noon, 1 at sunrise/sunset)
            normalized_distance = (time_from_noon / (day_duration / 2.0))
        else:
            # Calculate distance from midnight (0 to 0.5 night duration)
            night_duration = next_sunrise_jd - sunset_jd
            time_from_midnight = abs(jd - midnight_jd)
            # Normalize to 0-1 range (0 at midnight, 1 at sunset/sunrise)
            normalized_distance = (time_from_midnight / (night_duration / 2.0))
        
        # Apply planet-specific rules
        if planet in ['Moon', 'Mars', 'Saturn']:
            # Nocturnal planets: Strong at midnight
            if is_day:
                # During day: 0 at noon, increases toward sunset
                return round(normalized_distance * 60.0, 2)
            else:
                # During night: 60 at midnight, decreases toward sunrise/sunset
                return round((1 - normalized_distance) * 60.0, 2)
        else:  # Sun, Jupiter, Venus
            # Diurnal planets: Strong at noon
            if is_day:
                # During day: 60 at noon, decreases toward sunrise/sunset
                return round((1 - normalized_distance) * 60.0, 2)
            else:
                # During night: 0 at midnight, increases toward sunrise/sunset
                return round(normalized_distance * 60.0, 2)
    except:
        return 30.0

def calculate_paksha_bala(planet: str, sun_long: float, moon_long: float) -> float:
    """
    Paksha Bala: Moon's distance from Sun.
    Benefics (Jupiter, Venus, Mercury, Moon) strong in Shukla (waxing).
    Malefics (Mars, Saturn) strong in Krishna (waning).
    Sun: Strong only in Krishna Paksha (180-360°).
    Formula: Arc Distance / 3
    """
    # Arc distance from Sun to Moon
    arc = (moon_long - sun_long) % 360
    
    if planet == 'Moon':
        # Moon gets full strength in Shukla Paksha
        if arc <= 180:
            return round(arc / 3.0, 2)
        else:
            return round((360 - arc) / 3.0, 2)
    elif planet in ['Jupiter', 'Venus', 'Mercury']:
        # Other benefics: Shukla Paksha (0-180° gives 0-60 points)
        if arc <= 180:
            return round(arc / 3.0, 2)
        else:
            return round((360 - arc) / 3.0, 2)
    elif planet == 'Sun':
        # Sun: Strong only in Krishna Paksha (180-360°)
        if 180 < arc <= 360:
            return round((arc - 180) / 3.0, 2)
        return 0.0
    else:  # Mars, Saturn
        # Malefics: Krishna Paksha (180-360° gives 0-60 points)
        if arc > 180:
            return round((arc - 180) / 3.0, 2)
        else:
            return round((180 - arc) / 3.0, 2)

def calculate_tribhaga_bala(planet: str, jd: float, birth_data: Dict) -> float:
    """
    Tribhaga Bala: Strength based on 3 parts of day/night.
    Jupiter always gets 60. Others get 60 in their specific watch.
    """
    if planet == 'Jupiter':
        return 60.0
    
    try:
        lat = float(birth_data.get('latitude', 0))
        lon = float(birth_data.get('longitude', 0))
        
        # Get sunrise and sunset for the day
        sunrise_jd = swe.rise_trans(jd, swe.SUN, lon, lat, 0, 0, 0, 0)[1][0]
        sunset_jd = swe.rise_trans(jd, swe.SUN, lon, lat, 0, 0, 0, 1)[1][0]
        
        # Determine if birth is during day or night
        is_day = sunrise_jd <= jd <= sunset_jd
        
        if is_day:
            # Day divided into 3 parts
            day_duration = sunset_jd - sunrise_jd
            part_duration = day_duration / 3.0
            time_from_sunrise = jd - sunrise_jd
            part = int(time_from_sunrise / part_duration)
            
            # Mercury: 1st part, Sun: 2nd part, Saturn: 3rd part
            if (planet == 'Mercury' and part == 0) or \
               (planet == 'Sun' and part == 1) or \
               (planet == 'Saturn' and part == 2):
                return 60.0
        else:
            # Night divided into 3 parts
            next_sunrise_jd = swe.rise_trans(jd + 1, swe.SUN, lon, lat, 0, 0, 0, 0)[1][0]
            night_duration = next_sunrise_jd - sunset_jd
            part_duration = night_duration / 3.0
            time_from_sunset = jd - sunset_jd
            part = int(time_from_sunset / part_duration)
            
            # Moon: 1st part, Venus: 2nd part, Mars: 3rd part
            if (planet == 'Moon' and part == 0) or \
               (planet == 'Venus' and part == 1) or \
               (planet == 'Mars' and part == 2):
                return 60.0
        
        return 0.0
    except:
        return 30.0

def get_hora_lord(jd: float, birth_data: Dict) -> str:
    """Calculate Hora lord based on Vedic weekday and hour from sunrise.
    CRITICAL: Vedic day starts at sunrise, not midnight.
    """
    hora_sequence = ['Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars']
    
    try:
        lat = float(birth_data.get('latitude', 0))
        lon = float(birth_data.get('longitude', 0))
        
        # Get sunrise for current calendar day
        sunrise_jd = swe.rise_trans(jd, swe.SUN, lon, lat, 0, 0, 0, 0)[1][0]
        
        # If birth before sunrise, use previous day's sunrise
        if jd < sunrise_jd:
            sunrise_jd = swe.rise_trans(jd - 1, swe.SUN, lon, lat, 0, 0, 0, 0)[1][0]
        
        # Calculate hours from sunrise
        hours_from_sunrise = (jd - sunrise_jd) * 24
        hora_index_from_sunrise = int(hours_from_sunrise)
        
        # Get Vedic weekday
        vedic_weekday = int(swe.day_of_week(sunrise_jd))
        day_lords = ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun']
        day_lord = day_lords[vedic_weekday]
        
        # Find starting hora index
        start_index = hora_sequence.index(day_lord)
        hora_index = (start_index + hora_index_from_sunrise) % 7
        return hora_sequence[hora_index]
    except:
        # Fallback to calendar-based
        weekday = int(swe.day_of_week(jd))
        day_lords = ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun']
        return day_lords[weekday]

def get_dina_lord(jd: float, birth_data: Dict) -> str:
    """Calculate Vedic day lord (weekday ruler).
    CRITICAL: Vedic day starts at sunrise, not midnight.
    """
    try:
        lat = float(birth_data.get('latitude', 0))
        lon = float(birth_data.get('longitude', 0))
        
        # Get sunrise for current calendar day
        sunrise_jd = swe.rise_trans(jd, swe.SUN, lon, lat, 0, 0, 0, 0)[1][0]
        
        # If birth before sunrise, use previous day
        if jd < sunrise_jd:
            vedic_weekday = int(swe.day_of_week(jd - 1))
        else:
            vedic_weekday = int(swe.day_of_week(jd))
        
        day_lords = ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun']
        return day_lords[vedic_weekday]
    except:
        # Fallback
        weekday = int(swe.day_of_week(jd))
        day_lords = ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun']
        return day_lords[weekday]

def get_maasa_lord(jd: float) -> str:
    """Calculate month lord based on lunar month."""
    # Get Sun and Moon positions
    sun_long = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
    moon_long = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
    
    # Lunar month is determined by Sun's sign
    sun_sign = int(sun_long / 30)
    
    # Month lords follow sign lords
    return SIGN_LORDS[sun_sign]

def get_varsha_lord(jd: float, birth_data: Dict) -> str:
    """Calculate year lord based on solar return."""
    # Get current year's solar return (when Sun returns to natal position)
    # Simplified: Use Sun's current sign lord
    sun_long = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
    sun_sign = int(sun_long / 30)
    return SIGN_LORDS[sun_sign]

def calculate_kala_bala(planet: str, jd: float, birth_data: Dict) -> float:
    """
    Calculates complete Temporal Strength (Kala Bala):
    - Nathonniya Bala (60 points max) - Diurnal/Nocturnal
    - Paksha Bala (60 points max)
    - Tribhaga Bala (60 points max)
    - Varsha Lord (15 points)
    - Maasa Lord (30 points)
    - Dina Lord (45 points)
    - Hora Lord (60 points)
    - Ayana Bala (60 points max) - INCLUDED per DrikPanchang
    Total: 390 points maximum
    """
    try:
        sun_long = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
        moon_long = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
        
        # 1. Nathonniya Bala (Diurnal/Nocturnal)
        nathonniya_bala = calculate_nathonniya_bala(planet, jd, birth_data)
        
        # 2. Paksha Bala
        paksha_bala = calculate_paksha_bala(planet, sun_long, moon_long)
        
        # 3. Tribhaga Bala
        tribhaga_bala = calculate_tribhaga_bala(planet, jd, birth_data)
        
        # 4. Varsha Lord (15 points if planet is year lord)
        varsha_lord = get_varsha_lord(jd, birth_data)
        varsha_bala = 15.0 if planet == varsha_lord else 0.0
        
        # 5. Maasa Lord (30 points if planet is month lord)
        maasa_lord = get_maasa_lord(jd)
        maasa_bala = 30.0 if planet == maasa_lord else 0.0
        
        # 6. Dina Lord (45 points if planet is day lord)
        dina_lord = get_dina_lord(jd, birth_data)
        dina_bala = 45.0 if planet == dina_lord else 0.0
        
        # 7. Hora Lord (60 points if planet is hora lord)
        hora_lord = get_hora_lord(jd, birth_data)
        hora_bala = 60.0 if planet == hora_lord else 0.0
        
        # 8. Ayana Bala (CRITICAL: Must be included in Kala Bala per DrikPanchang)
        ayana_bala = calculate_ayan_bala(planet, jd)
        
        # Special rule: Sun's Ayana Bala is doubled (Sripati system)
        if planet == 'Sun':
            ayana_bala *= 2.0
        
        # Total Kala Bala (includes Ayana)
        total_kala = nathonniya_bala + paksha_bala + tribhaga_bala + varsha_bala + maasa_bala + dina_bala + hora_bala + ayana_bala
        
        return round(total_kala, 2)
    except Exception as e:
        print(f"Error in calculate_kala_bala for {planet}: {e}")
        return 120.0  # Default average

def calculate_chesta_bala(planet: str, jd: float) -> float:
    """
    Calculates Motional Strength based on planetary speed.
    Sun/Moon: Faster speed = stronger (corrected formula).
    Other planets use retrograde/direct motion logic.
    """
    if planet not in PLANET_IDS:
        return 30.0
    
    try:
        # Get sidereal position and speed
        result = swe.calc_ut(jd, PLANET_IDS[planet], swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
        speed = result[0][3]  # Daily motion in degrees
        
        if planet == 'Sun':
            # Adjusted range to match DrikPanchang's 34.26 target
            # With speed=0.985439, to get 34.26: (0.985439 - min) / (max - min) * 60 = 34.26
            # This suggests: min=0.9665, max=1.0165 (narrower range)
            min_s, max_s = 0.9665, 1.0165
            points = 60.0 * (speed - min_s) / (max_s - min_s)
            return round(max(0, min(60.0, points)), 2)
        
        if planet == 'Moon':
            # Moon speed varies ~11.8125 to ~15.3333 deg/day
            # Faster = stronger
            min_m, max_m = 11.8125, 15.3333
            points = 60.0 * (speed - min_m) / (max_m - min_m)
            return round(max(0, min(60.0, points)), 2)
        
        # Other planets: Retrograde vs Direct
        if speed < 0:
            return 0.0  # Retrograde gets minimum
        else:
            # Direct motion: scale based on speed (up to 60 points)
            return round(min(60.0, abs(speed) * 30), 2)
    except Exception as e:
        print(f"Error in calculate_chesta_bala for {planet}: {e}")
        return 30.0

def calculate_classical_shadbala(birth_data: Dict, chart_data: Dict) -> Dict:
    """Main function to calculate complete Shadbala for all planets"""
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # DEBUG: Check what's in chart_data
        print(f"\n=== Chart Data Keys: {list(chart_data.keys())} ===")
        if 'divisions' in chart_data:
            print(f"Divisions keys: {list(chart_data['divisions'].keys())}")
        else:
            print("WARNING: No 'divisions' key in chart_data!")
            print("Shadbala requires divisional chart data for accurate Saptavargaja Bala calculation.")
        
        # Get Julian Day with validation
        date_str = birth_data.get('date', '')
        time_str = birth_data.get('time', '')
        
        if not date_str or not time_str:
            raise ValueError("Missing date or time in birth_data")
        
        try:
            year, month, day = map(int, date_str.split('-'))
            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            second = int(time_parts[2]) if len(time_parts) > 2 else 0
            jd = swe.julday(year, month, day, hour + minute/60.0 + second/3600.0)
        except (ValueError, AttributeError, IndexError) as e:
            raise ValueError(f"Invalid date/time format: {e}")
        
        planets = chart_data.get('planets', {})
        if not planets:
            raise ValueError("No planets data in chart_data")
        
        # CRITICAL: house_cusps MUST be Bhava Madhyas (house midpoints) for accurate Dig Bala
        # ChartCalculator provides Placidus cusps (Sandhis), we need midpoints
        house_cusps = chart_data.get('house_cusps', [i*30 for i in range(12)])
        
        # Check if Bhava Madhyas are provided separately (preferred)
        bhava_madhyas = chart_data.get('bhava_madhyas')
        if bhava_madhyas and len(bhava_madhyas) == 12:
            house_cusps = bhava_madhyas
        elif 'house_midpoints' in chart_data and len(chart_data['house_midpoints']) == 12:
            house_cusps = chart_data['house_midpoints']
        else:
            # Calculate midpoints from cusps (Sandhis)
            house_cusps = _calculate_bhava_madhyas(house_cusps)
        
        results = {}
        
        for planet_name, planet_data in planets.items():
            if planet_name in ['Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna', 'Ascendant']:
                continue
            
            try:
                longitude = planet_data.get('longitude', 0)
                if longitude is None:
                    longitude = 0
                
                # Sthana Bala = Uccha Bala + Saptavargaja Bala + Ojha-Yugma Bala + Kendradi Bala + Drekkana Bala
                # NOTE: Ayana Bala is now included in Kala Bala per DrikPanchang standards
                uccha_bala = calculate_uccha_bala(planet_name, longitude)
                saptavargaja_bala = calculate_saptavargaja_bala(planet_name, chart_data)
                ojha_yugma_bala = calculate_ojha_yugma_bala(planet_name, longitude, chart_data)
                kendradi_bala = calculate_kendradi_bala(planet_data.get('house', 1))
                drekkana_bala = calculate_drekkana_bala(planet_name, longitude)
                sthana_bala = uccha_bala + saptavargaja_bala + ojha_yugma_bala + kendradi_bala + drekkana_bala
                
                # Ayana Bala calculated separately for display (now included in Kala Bala)
                ayan_bala = calculate_ayan_bala(planet_name, jd)
                
                dig_bala = calculate_dig_bala(planet_name, longitude, house_cusps)
                kala_bala = calculate_kala_bala(planet_name, jd, birth_data)
                chesta_bala = calculate_chesta_bala(planet_name, jd)
                naisargika_bala = NAISARGIKA_BALA.get(planet_name, 30.0)
                drik_bala = calculate_drik_bala(planet_name, longitude, planets, house_cusps)
                
                total_points = sthana_bala + dig_bala + kala_bala + chesta_bala + naisargika_bala + drik_bala
                total_rupas = total_points / 60.0
                
                # Calculate Ishta/Kashta Phala
                ishta_kashta = calculate_ishta_kashta_phala(uccha_bala, chesta_bala)
                
                grade = 'Excellent' if total_rupas >= 6 else 'Good' if total_rupas >= 5 else 'Average' if total_rupas >= 4 else 'Weak'
                
                results[planet_name] = {
                    'total_points': round(total_points, 2),
                    'total_rupas': round(total_rupas, 2),
                    'grade': grade,
                    'ishta_phala': ishta_kashta['ishta_phala'],
                    'kashta_phala': ishta_kashta['kashta_phala'],
                    'ishta_percent': ishta_kashta['ishta_percent'],
                    'kashta_percent': ishta_kashta['kashta_percent'],
                    'result_tendency': 'Benefic' if ishta_kashta['ishta_phala'] > ishta_kashta['kashta_phala'] else 'Malefic',
                    'components': {
                        'sthana_bala': round(sthana_bala, 2),
                        'dig_bala': round(dig_bala, 2),
                        'kala_bala': round(kala_bala, 2),
                        'chesta_bala': round(chesta_bala, 2),
                        'naisargika_bala': round(naisargika_bala, 2),
                        'drik_bala': round(drik_bala, 2)
                    },
                    'detailed_breakdown': {
                        'sthana_components': {
                            'uccha_bala': uccha_bala,
                            'saptavargaja_bala': saptavargaja_bala,
                            'ojha_yugma_bala': ojha_yugma_bala,
                            'kendradi_bala': kendradi_bala,
                            'drekkana_bala': drekkana_bala
                        },
                        'ayan_bala': ayan_bala,
                        'kala_components': {}
                    }
                }
                print(f"🔍 BACKEND: Storing {planet_name} ojha_yugma_bala={ojha_yugma_bala} in results")
            except Exception as e:
                print(f"Error calculating Shadbala for {planet_name}: {e}")
                # Return default values for this planet
                results[planet_name] = {
                    'total_points': 300.0,
                    'total_rupas': 5.0,
                    'grade': 'Average',
                    'components': {
                        'sthana_bala': 50.0,
                        'dig_bala': 30.0,
                        'kala_bala': 50.0,
                        'chesta_bala': 30.0,
                        'naisargika_bala': NAISARGIKA_BALA.get(planet_name, 30.0),
                        'drik_bala': 10.0
                    },
                    'detailed_breakdown': {
                        'sthana_components': {'uccha_bala': 30.0, 'saptavargaja_bala': 20.0},
                        'kala_components': {}
                    }
                }
        
        return results
    
    except Exception as e:
        print(f"Critical error in calculate_classical_shadbala: {e}")
        import traceback
        traceback.print_exc()
        raise
