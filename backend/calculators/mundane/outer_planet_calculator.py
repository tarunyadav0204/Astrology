import swisseph as swe
from typing import Dict, Any
from datetime import datetime

class OuterPlanetCalculator:
    """Calculates positions of Uranus, Neptune, and Pluto - the Era Markers"""
    
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    def calculate_outer_planets(self, date: datetime, latitude: float, longitude: float) -> Dict[str, Any]:
        """Calculate positions of outer planets for a given date and location"""
        jd = swe.julday(date.year, date.month, date.day, 
                       date.hour + date.minute/60.0 + date.second/3600.0)
        
        planets = {}
        planet_ids = {
            'Uranus': swe.URANUS,
            'Neptune': swe.NEPTUNE,
            'Pluto': swe.PLUTO
        }
        
        for name, planet_id in planet_ids.items():
            pos = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)[0]
            longitude_deg = pos[0]
            speed = pos[3]
            
            planets[name] = {
                'longitude': round(longitude_deg, 4),
                'sign': int(longitude_deg / 30),
                'sign_name': self._get_sign_name(int(longitude_deg / 30)),
                'degree_in_sign': round(longitude_deg % 30, 4),
                'speed': round(speed, 6),
                'is_retrograde': speed < 0,
                'nakshatra': self._get_nakshatra(longitude_deg)
            }
        
        return planets
    
    def _get_sign_name(self, sign_num: int) -> str:
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_num % 12]
    
    def _get_nakshatra(self, longitude: float) -> Dict[str, Any]:
        nakshatras = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
            'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
            'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
            'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
            'Uttara Bhadrapada', 'Revati'
        ]
        
        nakshatra_span = 360 / 27
        nak_index = int(longitude / nakshatra_span)
        pada = int((longitude % nakshatra_span) / (nakshatra_span / 4)) + 1
        
        return {
            'name': nakshatras[nak_index % 27],
            'pada': pada
        }
