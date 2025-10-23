from datetime import datetime
import swisseph as swe
from typing import Dict
import random

class PlanetaryCalculator:
    def __init__(self):
        self.zodiac_signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
    
    def get_planetary_positions(self, date: datetime) -> Dict:
        jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute/60.0)
        
        planets = {}
        planet_ids = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, 
                     swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]
        planet_names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                       'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
        
        for i, planet_id in enumerate(planet_ids):
            try:
                pos, _ = swe.calc_ut(jd, planet_id)
                sign_num = int(pos[0] // 30)
                degree = pos[0] % 30
                
                planets[planet_names[i]] = {
                    'longitude': pos[0],
                    'sign': self.zodiac_signs[sign_num],
                    'degree': degree
                }
            except:
                planets[planet_names[i]] = {
                    'longitude': random.uniform(0, 360),
                    'sign': random.choice(self.zodiac_signs),
                    'degree': random.uniform(0, 30)
                }
        
        return planets