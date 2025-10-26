import swisseph as swe
from .base_calculator import BaseCalculator

class TransitCalculator(BaseCalculator):
    """Extract transit calculation logic from main.py"""
    
    def calculate_transits(self, birth_data, transit_date):
        """Calculate transit planetary positions for given date"""
        jd = swe.julday(
            int(transit_date.split('-')[0]),
            int(transit_date.split('-')[1]),
            int(transit_date.split('-')[2]),
            12.0
        )
        
        # Calculate transit planetary positions
        planets = {}
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):
            if planet <= 6:
                pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            else:
                pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            
            pos_array = pos[0]
            longitude = pos_array[0]
            speed = pos_array[3] if len(pos_array) > 3 else 0.0
            
            if planet == 12:  # Ketu
                longitude = (longitude + 180) % 360
            
            is_retrograde = speed < 0 if planet <= 6 else False
            
            planets[planet_names[i]] = {
                'longitude': longitude,
                'sign': int(longitude / 30),
                'degree': longitude % 30,
                'retrograde': is_retrograde
            }
        
        # Calculate birth chart houses for transit display
        time_parts = birth_data.time.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        if 6.0 <= birth_data.latitude <= 37.0 and 68.0 <= birth_data.longitude <= 97.0:
            tz_offset = 5.5
        else:
            tz_offset = 0
            if birth_data.timezone.startswith('UTC'):
                tz_str = birth_data.timezone[3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
        
        utc_hour = hour - tz_offset
        birth_jd = swe.julday(
            int(birth_data.date.split('-')[0]),
            int(birth_data.date.split('-')[1]),
            int(birth_data.date.split('-')[2]),
            utc_hour
        )
        
        birth_houses_data = swe.houses(birth_jd, birth_data.latitude, birth_data.longitude, b'P')
        birth_ayanamsa = swe.get_ayanamsa_ut(birth_jd)
        birth_ascendant_tropical = birth_houses_data[1][0]
        birth_ascendant_sidereal = (birth_ascendant_tropical - birth_ayanamsa) % 360
        
        ascendant_sign = int(birth_ascendant_sidereal / 30)
        houses = []
        for i in range(12):
            house_sign = (ascendant_sign + i) % 12
            house_longitude = (house_sign * 30) + (birth_ascendant_sidereal % 30)
            houses.append({
                'longitude': house_longitude % 360,
                'sign': house_sign
            })
        
        return {
            "planets": planets,
            "houses": houses,
            "ayanamsa": birth_ayanamsa,
            "ascendant": birth_ascendant_sidereal
        }