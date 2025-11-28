import swisseph as swe
from .base_calculator import BaseCalculator

class ChartCalculator(BaseCalculator):
    """Extract chart calculation logic from main.py"""
    
    def __init__(self, *args, **kwargs):
        """Initialize with Lahiri Ayanamsa as default"""
        super().__init__(*args, **kwargs)
        # CRITICAL: Always ensure Lahiri Ayanamsa is set
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    def calculate_chart(self, birth_data, node_type='mean'):
        """Calculate birth chart with planetary positions and houses"""
        # CRITICAL: Ensure Ayanamsa is set to Lahiri (safety check)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # Calculate Julian Day with proper timezone handling
        time_parts = birth_data.time.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        print(f"DEBUG: Birth data - Date: {birth_data.date}, Time: {birth_data.time}, Timezone: {getattr(birth_data, 'timezone', 'None')}")
        
        # Parse timezone offset with proper global handling
        tz_offset = 0
        if hasattr(birth_data, 'timezone') and birth_data.timezone:
            if birth_data.timezone.startswith('UTC'):
                tz_str = birth_data.timezone[3:]  # Remove 'UTC'
                if tz_str:
                    if ':' in tz_str:
                        # Handle UTC+5:30 format
                        sign = 1 if tz_str[0] == '+' else -1
                        parts = tz_str[1:].split(':')
                        tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
                    else:
                        # Handle UTC+5 format
                        tz_offset = float(tz_str)
        
        # Override with geographic timezone for specific regions if timezone seems incorrect
        if 6.0 <= birth_data.latitude <= 37.0 and 68.0 <= birth_data.longitude <= 97.0:
            # Indian coordinates - verify IST
            if abs(tz_offset - 5.5) > 0.1:  # If not IST, override
                print(f"DEBUG: Indian coordinates with incorrect timezone {birth_data.timezone} (offset: {tz_offset}), overriding to IST")
                tz_offset = 5.5
            else:
                print(f"DEBUG: Indian coordinates with correct IST timezone: {tz_offset}")
        else:
            print(f"DEBUG: Non-Indian coordinates, using timezone: {getattr(birth_data, 'timezone', 'None')} -> offset: {tz_offset}")
        
        # Convert local time to UTC
        utc_hour = hour - tz_offset
        print(f"DEBUG: Local time: {hour}, UTC time: {utc_hour}, Timezone offset: {tz_offset}, Coordinates: ({birth_data.latitude}, {birth_data.longitude})")
        
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
            
            # Calculate retrograde status
            is_retrograde = speed < 0
            # Force True for Mean Nodes (standard in Vedic astrology)
            if planet in [11, 12] and node_type == 'mean':
                is_retrograde = True
            
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
        print(f"DEBUG: Tropical ASC: {ascendant_tropical:.6f}, Ayanamsa: {ayanamsa:.6f}, Sidereal ASC: {ascendant_sidereal:.6f}, Final TZ Offset: {tz_offset}")
        asc_sign_num = int(ascendant_sidereal / 30)
        asc_sign_name = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][asc_sign_num]
        print(f"DEBUG: ASC Sign: {asc_sign_num} ({asc_sign_name})")
        
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
        
        # Calculate Gulika and Mandi using accurate sunrise/sunset
        self._calculate_upagrahas(jd, birth_data.latitude, birth_data.longitude, planets, ayanamsa)
        
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
            if 'house' not in planets[planet_name] or planets[planet_name]['house'] == 1:
                planet_longitude = planets[planet_name]['longitude']
                planet_sign = int(planet_longitude / 30)
                house_number = ((planet_sign - ascendant_sign) % 12) + 1
                planets[planet_name]['house'] = house_number
        
        # Calculate Bhav Chalit using professional house system
        bhav_chalit = self._calculate_bhav_chalit_professional(jd, birth_data.latitude, birth_data.longitude, planets, ayanamsa)
        
        return {
            "planets": planets,
            "houses": houses,
            "ayanamsa": ayanamsa,
            "ascendant": ascendant_sidereal,
            "bhav_chalit": bhav_chalit
        }
    
    def _calculate_bhav_chalit_professional(self, jd, lat, lon, planets, ayanamsa):
        """Calculate Bhav Chalit using Placidus house system (professional KP/Sripati method)"""
        # Ensure Lahiri Ayanamsa for house calculations
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        try:
            # Use Placidus house system (P) for accurate unequal houses
            cusps, ascmc = swe.houses_ex(jd, lat, lon, b'P')
            
            # Convert tropical cusps to sidereal - ensure we have 12 cusps
            sidereal_cusps = [(cusp - ayanamsa) % 360 for cusp in cusps[1:13]]  # Take exactly 12 cusps
            
            # Ensure we have exactly 12 cusps
            if len(sidereal_cusps) < 12:
                # Fallback to equal houses if cusps are incomplete
                asc_sidereal = (ascmc[0] - ayanamsa) % 360
                sidereal_cusps = [(asc_sidereal + i * 30) % 360 for i in range(12)]
            
            bhav_planets = {}
            
            for planet_name, planet_data in planets.items():
                planet_longitude = planet_data['longitude']
                
                # Find which house this longitude falls into
                planet_house = 1
                for i in range(12):
                    start = sidereal_cusps[i]
                    end = sidereal_cusps[(i + 1) % 12]
                    
                    # Handle 360° crossover (Pisces to Aries)
                    if end < start:
                        if planet_longitude >= start or planet_longitude < end:
                            planet_house = i + 1
                            break
                    else:
                        if start <= planet_longitude < end:
                            planet_house = i + 1
                            break
                
                bhav_planets[planet_name] = {
                    'longitude': planet_longitude,
                    'sign': planet_data['sign'],
                    'degree': planet_data['degree'],
                    'house': planet_house,
                    'retrograde': planet_data.get('retrograde', False)
                }
            
            return {
                'planets': bhav_planets,
                'cusps': sidereal_cusps,
                'ascendant': (ascmc[0] - ayanamsa) % 360
            }
        except Exception as e:
            # Fallback to whole sign houses if Bhav Chalit fails
            asc_sidereal = (ayanamsa) % 360
            bhav_planets = {}
            for planet_name, planet_data in planets.items():
                bhav_planets[planet_name] = planet_data.copy()
            
            return {
                'planets': bhav_planets,
                'cusps': [(i * 30) for i in range(12)],
                'ascendant': asc_sidereal
            }
    
    def _calculate_upagrahas(self, jd, lat, lon, planets, ayanamsa):
        """Calculate Gulika and Mandi based on actual sunrise/sunset (Dinamaan)"""
        # Ensure Lahiri Ayanamsa for upagraha calculations
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        try:
            # Get sunrise and sunset for the day (single call)
            sun_transit = swe.rise_trans(jd, swe.SUN, '', swe.FLG_SWIEPH, lon, lat, 0)
            
            sunrise_jd = sun_transit[1][0]  # Index 1 is Rise
            sunset_jd = sun_transit[2][0]   # Index 2 is Set
            
            # Check if birth is day or night
            is_day_birth = sunrise_jd <= jd < sunset_jd
            
            # Calculate day/night duration
            day_duration = sunset_jd - sunrise_jd
            night_duration = (sunrise_jd + 1.0) - sunset_jd
            
            current_duration = day_duration if is_day_birth else night_duration
            part_length = current_duration / 8
            
            # Weekday mapping for Saturn's segment
            weekday = int((jd + 1.5) % 7)
            gulika_indices_day = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0}
            gulika_indices_night = {0: 2, 1: 1, 2: 0, 3: 6, 4: 5, 5: 4, 6: 3}
            
            if is_day_birth:
                segment_index = gulika_indices_day[weekday]
                start_time_jd = sunrise_jd + (segment_index * part_length)
            else:
                segment_index = gulika_indices_night[weekday]
                start_time_jd = sunset_jd + (segment_index * part_length)
            
            # Calculate Gulika longitude at Saturn's segment start
            houses_gulika = swe.houses(start_time_jd, lat, lon, b'P')
            gulika_long = (houses_gulika[1][0] - ayanamsa) % 360
            
            # Mandi at middle of Saturn's segment
            mandi_time_jd = start_time_jd + (part_length / 2)
            houses_mandi = swe.houses(mandi_time_jd, lat, lon, b'P')
            mandi_long = (houses_mandi[1][0] - ayanamsa) % 360
            
        except Exception:
            # Fallback to approximate calculation if sunrise/sunset fails
            weekday = int((jd + 1.5) % 7)
            gulika_portions = [10.5, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0]
            mandi_portions = [7.5, 15.0, 22.5, 6.0, 13.5, 21.0, 4.5]
            
            gulika_long = ((gulika_portions[weekday] * 15) - ayanamsa) % 360
            mandi_long = ((mandi_portions[weekday] * 15) - ayanamsa) % 360
            
            if gulika_long < 0:
                gulika_long += 360
            if mandi_long < 0:
                mandi_long += 360
        
        # Add to planets dict
        for name, longitude in [('Gulika', gulika_long), ('Mandi', mandi_long)]:
            planets[name] = {
                'longitude': longitude,
                'sign': int(longitude / 30),
                'degree': longitude % 30,
                'house': 1  # Will be calculated later
            }
    
    def get_baladi_avastha(self, planet_name: str, degree: float, sign: int) -> str:
        """Calculate Planetary Age (State of Maturity)"""
        if planet_name in ['Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna']:
            return "N/A"
            
        is_odd_sign = (sign + 1) % 2 != 0
        
        if 0 <= degree < 6:
            return "Bal (Infant - 25% Strength)" if is_odd_sign else "Mrit (Dead - 0% Strength)"
        elif 6 <= degree < 12:
            return "Kumar (Teen - 50% Strength)" if is_odd_sign else "Vriddha (Old - Minimal Strength)"
        elif 12 <= degree < 18:
            return "Yuva (Youth - 100% Strength)"
        elif 18 <= degree < 24:
            return "Vriddha (Old - Minimal Strength)" if is_odd_sign else "Kumar (Teen - 50% Strength)"
        elif 24 <= degree < 30:
            return "Mrit (Dead - 0% Strength)" if is_odd_sign else "Bal (Infant - 25% Strength)"
        
        return "Unknown"