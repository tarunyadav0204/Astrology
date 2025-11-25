import swisseph as swe
from .base_calculator import BaseCalculator

class ChartCalculator(BaseCalculator):
    """Extract chart calculation logic from main.py"""
    
    def calculate_chart(self, birth_data, node_type='mean'):
        """Calculate birth chart with planetary positions and houses"""
        # Calculate Julian Day with proper timezone handling
        time_parts = birth_data.time.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        # Auto-detect IST for Indian coordinates, otherwise parse timezone
        if 6.0 <= birth_data.latitude <= 37.0 and 68.0 <= birth_data.longitude <= 97.0:
            tz_offset = 5.5
        else:
            tz_offset = 0
            if birth_data.timezone.startswith('UTC'):
                tz_str = birth_data.timezone[3:]
                if tz_str:
                    if ':' in tz_str:
                        sign = 1 if tz_str[0] == '+' else -1
                        parts = tz_str[1:].split(':')
                        tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
                    else:
                        tz_offset = float(tz_str)
        
        # Convert local time to UTC
        utc_hour = hour - tz_offset
        
        jd = swe.julday(
            int(birth_data.date.split('-')[0]),
            int(birth_data.date.split('-')[1]),
            int(birth_data.date.split('-')[2]),
            utc_hour
        )
        
        # Calculate planetary positions
        planets = {}
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):
            if planet <= 6:
                pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            else:
                node_flag = swe.TRUE_NODE if node_type == 'true' else swe.MEAN_NODE
                pos = swe.calc_ut(jd, node_flag, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            
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

        # Calculate ascendant and houses
        houses_data = swe.houses(jd, birth_data.latitude, birth_data.longitude, b'P')
        ayanamsa = swe.get_ayanamsa_ut(jd)
        
        ascendant_tropical = houses_data[1][0]
        ascendant_sidereal = (ascendant_tropical - ayanamsa) % 360
        
        # Whole Sign houses based on sidereal ascendant
        ascendant_sign = int(ascendant_sidereal / 30)
        houses = []
        for i in range(12):
            house_sign = (ascendant_sign + i) % 12
            house_longitude = (house_sign * 30) + (ascendant_sidereal % 30)
            houses.append({
                'longitude': house_longitude % 360,
                'sign': house_sign
            })
        
        # Calculate Gulika and Mandi
        weekday = int((jd + 1.5) % 7)
        gulika_portions = [10.5, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0]
        mandi_portions = [7.5, 15.0, 22.5, 6.0, 13.5, 21.0, 4.5]
        
        gulika_longitude = ((gulika_portions[weekday] * 15) - ayanamsa) % 360
        mandi_longitude = ((mandi_portions[weekday] * 15) - ayanamsa) % 360
        
        if gulika_longitude < 0:
            gulika_longitude += 360
        if mandi_longitude < 0:
            mandi_longitude += 360
        
        # Add Gulika and Mandi
        for name, longitude in [('Gulika', gulika_longitude), ('Mandi', mandi_longitude)]:
            house_num = 1
            for house_idx in range(12):
                house_start = houses[house_idx]['longitude']
                house_end = (house_start + 30) % 360
                if house_start <= house_end:
                    if house_start <= longitude < house_end:
                        house_num = house_idx + 1
                        break
                else:
                    if longitude >= house_start or longitude < house_end:
                        house_num = house_idx + 1
                        break
            
            planets[name] = {
                'longitude': longitude,
                'sign': int(longitude / 30),
                'degree': longitude % 30,
                'house': house_num
            }
        
        # Add InduLagna
        from .indu_lagna_calculator import InduLagnaCalculator
        indu_calc = InduLagnaCalculator({
            'ascendant': ascendant_sidereal,
            'planets': planets
        })
        indu_data = indu_calc.get_indu_lagna_data()
        planets['InduLagna'] = indu_data
        
        # Calculate house positions for all planets
        for planet_name in planets:
            if 'house' not in planets[planet_name]:
                planet_longitude = planets[planet_name]['longitude']
                planet_sign = int(planet_longitude / 30)
                house_number = ((planet_sign - ascendant_sign) % 12) + 1
                planets[planet_name]['house'] = house_number
        
        return {
            "planets": planets,
            "houses": houses,
            "ayanamsa": ayanamsa,
            "ascendant": ascendant_sidereal
        }