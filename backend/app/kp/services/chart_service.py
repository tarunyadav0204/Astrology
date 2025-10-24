import swisseph as swe
from datetime import datetime
from ..utils.kp_calculations import KPCalculations

class KPChartService:
    @staticmethod
    def calculate_kp_chart(birth_date, birth_time, latitude, longitude, timezone_offset=0):
        """Calculate KP chart with Placidus houses"""
        try:
            # Parse datetime
            birth_datetime = datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M")
            
            # Calculate Julian Day (convert to UTC)
            # For Indian locations, if timezone_offset is 0, assume IST (+5:30)
            if timezone_offset == 0 and 68 <= longitude <= 97 and 8 <= latitude <= 37:
                timezone_offset = -5.5  # IST is UTC+5:30, so subtract 5.5 hours
            
            jd = swe.julday(birth_datetime.year, birth_datetime.month, birth_datetime.day,
                           birth_datetime.hour + birth_datetime.minute/60.0 + timezone_offset)
            
            # Get KP ayanamsa
            ayanamsa = KPCalculations.get_kp_ayanamsa(jd)
            
            # Calculate houses using Placidus system
            houses_data = swe.houses(jd, latitude, longitude, b'P')
            house_cusps = {}
            for i in range(12):
                # Apply ayanamsa correction for sidereal house cusps
                house_cusps[i + 1] = (houses_data[0][i] - ayanamsa) % 360
            
            # Calculate planet positions
            planets = {
                'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
                'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS,
                'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE, 'Ketu': swe.MEAN_NODE
            }
            
            planet_positions = {}
            for name, planet_id in planets.items():
                if name == 'Ketu':
                    # Ketu is 180 degrees opposite to Rahu
                    rahu_pos = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
                    ketu_pos = (rahu_pos + 180) % 360
                    # Apply ayanamsa correction for sidereal position
                    planet_positions[name] = (ketu_pos - ayanamsa) % 360
                else:
                    pos = swe.calc_ut(jd, planet_id)[0][0]
                    # Apply ayanamsa correction for sidereal position
                    planet_positions[name] = (pos - ayanamsa) % 360
            
            # Calculate sub-lords and sub-sub lords for planets and cusps
            planet_sub_lords = {}
            planet_sub_sub_lords = {}
            for planet, position in planet_positions.items():
                if planet == 'Sun':
                    print(f"\n=== SUN ONLY DEBUG ===")
                    print(f"Sun longitude: {position}")
                    sub_lord = KPCalculations.get_sub_lord(position)
                    sub_sub_lord = KPCalculations.get_sub_sub_lord(position)
                    print(f"Sun sub-lord: {sub_lord}")
                    print(f"Sun sub-sub-lord: {sub_sub_lord}")
                    print(f"=== END SUN DEBUG ===\n")
                    planet_sub_lords[planet] = sub_lord
                    planet_sub_sub_lords[planet] = sub_sub_lord
                else:
                    planet_sub_lords[planet] = KPCalculations.get_sub_lord(position)
                    planet_sub_sub_lords[planet] = KPCalculations.get_sub_sub_lord(position)
            
            cusp_sub_lords = {}
            for house, cusp in house_cusps.items():
                cusp_sub_lords[house] = KPCalculations.get_sub_lord(cusp)
            
            # Calculate significators
            significators = KPCalculations.get_significators(planet_positions, house_cusps)
            
            return {
                "house_cusps": house_cusps,
                "planet_positions": planet_positions,
                "planet_sub_lords": planet_sub_lords,
                "planet_sub_sub_lords": planet_sub_sub_lords,
                "cusp_sub_lords": cusp_sub_lords,
                "significators": significators,
                "ayanamsa": ayanamsa
            }
            
        except Exception as e:
            raise Exception(f"Error calculating KP chart: {str(e)}")
    
    @staticmethod
    def get_planet_house_positions(planet_positions, house_cusps):
        """Get which house each planet is positioned in"""
        planet_houses = {}
        for planet, longitude in planet_positions.items():
            house = KPCalculations.get_house_from_longitude(longitude, house_cusps)
            planet_houses[planet] = house
        return planet_houses