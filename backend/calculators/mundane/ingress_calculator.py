import swisseph as swe
from typing import Dict, Any, List
from datetime import datetime, timedelta

class IngressCalculator:
    """Calculates exact moments when Sun enters Cardinal Signs (Aries, Cancer, Libra, Capricorn)"""
    
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    def calculate_yearly_ingresses(self, year: int, latitude: float, longitude: float) -> Dict[str, Any]:
        """Calculate all four cardinal ingresses for a given year"""
        ingresses = {
            'Aries': self._find_ingress(year, 0, latitude, longitude),
            'Cancer': self._find_ingress(year, 90, latitude, longitude),
            'Libra': self._find_ingress(year, 180, latitude, longitude),
            'Capricorn': self._find_ingress(year, 270, latitude, longitude)
        }
        
        return {
            'year': year,
            'ingresses': ingresses,
            'aries_ingress_chart': self._calculate_ingress_chart(ingresses['Aries'], latitude, longitude)
        }
    
    def _find_ingress(self, year: int, target_longitude: float, latitude: float, longitude: float) -> Dict[str, Any]:
        """Find exact moment Sun reaches target longitude"""
        # Start search from appropriate month based on target
        if target_longitude == 0:  # Aries (March-April)
            search_date = datetime(year, 3, 15, 0, 0, 0)
        elif target_longitude == 90:  # Cancer (June-July)
            search_date = datetime(year, 6, 15, 0, 0, 0)
        elif target_longitude == 180:  # Libra (September-October)
            search_date = datetime(year, 9, 15, 0, 0, 0)
        elif target_longitude == 270:  # Capricorn (December-January)
            search_date = datetime(year, 12, 15, 0, 0, 0)
        else:
            search_date = datetime(year, 1, 1, 0, 0, 0)
        
        # Binary search for exact moment
        for _ in range(100):  # Max iterations
            jd = swe.julday(search_date.year, search_date.month, search_date.day,
                           search_date.hour + search_date.minute/60.0)
            sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
            
            # Calculate shortest angular distance (handles 360/0 wrap)
            diff = (target_longitude - sun_pos + 180) % 360 - 180
            
            if abs(diff) < 0.0001:  # Within 0.36 seconds
                break
            
            # Adjust search date (Sun moves ~1 degree per day)
            search_date += timedelta(days=diff)
        
        return {
            'datetime': search_date.isoformat(),
            'sun_longitude': round(sun_pos, 6),
            'sign': self._get_sign_name(int(target_longitude / 30))
        }
    
    def _calculate_ingress_chart(self, ingress_data: Dict, latitude: float, longitude: float) -> Dict[str, Any]:
        """Calculate full chart for ingress moment"""
        dt = datetime.fromisoformat(ingress_data['datetime'])
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        
        # Calculate ascendant
        asc_data = swe.houses_ex(jd, latitude, longitude, b'P')
        ascendant = asc_data[0][0]
        
        # Calculate all planets
        planets = {}
        planet_ids = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
            'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS,
            'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE
        }
        
        for name, planet_id in planet_ids.items():
            pos = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)[0]
            planets[name] = {
                'longitude': round(pos[0], 4),
                'sign': int(pos[0] / 30),
                'house': self._calculate_house(pos[0], ascendant)
            }
        
        # Add Ketu (opposite Rahu)
        planets['Ketu'] = {
            'longitude': round((planets['Rahu']['longitude'] + 180) % 360, 4),
            'sign': int(((planets['Rahu']['longitude'] + 180) % 360) / 30),
            'house': self._calculate_house((planets['Rahu']['longitude'] + 180) % 360, ascendant)
        }
        
        return {
            'ascendant': round(ascendant, 4),
            'planets': planets,
            'datetime': ingress_data['datetime']
        }
    
    def _calculate_house(self, planet_long: float, ascendant: float) -> int:
        """Calculate house position using whole sign system"""
        asc_sign = int(ascendant / 30)
        planet_sign = int(planet_long / 30)
        house = ((planet_sign - asc_sign) % 12) + 1
        return house
    
    def _get_sign_name(self, sign_num: int) -> str:
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_num % 12]
