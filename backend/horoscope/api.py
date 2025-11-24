from datetime import datetime
from typing import Dict
from .generators.western_generator import WesternHoroscopeGenerator
from .generators.accurate_generator import AccurateHoroscopeGenerator

class HoroscopeAPI:
    def __init__(self):
        self.western_generator = WesternHoroscopeGenerator()
        self.accurate_generator = AccurateHoroscopeGenerator()
    
    def get_daily_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()
            
        # Use accurate generator for real astronomical data
        horoscope = self.accurate_generator.generate_accurate_horoscope(
            zodiac_sign.capitalize(), date, 'daily'
        )
        
        return {
            'zodiac_sign': zodiac_sign,
            'date': date.strftime('%Y-%m-%d'),
            'period': 'daily',
            **horoscope
        }
    
    def get_weekly_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()
            
        # Use accurate generator for real astronomical data
        horoscope = self.accurate_generator.generate_accurate_horoscope(
            zodiac_sign.capitalize(), date, 'weekly'
        )
        
        return {
            'zodiac_sign': zodiac_sign,
            'date': date.strftime('%Y-%m-%d'),
            'period': 'weekly',
            **horoscope
        }
    
    def get_monthly_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()
            
        # Use accurate generator for real astronomical data
        horoscope = self.accurate_generator.generate_accurate_horoscope(
            zodiac_sign.capitalize(), date, 'monthly'
        )
        
        return {
            'zodiac_sign': zodiac_sign,
            'date': date.strftime('%Y-%m-%d'),
            'period': 'monthly',
            **horoscope
        }
    
    def get_yearly_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()
            
        # Use accurate generator for real astronomical data
        horoscope = self.accurate_generator.generate_accurate_horoscope(
            zodiac_sign.capitalize(), date, 'yearly'
        )
        
        return {
            'zodiac_sign': zodiac_sign,
            'date': date.strftime('%Y-%m-%d'),
            'period': 'yearly',
            **horoscope
        }