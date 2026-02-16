import swisseph as swe
from datetime import datetime
from ..config.kp_constants import NAKSHATRAS, SUB_LORD_DIVISIONS, PLANET_ORDER, KP_AYANAMSA

class KPCalculations:
    @staticmethod
    def get_nakshatra_info(longitude):
        """Get nakshatra information for given longitude"""
        # Normalize longitude to 0-360 range
        longitude = longitude % 360
        
        for nakshatra in NAKSHATRAS:
            if nakshatra["start"] <= longitude < nakshatra["end"]:
                return nakshatra
        
        # Handle edge case - if longitude is exactly 360 or close to it
        if longitude >= 359.999:
            return NAKSHATRAS[-1]  # Revati
        
        # Fallback - find closest nakshatra
        for nakshatra in NAKSHATRAS:
            if longitude < nakshatra["end"]:
                return nakshatra
        
        return NAKSHATRAS[0]  # Ashwini as final fallback
    
    @staticmethod
    def get_sub_lord(longitude):
        """Calculate sub-lord using exact working KP method"""
        from .working_kp import find_sublord
        _, sub_ruler, _, _, _ = find_sublord(longitude)
        return sub_ruler
    
    @staticmethod
    def get_sub_sub_lord(longitude):
        """Calculate sub-sub lord using exact working KP method"""
        from .working_kp import find_sub_sublord
        return find_sub_sublord(longitude)
    
    @staticmethod
    def get_significators(planet_positions, house_cusps):
        """Calculate significators for each house and planet using standard KP 4-level logic"""
        house_significators = {i: [] for i in range(1, 13)}
        planet_significators = {p: set() for p in planet_positions.keys() if p != 'Ascendant'}
        planet_house_map = {}
        
        # 1. Map planets to houses
        for planet, position in planet_positions.items():
            if planet == 'Ascendant': continue
            house = KPCalculations.get_house_from_longitude(position, house_cusps)
            planet_house_map[planet] = house

        # 2. Calculate significators for each house
        for house_num in range(1, 13):
            house_sigs = set()
            
            # Level 1: Planets in the Nakshatra of planets in the house
            planets_in_house = [p for p, h in planet_house_map.items() if h == house_num]
            for p_in_h in planets_in_house:
                for planet, pos in planet_positions.items():
                    if planet == 'Ascendant': continue
                    nak_info = KPCalculations.get_nakshatra_info(pos)
                    if nak_info["lord"] == p_in_h:
                        house_sigs.add(planet)
                        planet_significators[planet].add(house_num)
            
            # Level 2: Planets in the house
            for p_in_h in planets_in_house:
                house_sigs.add(p_in_h)
                planet_significators[p_in_h].add(house_num)
                
            # Level 3: Planets in the Nakshatra of the house lord
            cusp_pos = house_cusps[house_num]
            house_lord = KPCalculations.get_sign_lord(cusp_pos)
            for planet, pos in planet_positions.items():
                if planet == 'Ascendant': continue
                nak_info = KPCalculations.get_nakshatra_info(pos)
                if nak_info["lord"] == house_lord:
                    house_sigs.add(planet)
                    planet_significators[planet].add(house_num)
            
            # Level 4: The house lord itself
            house_sigs.add(house_lord)
            if house_lord in planet_significators:
                planet_significators[house_lord].add(house_num)
            
            house_significators[house_num] = sorted(list(house_sigs))
        
        # Convert sets to sorted lists for JSON serialization
        planet_significators_list = {p: sorted(list(h_list)) for p, h_list in planet_significators.items()}
        
        return {
            "house_significators": house_significators,
            "planet_significators": planet_significators_list
        }
    
    @staticmethod
    def get_house_from_longitude(longitude, house_cusps):
        """Determine which house a longitude falls into"""
        for house in range(1, 13):
            next_house = house + 1 if house < 12 else 1
            start = house_cusps[house]
            end = house_cusps[next_house]
            
            if start < end:
                if start <= longitude < end:
                    return house
            else:  # Crosses 0 degrees
                if longitude >= start or longitude < end:
                    return house
        return 1  # Fallback
    
    @staticmethod
    def get_ruling_planets(birth_date, birth_time, latitude, longitude, timezone):
        """Calculate KP ruling planets with correct timezone handling."""
        try:
            from utils.timezone_service import parse_timezone_offset
        except ImportError:
            pass

        # Calculate Julian Day in UTC
        time_parts = birth_time.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60.0
        tz_offset = parse_timezone_offset(timezone, latitude, longitude)
        utc_hour = hour - tz_offset
        year, month, day = [int(p) for p in birth_date.split('-')]
        jd = swe.julday(year, month, day, utc_hour)

        # CRITICAL: Set sidereal mode BEFORE getting ayanamsa
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        ayanamsa = swe.get_ayanamsa_ut(jd)

        # Calculate Ascendant
        # Note: swe.houses always returns tropical positions regardless of sidereal mode
        cusps_tropical, ascmc_tropical = swe.houses(jd, latitude, longitude, b'P')
        
        # Apply Ayanamsa and Correction Factor to get Sidereal Ascendant
        # Using the same correction factor as the main chart for consistency
        CORRECTION_FACTOR = 0.00653
        asc_longitude = (ascmc_tropical[0] - ayanamsa - CORRECTION_FACTOR) % 360

        # Ascendant lords
        asc_nakshatra = KPCalculations.get_nakshatra_info(asc_longitude)
        asc_sub_lord = KPCalculations.get_sub_lord(asc_longitude)

        # Moon position and lords
        # swe.calc_ut with FLG_SIDEREAL respects the set_sid_mode
        moon_pos_raw = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        moon_pos = (moon_pos_raw - CORRECTION_FACTOR) % 360
        
        moon_nakshatra = KPCalculations.get_nakshatra_info(moon_pos)
        moon_sub_lord = KPCalculations.get_sub_lord(moon_pos)

        # Day lord (based on local weekday)
        local_dt = datetime(year, month, day)
        # Python weekday(): Monday is 0 and Sunday is 6
        # Day lords: Sun=Sun, Mon=Moon, Tue=Mars, Wed=Mercury, Thu=Jupiter, Fri=Venus, Sat=Saturn
        day_lords = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
        day_lord = day_lords[local_dt.weekday()]
        
        return {
            "ascendant": {
                "sign_lord": KPCalculations.get_sign_lord(asc_longitude),
                "star_lord": asc_nakshatra["lord"],
                "sub_lord": asc_sub_lord
            },
            "moon": {
                "sign_lord": KPCalculations.get_sign_lord(moon_pos),
                "star_lord": moon_nakshatra["lord"],
                "sub_lord": moon_sub_lord
            },
            "day_lord": day_lord
        }
    
    @staticmethod
    def get_sign_lord(longitude):
        """Get sign lord for given longitude"""
        sign_lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                     "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
        sign_num = int(longitude // 30)
        return sign_lords[sign_num]