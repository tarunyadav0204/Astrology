from datetime import datetime
from typing import Dict
import random

class DailyHoroscopeGenerator:
    def generate(self, zodiac_sign: str, planetary_data: Dict, date: datetime) -> Dict:
        return {
            'prediction': {
                'love': self._get_love_prediction(zodiac_sign),
                'career': self._get_career_prediction(zodiac_sign),
                'health': self._get_health_prediction(zodiac_sign),
                'finance': self._get_finance_prediction(zodiac_sign),
                'overall': self._get_overall_prediction(zodiac_sign)
            },
            'lucky_number': random.randint(1, 50),
            'lucky_color': random.choice(['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange']),
            'rating': random.randint(3, 5)
        }
    
    def _get_love_prediction(self, sign: str) -> str:
        predictions = {
            'Aries': "Venus brings romantic opportunities today.",
            'Taurus': "Stable relationships flourish with gentle care.",
            'Gemini': "Communication deepens romantic connections.",
            'Cancer': "Family harmony supports love life.",
            'Leo': "Your charisma attracts romantic attention.",
            'Virgo': "Practical gestures show love effectively.",
            'Libra': "Balance creates relationship harmony.",
            'Scorpio': "Intense emotions deepen intimacy.",
            'Sagittarius': "Adventure spices up romance.",
            'Capricorn': "Commitment strengthens partnerships.",
            'Aquarius': "Unique connections spark interest.",
            'Pisces': "Intuitive understanding guides love."
        }
        return predictions.get(sign, "Love energy flows positively.")
    
    def _get_career_prediction(self, sign: str) -> str:
        predictions = {
            'Aries': "Leadership opportunities emerge today.",
            'Taurus': "Steady progress in work projects.",
            'Gemini': "Communication skills open doors.",
            'Cancer': "Team collaboration brings success.",
            'Leo': "Creative talents gain recognition.",
            'Virgo': "Detail-oriented work pays off.",
            'Libra': "Diplomatic approach advances goals.",
            'Scorpio': "Research reveals important insights.",
            'Sagittarius': "Learning opportunities expand horizons.",
            'Capricorn': "Authority and responsibility increase.",
            'Aquarius': "Innovation leads to breakthroughs.",
            'Pisces': "Intuitive decisions guide success."
        }
        return predictions.get(sign, "Professional growth is highlighted.")
    
    def _get_health_prediction(self, sign: str) -> str:
        predictions = {
            'Aries': "High energy supports active lifestyle.",
            'Taurus': "Focus on throat and neck wellness.",
            'Gemini': "Breathing exercises benefit health.",
            'Cancer': "Digestive care is important today.",
            'Leo': "Heart health deserves attention.",
            'Virgo': "Stress management supports wellness.",
            'Libra': "Balance work and rest periods.",
            'Scorpio': "Detox activities are beneficial.",
            'Sagittarius': "Outdoor activities boost vitality.",
            'Capricorn': "Joint health needs gentle care.",
            'Aquarius': "Stay hydrated and active.",
            'Pisces': "Rest and relaxation are essential."
        }
        return predictions.get(sign, "Health trends are positive today.")
    
    def _get_finance_prediction(self, sign: str) -> str:
        predictions = {
            'Aries': "Control impulsive spending today.",
            'Taurus': "Steady financial growth continues.",
            'Gemini': "Multiple income opportunities arise.",
            'Cancer': "Family finances need attention.",
            'Leo': "Balance luxury with responsibility.",
            'Virgo': "Detailed budgeting shows results.",
            'Libra': "Joint financial decisions are favored.",
            'Scorpio': "Hidden financial matters surface.",
            'Sagittarius': "Investment opportunities expand.",
            'Capricorn': "Long-term planning succeeds.",
            'Aquarius': "Unconventional income sources emerge.",
            'Pisces': "Intuitive money decisions work well."
        }
        return predictions.get(sign, "Financial stability improves.")
    
    def _get_overall_prediction(self, sign: str) -> str:
        predictions = {
            'Aries': "Dynamic energy propels you forward.",
            'Taurus': "Steady progress in all areas.",
            'Gemini': "Communication opens opportunities.",
            'Cancer': "Emotional security guides decisions.",
            'Leo': "Creative expression shines brightly.",
            'Virgo': "Practical skills bring rewards.",
            'Libra': "Harmony guides your path.",
            'Scorpio': "Transformation brings growth.",
            'Sagittarius': "Adventure calls to you.",
            'Capricorn': "Achievement is within reach.",
            'Aquarius': "Innovation brings success.",
            'Pisces': "Intuition guides your journey."
        }
        return predictions.get(sign, "Positive energy surrounds you.")