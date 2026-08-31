"""
Corrected Classical Shadbala Calculator
Based on DrikPanchang standards and rigorous BPHS method
Uses continuous mathematical differentials instead of static if/else logic
"""

import logging
import swisseph as swe
import math
from typing import Dict, Any, List
from datetime import datetime

from utils.timezone_service import parse_timezone_offset

_logger = logging.getLogger(__name__)

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

# Classical Saptavargaja virupas.  Exaltation/debilitation belong to Uccha
# Bala and must not be counted a second time here.
COMPOUND_DIGNITY_POINTS = {
    'moolatrikona': 45.0,
    'own_sign': 30.0,
    'great_friend': 22.5,
    'friend': 15.0,
    'neutral': 7.5,
    'enemy': 3.75,
    'great_enemy': 1.875,
}

def _interpolate_arc(start: float, end: float, fraction: float) -> float:
    return (start + ((end - start) % 360.0) * fraction) % 360.0


def _sripati_bhava_madhyas(jd: float, latitude: float, longitude: float) -> List[float]:
    """Return the twelve Sripati bhava madhyas from Ascendant and MC.

    Sripati trisects each quadrant.  Swiss Ephemeris supplies the two angular
    anchors; interpolating *madhyas* is different from averaging house starts.
    """
    _cusps, angles = swe.houses_ex(jd, latitude, longitude, b'P', swe.FLG_SIDEREAL)
    ascendant, midheaven = angles[0] % 360.0, angles[1] % 360.0
    anchors = {0: ascendant, 3: (midheaven + 180.0) % 360.0,
               6: (ascendant + 180.0) % 360.0, 9: midheaven}
    result = [0.0] * 12
    for start_house, end_house in ((9, 0), (0, 3), (3, 6), (6, 9)):
        start, end = anchors[start_house], anchors[end_house]
        result[start_house] = start
        for step in (1, 2):
            result[(start_house + step) % 12] = _interpolate_arc(start, end, step / 3.0)
    return result


def _birth_julian_days(birth_data: Dict[str, Any]):
    """Return (UT JD, local civil JD, timezone offset) without losing seconds."""
    date_text = str(birth_data.get('date') or '').split('T', 1)[0]
    time_text = str(birth_data.get('time') or '')
    if not date_text or not time_text:
        raise ValueError('Missing date or time in birth_data')
    year, month, day = (int(value) for value in date_text.split('-'))
    parts = time_text.split(':')
    local_hour = int(parts[0]) + (int(parts[1]) if len(parts) > 1 else 0) / 60.0
    local_hour += (float(parts[2]) if len(parts) > 2 else 0.0) / 3600.0
    latitude = float(birth_data.get('latitude'))
    longitude = float(birth_data.get('longitude'))
    offset = parse_timezone_offset(
        birth_data.get('timezone', ''), latitude, longitude, for_date=date_text
    )
    return (
        swe.julday(year, month, day, local_hour - offset),
        swe.julday(year, month, day, local_hour),
        float(offset),
    )

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

