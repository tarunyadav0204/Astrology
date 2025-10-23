from datetime import datetime
from typing import Dict
from .generators.western_generator import WesternHoroscopeGenerator

class HoroscopeAPI:
    def __init__(self):
        self.western_generator = WesternHoroscopeGenerator()
    
    def get_daily_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()
            
        horoscope = self.western_generator.generate_comprehensive_horoscope(
            zodiac_sign, 'daily', date
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
            
        horoscope = self.western_generator.generate_comprehensive_horoscope(
            zodiac_sign, 'weekly', date
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
            
        horoscope = self.western_generator.generate_comprehensive_horoscope(
            zodiac_sign, 'monthly', date
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
            
        horoscope = self.western_generator.generate_comprehensive_horoscope(
            zodiac_sign, 'yearly', date
        )
        
        return {
            'zodiac_sign': zodiac_sign,
            'date': date.strftime('%Y-%m-%d'),
            'period': 'yearly',
            **horoscope
        }