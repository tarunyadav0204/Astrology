from datetime import datetime
from typing import Dict
from .generators.western_generator import WesternHoroscopeGenerator
from .generators.accurate_generator import AccurateHoroscopeGenerator

class HoroscopeAPI:
    VALID_SIGNS = {
        'aries': 'Aries',
        'taurus': 'Taurus',
        'gemini': 'Gemini',
        'cancer': 'Cancer',
        'leo': 'Leo',
        'virgo': 'Virgo',
        'libra': 'Libra',
        'scorpio': 'Scorpio',
        'sagittarius': 'Sagittarius',
        'capricorn': 'Capricorn',
        'aquarius': 'Aquarius',
        'pisces': 'Pisces',
    }

    VALID_PERIODS = {'daily', 'weekly', 'monthly', 'yearly'}

    def __init__(self):
        self.western_generator = WesternHoroscopeGenerator()
        self.accurate_generator = AccurateHoroscopeGenerator()

    def _normalize_sign(self, zodiac_sign: str) -> str:
        normalized = self.VALID_SIGNS.get(str(zodiac_sign or '').strip().lower())
        if not normalized:
            raise ValueError(f"Unsupported zodiac sign: {zodiac_sign}")
        return normalized

    def _normalize_period(self, period: str) -> str:
        normalized = str(period or 'daily').strip().lower()
        if normalized not in self.VALID_PERIODS:
            raise ValueError(f"Unsupported horoscope period: {period}")
        return normalized

    def get_horoscope(self, zodiac_sign: str, period: str = 'daily', date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()

        sign = self._normalize_sign(zodiac_sign)
        normalized_period = self._normalize_period(period)

        horoscope = self.western_generator.generate_comprehensive_horoscope(
            sign, normalized_period, date
        )

        return {
            'zodiac_sign': sign,
            'date': date.strftime('%Y-%m-%d'),
            'period': normalized_period,
            'calculation_system': 'western_tropical_ephemeris',
            'astronomical_accuracy': True,
            **horoscope
        }
    
    def get_daily_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        return self.get_horoscope(zodiac_sign, 'daily', date)
    
    def get_weekly_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        return self.get_horoscope(zodiac_sign, 'weekly', date)
    
    def get_monthly_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        return self.get_horoscope(zodiac_sign, 'monthly', date)
    
    def get_yearly_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        return self.get_horoscope(zodiac_sign, 'yearly', date)