# BPHS minimum Shadbala required for a planet to be considered capable of
# delivering its promised results.  Parashara's Light prints these in
# virupas; the corresponding rupas are the values divided by 60.
SHADBALA_MINIMUM_VIRUPAS = {
    'Sun': 390.0,
    'Moon': 360.0,
    'Mars': 300.0,
    'Mercury': 420.0,
    'Jupiter': 390.0,
    'Venus': 330.0,
    'Saturn': 300.0,
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
    
    # Classical geometric mean in virupas.  Dividing this by two (as the old
    # implementation did) has no textual basis and halves the published phala.
    ishta_phala = math.sqrt(product) if product > 0 else 0.0
    
    kashta_phala = math.sqrt(
        max(0.0, 60.0 - uccha_bala) * max(0.0, 60.0 - chesta_bala)
    )
    
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
    
    # Check D1 (Rashi)
    d1_sign = int(longitude / 30)
    is_d1_odd = (d1_sign % 2 == 0)  # Aries(0), Gemini(2), Leo(4), etc. are odd signs
    sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    if planet in ['Moon', 'Venus']:
        d1_points = 15.0 if not is_d1_odd else 0.0
        total_points += d1_points
    else:
        d1_points = 15.0 if is_d1_odd else 0.0
        total_points += d1_points
    
    # Check D9 (Navamsa)
    divisions = chart_data.get('divisions', {})
    d9_data = divisions.get('D9', {})
    if d9_data and planet in d9_data:
        d9_sign = d9_data[planet].get('sign', 0)
        is_d9_odd = (d9_sign % 2 == 0)

        if planet in ['Moon', 'Venus']:
            d9_points = 15.0 if not is_d9_odd else 0.0
            total_points += d9_points
        else:
            d9_points = 15.0 if is_d9_odd else 0.0
            total_points += d9_points
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
    Panchadha friendship is established once from D1.  Recomputing temporal
    friendship separately inside each varga is a common implementation error.
    """
    varga_list = ['D1', 'D2', 'D3', 'D7', 'D9', 'D12', 'D30']
    divisions = chart_data.get('divisions', {})
    missing = [name for name in varga_list if not divisions.get(name)]
    if missing:
        raise ValueError(f"Saptavargaja requires {', '.join(missing)}")

    d1 = divisions['D1']
    if planet not in d1:
        raise ValueError(f"D1 is missing {planet}")
    d1_planet_sign = int(d1[planet]['sign'])
    compound_relations = {}
    for lord in set(SIGN_LORDS.values()):
        if lord not in d1:
            raise ValueError(f"D1 is missing sign lord {lord}")
        lord_sign = int(d1[lord]['sign'])
        compound_relations[lord] = _get_panchadha_dignity(
            planet, lord, d1_planet_sign + 1, lord_sign + 1
        )

    moolatrikona_signs = {
        'Sun': 4, 'Moon': 1, 'Mars': 0, 'Mercury': 5,
        'Jupiter': 8, 'Venus': 6, 'Saturn': 10,
    }
    total_sthana_points = 0.0
    
    for varga_name in varga_list:
        v_data = divisions.get(varga_name, {})
        p_data = v_data.get(planet, {})
        if not p_data:
            raise ValueError(f"{varga_name} is missing {planet}")
            
        v_sign = p_data.get('sign', 0)
        v_lord = SIGN_LORDS.get(v_sign, 'Sun')

        if varga_name == 'D1' and v_sign == moolatrikona_signs[planet]:
            total_sthana_points += COMPOUND_DIGNITY_POINTS['moolatrikona']
            continue
        if v_lord == planet:
            total_sthana_points += COMPOUND_DIGNITY_POINTS['own_sign']
            continue
        total_sthana_points += COMPOUND_DIGNITY_POINTS[compound_relations[v_lord]]
    
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
    
    # Classical kranti is derived from sayana longitude on the 24-degree
    # obliquity circle, rather than using the body's observed celestial
    # latitude as a modern declination shortcut.
    tropical_longitude = swe.calc_ut(jd, PLANET_IDS[planet], swe.FLG_SWIEPH)[0][0]
    kranti = math.degrees(math.asin(
        math.sin(math.radians(tropical_longitude)) * math.sin(math.radians(24.0))
    ))
    if planet in ('Moon', 'Saturn'):
        value = (24.0 - kranti) * 1.25
    elif planet == 'Mercury':
        value = (24.0 + abs(kranti)) * 1.25
    else:
        value = (24.0 + kranti) * 1.25
    return round(max(0.0, min(60.0, value)), 2)

def _functional_benefics_and_malefics(all_planets: Dict):
    sun = float(all_planets['Sun']['longitude'])
    moon = float(all_planets['Moon']['longitude'])
    moon_arc = (moon - sun) % 360.0
    benefics = {'Jupiter', 'Venus'}
    malefics = {'Sun', 'Mars', 'Saturn'}
    (benefics if moon_arc <= 180.0 else malefics).add('Moon')

    mercury_sign = int(float(all_planets['Mercury']['longitude']) / 30.0)
    joined_malefics = sum(
        int(float(all_planets[name]['longitude']) / 30.0) == mercury_sign
        for name in ('Sun', 'Mars', 'Saturn')
    )
    joined_benefics = sum(
        int(float(all_planets[name]['longitude']) / 30.0) == mercury_sign
        for name in ('Moon', 'Jupiter', 'Venus')
    )
    (malefics if joined_malefics > joined_benefics else benefics).add('Mercury')
    return benefics, malefics


def calculate_drik_bala(target_planet: str, target_long: float, all_planets: Dict, house_cusps: List[float] = None) -> float:
    """
    Calculates Aspectual Strength based on exact arc distances (Viyoga).
    CRITICAL: Benefics ADD strength, Malefics SUBTRACT strength.
    Moon: Waxing (Shukla Paksha) = Benefic, Waning near New Moon (Krishna Paksha) = Malefic.
    """
    benefics, malefics = _functional_benefics_and_malefics(all_planets)
    total_drik = 0.0
    
    for p_name, p_data in all_planets.items():
        if p_name == target_planet or p_name in ['Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna', 'Ascendant']:
            continue
        
        p_long = p_data.get('longitude', 0)
        
        aspect_value = get_aspect_value(p_name, p_long, target_long)
        
        # Mercury and Jupiter retain their whole sphuta aspect; the remaining
        # grahas contribute one quarter.  Sign follows the graha's functional
        # benefic/malefic nature for this nativity.
        factor = 1.0 if p_name in ('Mercury', 'Jupiter') else 0.25
        if p_name in malefics:
            total_drik -= aspect_value * factor
        elif p_name in benefics:
            total_drik += aspect_value * factor
    
    return round(total_drik, 2)

def get_aspect_value(aspecting_planet: str, aspecting_long: float, target_long: float, house_cusps=None, diff=None) -> float:
    """
    Calculate aspect strength with Parashara Special and Partial Aspects.
    Uses strict Sripati Viyoga curve - malefics at 90° and 180° have maximum impact.
    For Drik Bala, use ONLY degree-based aspects (Viyoga), not house-based.
    """
    # Directed sphuta drishti: the arc is from the aspecting graha to the
    # aspected graha.  Folding it to 0..180 destroys the 8th/9th/10th aspects.
    arc = (target_long - aspecting_long) % 360.0
    if arc < 30.0:
        value = 0.0
    elif arc < 60.0:
        value = 0.5 * (arc - 30.0)
    elif arc < 90.0:
        value = arc - 45.0
    elif arc < 120.0:
        value = 0.5 * (120.0 - arc) + 30.0
    elif arc < 150.0:
        value = 150.0 - arc
    elif arc < 180.0:
        value = 2.0 * (arc - 150.0)
    elif arc < 300.0:
        value = 0.5 * (300.0 - arc)
    else:
        value = 0.0

    # Special aspects replace the generic curve on their specified arcs.
    if aspecting_planet == 'Mars':
        if 60.0 <= arc < 90.0:
            value = 15.0 + 1.5 * (arc - 60.0)
        elif 90.0 <= arc < 120.0:
            value = 60.0 - (arc - 90.0)
        elif 180.0 <= arc < 210.0:
            value = 60.0
        elif 210.0 <= arc < 240.0:
            value = 60.0 - (arc - 210.0)
    elif aspecting_planet == 'Jupiter':
        if 90.0 <= arc < 120.0:
            value = 45.0 + 0.5 * (arc - 90.0)
        elif 120.0 <= arc < 150.0:
            value = 60.0 - (arc - 120.0)
        elif 210.0 <= arc < 240.0:
            value = 45.0 + 0.5 * (arc - 210.0)
        elif 240.0 <= arc < 270.0:
            value = 60.0 - (arc - 240.0)
    elif aspecting_planet == 'Saturn':
        if 30.0 <= arc < 60.0:
            value = 2.0 * (arc - 30.0)
        elif 60.0 <= arc < 90.0:
            value = 45.0 + 0.5 * (90.0 - arc)
        elif 240.0 <= arc < 270.0:
            value = arc - 210.0
        elif 270.0 <= arc < 300.0:
            value = 2.0 * (300.0 - arc)
    return max(0.0, min(60.0, value))

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
    
    _ut_jd, local_jd, offset = _birth_julian_days(birth_data)
    local_hour = ((local_jd + 0.5) % 1.0) * 24.0
    # Convert standard civil time to local mean time at the birthplace.
    local_mean_hour = (local_hour + float(birth_data['longitude']) / 15.0 - offset) % 24.0
    day_strength = (60.0 - abs(local_mean_hour - 12.0) * 5.0) % 60.0
    if planet in ('Moon', 'Mars', 'Saturn'):
        day_strength = 60.0 - day_strength
    return round(day_strength, 2)

def calculate_paksha_bala(planet: str, sun_long: float, moon_long: float, all_planets: Dict = None) -> float:
    """
    Paksha Bala: Moon's distance from Sun.
    Benefics (Jupiter, Venus, Mercury, Moon) strong in Shukla (waxing).
    Malefics (Mars, Saturn) strong in Krishna (waning).
    Sun: Strong only in Krishna Paksha (180-360°).
    Formula: Arc Distance / 3
    """
    # Arc distance from Sun to Moon
    arc = (moon_long - sun_long) % 360
    
    base = min(arc, 360.0 - arc) / 3.0
    if planet == 'Moon':
        return round(base, 2)
    if all_planets:
        benefics, _malefics = _functional_benefics_and_malefics(all_planets)
    else:
        benefics = {'Mercury', 'Jupiter', 'Venus'}
    return round(base if planet in benefics else 60.0 - base, 2)


def _local_midnight_ut(jd: float, birth_data: Dict) -> float:
    _ut, local_jd, offset = _birth_julian_days(birth_data)
    return math.floor(local_jd - 0.5) + 0.5 - offset / 24.0


def _solar_event(start_jd: float, birth_data: Dict, event: int) -> float:
    geopos = (float(birth_data['longitude']), float(birth_data['latitude']), 0.0)
    result, times = swe.rise_trans(
        start_jd, swe.SUN, event | swe.BIT_DISC_CENTER, geopos, 0.0, 0.0,
        swe.FLG_SWIEPH,
    )
    if result != 0:
        raise ValueError('No solar rise/set event at the supplied location and date')
    return times[0]


def _sunrise_sunset_for_birth(jd: float, birth_data: Dict):
    midnight = _local_midnight_ut(jd, birth_data)
    sunrise = _solar_event(midnight, birth_data, swe.CALC_RISE)
    sunset = _solar_event(midnight, birth_data, swe.CALC_SET)
    return sunrise, sunset

def calculate_tribhaga_bala(planet: str, jd: float, birth_data: Dict) -> float:
    """
    Tribhaga Bala: Strength based on 3 parts of day/night.
    Jupiter always gets 60. Others get 60 in their specific watch.
    """
    if planet == 'Jupiter':
        return 60.0
    
    sunrise, sunset = _sunrise_sunset_for_birth(jd, birth_data)
    if sunrise <= jd < sunset:
        part = min(2, int((jd - sunrise) / ((sunset - sunrise) / 3.0)))
        rulers = ('Mercury', 'Sun', 'Saturn')
    else:
        if jd < sunrise:
            previous_sunset = _solar_event(_local_midnight_ut(jd, birth_data) - 1.0, birth_data, swe.CALC_SET)
            next_sunrise, night_start = sunrise, previous_sunset
        else:
            next_sunrise = _solar_event(_local_midnight_ut(jd, birth_data) + 1.0, birth_data, swe.CALC_RISE)
            night_start = sunset
        part = min(2, int((jd - night_start) / ((next_sunrise - night_start) / 3.0)))
        rulers = ('Moon', 'Venus', 'Mars')
    return 60.0 if planet == rulers[part] else 0.0

def get_hora_lord(jd: float, birth_data: Dict) -> str:
    """Calculate Hora lord based on Vedic weekday and hour from sunrise.
    CRITICAL: Vedic day starts at sunrise, not midnight.
    """
    hora_sequence = ['Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars']
    
    sunrise, _sunset = _sunrise_sunset_for_birth(jd, birth_data)
    if jd < sunrise:
        sunrise = _solar_event(_local_midnight_ut(jd, birth_data) - 1.0, birth_data, swe.CALC_RISE)
    day_lord = _weekday_lord(sunrise)
    elapsed_horas = int((jd - sunrise) * 24.0)
    return hora_sequence[(hora_sequence.index(day_lord) + elapsed_horas) % 7]


def _weekday_lord(jd: float) -> str:
    # Swiss Ephemeris is Monday=0.
    return ('Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun')[swe.day_of_week(jd)]

def get_dina_lord(jd: float, birth_data: Dict) -> str:
    """Calculate Vedic day lord (weekday ruler).
    CRITICAL: Vedic day starts at sunrise, not midnight. Use the weekday of the
    sunrise that began the current Vedic day.
    BPHS: Sunday=Sun, Monday=Moon, Tuesday=Mars, Wednesday=Mercury, Thursday=Jupiter, Friday=Venus, Saturday=Saturn.
    """
    sunrise, _sunset = _sunrise_sunset_for_birth(jd, birth_data)
    if jd < sunrise:
        sunrise = _solar_event(_local_midnight_ut(jd, birth_data) - 1.0, birth_data, swe.CALC_RISE)
    return _weekday_lord(sunrise)

def _days_elapsed_since_base(year: int, base_year: int = 1951, base_days: int = 174) -> int:
    step = 1 if year >= base_year else -1
    days = base_days
    for value in range(base_year, year, step):
        checked = value + (1 if step > 0 else 0)
        leap = checked % 4 == 0 and (checked % 100 != 0 or checked % 400 == 0)
        days += step * (366 if leap else 365)
    return days


def _ahargana(birth_data: Dict, base_year: int = 1951, base_days: int = 174) -> int:
    date_text = str(birth_data['date']).split('T', 1)[0]
    dt = datetime.strptime(date_text, '%Y-%m-%d')
    return _days_elapsed_since_base(dt.year - 1, base_year, base_days) + dt.timetuple().tm_yday


_ABDA_WEEKDAYS = ('Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun', 'Moon')


def get_maasa_lord(jd: float, birth_data: Dict = None) -> str:
    if birth_data is None:
        raise ValueError('birth_data is required for Maasa Bala')
    return _ABDA_WEEKDAYS[(int(_ahargana(birth_data) // 30) * 2 + 1) % 7]

def get_varsha_lord(jd: float, birth_data: Dict) -> str:
    return _ABDA_WEEKDAYS[(int(_ahargana(birth_data) // 360) * 3 + 1) % 7]

def calculate_kala_bala(planet: str, jd: float, birth_data: Dict, all_planets: Dict):
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
    Returns: (total_kala, kala_components_dict) for API breakdown display.
    """
    sun_long = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
    moon_long = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
    nathonniya_bala = calculate_nathonniya_bala(planet, jd, birth_data)
    paksha_bala = calculate_paksha_bala(planet, sun_long, moon_long, all_planets)
    tribhaga_bala = calculate_tribhaga_bala(planet, jd, birth_data)
    varsha_bala = 15.0 if planet == get_varsha_lord(jd, birth_data) else 0.0
    maasa_bala = 30.0 if planet == get_maasa_lord(jd, birth_data) else 0.0
    dina_bala = 45.0 if planet == get_dina_lord(jd, birth_data) else 0.0
    hora_bala = 60.0 if planet == get_hora_lord(jd, birth_data) else 0.0
    ayana_bala = calculate_ayan_bala(planet, jd)
    # Graha-yuddha applies only when two non-luminaries are within one degree.
    # The war correction needs the competing pre-war totals and is therefore
    # attached in a second pass by the main calculator.
    yuddha_bala = 0.0
    total_kala = nathonniya_bala + paksha_bala + tribhaga_bala + varsha_bala + maasa_bala + dina_bala + hora_bala + ayana_bala + yuddha_bala

    kala_components = {
        'nathonniya_bala': round(nathonniya_bala, 2),
        'paksha_bala': round(paksha_bala, 2),
        'tribhaga_bala': round(tribhaga_bala, 2),
        'varsha_bala': round(varsha_bala, 2),
        'maasa_bala': round(maasa_bala, 2),
        'dina_bala': round(dina_bala, 2),
        'hora_bala': round(hora_bala, 2),
        'ayana_bala': round(ayana_bala, 2),
        'yuddha_bala': round(yuddha_bala, 2),
    }
    return round(total_kala, 2), kala_components

_CHESTA_EPOCH_JD = swe.julday(1900, 1, 1, 0.0)
_CHESTA_MEAN_AT_EPOCH = {
    'Sun': 257.4568, 'Mars': 270.22, 'Mercury': 164.0,
    'Jupiter': 220.04, 'Venus': 328.51, 'Saturn': 236.74,
}
_CHESTA_MEAN_MOTION = {
    # Precision retained by the Kedarnath Dutt digit tables; using their
    # one-day display values as multipliers accumulates degrees of drift.
    'Sun': 0.98560265, 'Mars': 0.524019, 'Mercury': 4.092318,
    'Jupiter': 0.08311096, 'Venus': 1.602146, 'Saturn': 0.033439,
}
_CHESTA_YEAR_CORRECTION = {
    'Sun': (1.0, 0.0, 0.0), 'Mars': (1.0, 0.0, 0.0),
    'Mercury': (1.0, 6.67, -0.00133),
    'Jupiter': (-1.0, 3.3, 0.0067),
    'Venus': (-1.0, 5.0, 0.0001),
    'Saturn': (1.0, 5.0, 0.001),
}


def _classical_mean_longitude(planet: str, jd: float, longitude: float) -> float:
    days = jd - _CHESTA_EPOCH_JD + (76.0 - longitude) / 360.0
    year = swe.revjul(jd)[0]
    sign, constant, annual = _CHESTA_YEAR_CORRECTION[planet]
    correction = sign * (constant + annual * (year - 1900))
    return (
        _CHESTA_MEAN_AT_EPOCH[planet]
        + days * _CHESTA_MEAN_MOTION[planet]
        + correction
    ) % 360.0


def _circular_midpoint(first: float, second: float) -> float:
    return (first + ((second - first + 180.0) % 360.0 - 180.0) / 2.0) % 360.0


def calculate_chesta_bala(
    planet: str, jd: float, *, ayan_bala: float = None,
    paksha_bala: float = None, longitude: float = 76.0,
) -> float:
    """
    Calculates Motional Strength based on planetary speed.
    Sun/Moon: Faster speed = stronger (corrected formula).
    Other planets use retrograde/direct motion logic.
    """
    if planet not in PLANET_IDS:
        return 30.0
    
    if planet == 'Sun':
        if ayan_bala is None:
            raise ValueError('Sun Chesta Bala requires Ayana Bala')
        return round(ayan_bala, 2)
    if planet == 'Moon':
        if paksha_bala is None:
            raise ValueError('Moon Chesta Bala requires Paksha Bala')
        return round(paksha_bala, 2)

    true_longitude = swe.calc_ut(
        jd, PLANET_IDS[planet], swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    )[0][0]
    sun_mean = _classical_mean_longitude('Sun', jd, longitude)
    planet_mean = _classical_mean_longitude(planet, jd, longitude)
    if planet in ('Mercury', 'Venus'):
        seeghrocha, mean_for_midpoint = planet_mean, sun_mean
    else:
        seeghrocha, mean_for_midpoint = sun_mean, planet_mean
    mean_true_midpoint = _circular_midpoint(true_longitude, mean_for_midpoint)
    kendra = abs((seeghrocha - mean_true_midpoint + 180.0) % 360.0 - 180.0)
    return round(kendra / 3.0, 2)

def calculate_classical_shadbala(birth_data, chart_data: Dict) -> Dict:
    """Main function to calculate complete Shadbala for all planets"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    birth_dict = vars(birth_data) if hasattr(birth_data, '__dict__') else birth_data
    if not chart_data.get('divisions'):
        raise ValueError('Shadbala requires D1, D2, D3, D7, D9, D12 and D30')

    jd, _local_jd, _offset = _birth_julian_days(birth_dict)
    planets = chart_data.get('planets', {})
    if not planets:
        raise ValueError('No planets data in chart_data')
    bhava_madhyas = _sripati_bhava_madhyas(
        jd, float(birth_dict['latitude']), float(birth_dict['longitude'])
    )
    results = {}
    excluded = {'Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna', 'Ascendant'}
    for planet_name, planet_data in planets.items():
        if planet_name in excluded:
            continue
        longitude = planet_data.get('longitude')
        if longitude is None:
            raise ValueError(f'Missing longitude for {planet_name}')

        uccha_bala = calculate_uccha_bala(planet_name, longitude)
        saptavargaja_bala = calculate_saptavargaja_bala(planet_name, chart_data)
        ojha_yugma_bala = calculate_ojha_yugma_bala(planet_name, longitude, chart_data)
        kendradi_bala = calculate_kendradi_bala(planet_data.get('house', 1))
        drekkana_bala = calculate_drekkana_bala(planet_name, longitude)
        sthana_bala = sum((uccha_bala, saptavargaja_bala, ojha_yugma_bala,
                          kendradi_bala, drekkana_bala))
        ayan_bala = calculate_ayan_bala(planet_name, jd)
        dig_bala = calculate_dig_bala(planet_name, longitude, bhava_madhyas)
        kala_bala, kala_components = calculate_kala_bala(
            planet_name, jd, birth_dict, planets
        )
        chesta_bala = calculate_chesta_bala(
            planet_name, jd, ayan_bala=ayan_bala,
            paksha_bala=kala_components['paksha_bala'],
            longitude=float(birth_dict['longitude']),
        )
        naisargika_bala = NAISARGIKA_BALA[planet_name]
        drik_bala = calculate_drik_bala(planet_name, longitude, planets)
        total_points = sum((sthana_bala, dig_bala, kala_bala, chesta_bala,
                            naisargika_bala, drik_bala))
        total_rupas = total_points / 60.0
        ishta_kashta = calculate_ishta_kashta_phala(uccha_bala, chesta_bala)
        minimum_points = SHADBALA_MINIMUM_VIRUPAS[planet_name]
        required_ratio = total_points / minimum_points
        # Keep the legacy grade for downstream report compatibility.  The UI
        # uses classical_status, which is correctly based on this planet's
        # own minimum rather than a universal Rupa threshold.
        grade = ('Excellent' if total_rupas >= 6 else 'Good' if total_rupas >= 5
                 else 'Average' if total_rupas >= 4 else 'Weak')
        classical_status = ('Meets requirement' if required_ratio >= 1.0
                            else 'Below requirement')
        results[planet_name] = {
            'total_points': round(total_points, 2),
            'total_rupas': round(total_rupas, 2),
            'grade': grade,
            'classical_status': classical_status,
            'minimum_required_points': minimum_points,
            'minimum_required_rupas': round(minimum_points / 60.0, 2),
            'required_ratio': round(required_ratio, 2),
            'required_percent': round(required_ratio * 100.0, 1),
            'meets_minimum': required_ratio >= 1.0,
            **ishta_kashta,
            'result_tendency': ('Benefic' if ishta_kashta['ishta_phala']
                                > ishta_kashta['kashta_phala'] else 'Malefic'),
            'components': {
                'sthana_bala': round(sthana_bala, 2), 'dig_bala': round(dig_bala, 2),
                'kala_bala': round(kala_bala, 2), 'chesta_bala': round(chesta_bala, 2),
                'naisargika_bala': round(naisargika_bala, 2),
                'drik_bala': round(drik_bala, 2),
            },
            'detailed_breakdown': {
                'sthana_components': {
                    'uccha_bala': uccha_bala,
                    'saptavargaja_bala': saptavargaja_bala,
                    'ojha_yugma_bala': ojha_yugma_bala,
                    'kendradi_bala': kendradi_bala,
                    'drekkana_bala': drekkana_bala,
                },
                'ayan_bala': ayan_bala,
                'kala_components': kala_components,
            },
        }

    # Parashara's Light ranks by strength relative to each planet's own
    # minimum, not by the raw Shadbala total.
    ranked = sorted(
        results.items(),
        key=lambda item: (
            -(item[1]['total_points'] / item[1]['minimum_required_points']),
            item[0],
        ),
    )
    for rank, (planet_name, _data) in enumerate(ranked, start=1):
        results[planet_name]['relative_rank'] = rank
    return results
