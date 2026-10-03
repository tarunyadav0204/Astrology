import swisseph as swe
from .base_calculator import BaseCalculator
from .chart_calculator import resolve_ayanamsha_mode, _SWISSEPH_CHART_LOCK
from utils.calendar_date import parse_calendar_date_y_m_d
from utils.timezone_service import parse_timezone_offset

class TransitCalculator(BaseCalculator):
    """Extract transit calculation logic from main.py"""
    
    def calculate_transits(
        self,
        birth_data,
        transit_date,
        ayanamsha='lahiri',
        node_type='mean',
    ):
        """Calculate transit planetary positions for given date"""
        _, sid_mode = resolve_ayanamsha_mode(ayanamsha)
        node_key = str(node_type or 'mean').strip().lower()
        if node_key not in {'mean', 'true'}:
            raise ValueError(f"Unsupported lunar node type: {node_type}")
        transit_year, transit_month, transit_day = parse_calendar_date_y_m_d(transit_date)
        jd = swe.julday(transit_year, transit_month, transit_day, 12.0)
        
        # Calculate transit planetary positions
        planets = {}
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):
            with _SWISSEPH_CHART_LOCK:
                try:
                    swe.set_sid_mode(sid_mode)
                    if planet <= 6:
                        pos = swe.calc_ut(
                            jd,
                            planet,
                            swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH,
                        )
                    else:
                        node_planet = swe.TRUE_NODE if node_key == 'true' else swe.MEAN_NODE
                        pos = swe.calc_ut(
                            jd,
                            node_planet,
                            swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH,
                        )
                finally:
                    swe.set_sid_mode(swe.SIDM_LAHIRI)
            
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
        
        # Get timezone offset using centralized service
        tz_offset = parse_timezone_offset(
            getattr(birth_data, 'timezone', ''),
            getattr(birth_data, 'latitude', None),
            getattr(birth_data, 'longitude', None),
            for_date=getattr(birth_data, 'date', None),
        )
        
        utc_hour = hour - tz_offset
        birth_year, birth_month, birth_day = parse_calendar_date_y_m_d(birth_data.date)
        birth_jd = swe.julday(birth_year, birth_month, birth_day, utc_hour)
        
        with _SWISSEPH_CHART_LOCK:
            try:
                swe.set_sid_mode(sid_mode)
                birth_houses_data = swe.houses(birth_jd, birth_data.latitude, birth_data.longitude, b'P')
                birth_ayanamsa = swe.get_ayanamsa_ut(birth_jd)
            finally:
                swe.set_sid_mode(swe.SIDM_LAHIRI)
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
