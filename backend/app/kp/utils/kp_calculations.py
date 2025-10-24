import swisseph as swe
from datetime import datetime
from ..config.kp_constants import NAKSHATRAS, SUB_LORD_DIVISIONS, PLANET_ORDER, KP_AYANAMSA

class KPCalculations:
    @staticmethod
    def get_kp_ayanamsa(jd):
        """Calculate KP Ayanamsa for given Julian Day"""
        # Using Lahiri ayanamsa as base, KP uses slight modification
        lahiri = swe.get_ayanamsa(jd)
        return lahiri + 0.25  # KP adjustment
    
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
        """Calculate significators for each house"""
        significators = {i: [] for i in range(1, 13)}
        
        # Star lords (planets in nakshatras)
        for planet, position in planet_positions.items():
            nakshatra = KPCalculations.get_nakshatra_info(position)
            star_lord = nakshatra["lord"]
            
            # Find which house this planet is in
            house = KPCalculations.get_house_from_longitude(position, house_cusps)
            if house:
                significators[house].append(f"{star_lord} (Star lord of {planet})")
        
        # Sub lords of cusps
        for house_num, cusp_longitude in house_cusps.items():
            sub_lord = KPCalculations.get_sub_lord(cusp_longitude)
            significators[house_num].append(f"{sub_lord} (Sub lord of {house_num})")
        
        return significators
    
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
    def get_ruling_planets(birth_time, latitude, longitude):
        """Calculate KP ruling planets"""
        jd = swe.julday(birth_time.year, birth_time.month, birth_time.day, 
                       birth_time.hour + birth_time.minute/60.0)
        
        # Calculate ascendant
        houses = swe.houses(jd, latitude, longitude, b'P')  # Placidus
        asc_longitude = houses[1][0]  # Ascendant longitude
        
        # Ascendant ruling planet
        asc_nakshatra = KPCalculations.get_nakshatra_info(asc_longitude)
        asc_sub_lord = KPCalculations.get_sub_lord(asc_longitude)
        
        # Moon position and ruling planet
        moon_pos = swe.calc_ut(jd, swe.MOON)[0][0]
        moon_nakshatra = KPCalculations.get_nakshatra_info(moon_pos)
        moon_sub_lord = KPCalculations.get_sub_lord(moon_pos)
        
        # Day lord (based on weekday)
        day_lords = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        day_lord = day_lords[birth_time.weekday()]
        
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