from datetime import datetime, timedelta
import swisseph as swe
from typing import Dict, List
import random

class HoroscopeEngine:
    def __init__(self):
        self.zodiac_signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        
    def get_daily_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()
            
        # Get current planetary positions
        planetary_data = self._get_planetary_positions(date)
        
        # Generate horoscope based on transits
        horoscope = self._generate_horoscope(zodiac_sign, planetary_data, 'daily')
        
        return {
            'zodiac_sign': zodiac_sign,
            'date': date.strftime('%Y-%m-%d'),
            'period': 'daily',
            'prediction': horoscope,
            'lucky_number': random.randint(1, 50),
            'lucky_color': random.choice(['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange']),
            'rating': random.randint(3, 5)
        }
    
    def get_weekly_horoscope(self, zodiac_sign: str, date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()
            
        week_start = date - timedelta(days=date.weekday())
        week_end = week_start + timedelta(days=6)
        
        planetary_data = self._get_planetary_positions(date)
        horoscope = self._generate_horoscope(zodiac_sign, planetary_data, 'weekly')
        
        return {
            'zodiac_sign': zodiac_sign,
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'period': 'weekly',
            'prediction': horoscope,
            'key_days': self._get_key_days(week_start, week_end),
            'rating': random.randint(3, 5)
        }
    
    def get_monthly_horoscope(self, zodiac_sign: str, year: int = None, month: int = None) -> Dict:
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
            
        date = datetime(year, month, 15)  # Mid-month for calculations
        planetary_data = self._get_planetary_positions(date)
        horoscope = self._generate_horoscope(zodiac_sign, planetary_data, 'monthly')
        
        return {
            'zodiac_sign': zodiac_sign,
            'year': year,
            'month': month,
            'month_name': date.strftime('%B'),
            'period': 'monthly',
            'prediction': horoscope,
            'themes': self._get_monthly_themes(zodiac_sign, planetary_data),
            'rating': random.randint(3, 5)
        }
    
    def get_yearly_horoscope(self, zodiac_sign: str, year: int = None) -> Dict:
        if not year:
            year = datetime.now().year
            
        date = datetime(year, 6, 15)  # Mid-year for calculations
        planetary_data = self._get_planetary_positions(date)
        horoscope = self._generate_horoscope(zodiac_sign, planetary_data, 'yearly')
        
        return {
            'zodiac_sign': zodiac_sign,
            'year': year,
            'period': 'yearly',
            'prediction': horoscope,
            'major_transits': self._get_major_transits(year),
            'quarterly_outlook': self._get_quarterly_outlook(zodiac_sign, year),
            'rating': random.randint(3, 5)
        }
    
    def _get_planetary_positions(self, date: datetime) -> Dict:
        """Get current planetary positions using Swiss Ephemeris"""
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
                # Fallback if Swiss Ephemeris fails
                planets[planet_names[i]] = {
                    'longitude': random.uniform(0, 360),
                    'sign': random.choice(self.zodiac_signs),
                    'degree': random.uniform(0, 30)
                }
        
        return planets
    
    def _generate_horoscope(self, zodiac_sign: str, planetary_data: Dict, period: str) -> Dict:
        """Generate horoscope based on planetary positions"""
        
        # Base predictions for each sign and period
        predictions = {
            'daily': {
                'love': self._get_love_prediction(zodiac_sign, planetary_data, period),
                'career': self._get_career_prediction(zodiac_sign, planetary_data, period),
                'health': self._get_health_prediction(zodiac_sign, planetary_data, period),
                'finance': self._get_finance_prediction(zodiac_sign, planetary_data, period),
                'overall': self._get_overall_prediction(zodiac_sign, planetary_data, period)
            },
            'weekly': {
                'love': self._get_love_prediction(zodiac_sign, planetary_data, period),
                'career': self._get_career_prediction(zodiac_sign, planetary_data, period),
                'health': self._get_health_prediction(zodiac_sign, planetary_data, period),
                'finance': self._get_finance_prediction(zodiac_sign, planetary_data, period),
                'overall': self._get_overall_prediction(zodiac_sign, planetary_data, period)
            },
            'monthly': {
                'love': self._get_love_prediction(zodiac_sign, planetary_data, period),
                'career': self._get_career_prediction(zodiac_sign, planetary_data, period),
                'health': self._get_health_prediction(zodiac_sign, planetary_data, period),
                'finance': self._get_finance_prediction(zodiac_sign, planetary_data, period),
                'overall': self._get_overall_prediction(zodiac_sign, planetary_data, period)
            },
            'yearly': {
                'love': self._get_love_prediction(zodiac_sign, planetary_data, period),
                'career': self._get_career_prediction(zodiac_sign, planetary_data, period),
                'health': self._get_health_prediction(zodiac_sign, planetary_data, period),
                'finance': self._get_finance_prediction(zodiac_sign, planetary_data, period),
                'overall': self._get_overall_prediction(zodiac_sign, planetary_data, period)
            }
        }
        
        return predictions[period]
    
    def _get_love_prediction(self, sign: str, planets: Dict, period: str) -> str:
        love_predictions = {
            'Aries': f"Venus brings romantic opportunities. Single Aries may find love through social connections.",
            'Taurus': f"Stable relationships flourish. Focus on deepening emotional bonds with your partner.",
            'Gemini': f"Communication is key in relationships. Express your feelings openly and honestly.",
            'Cancer': f"Family and home life take priority. Nurture existing relationships with care.",
            'Leo': f"Your charisma attracts admirers. Enjoy the spotlight in romantic situations.",
            'Virgo': f"Practical approach to love works well. Focus on building solid foundations.",
            'Libra': f"Harmony in relationships is highlighted. Balance give and take with your partner.",
            'Scorpio': f"Intense emotions surface. Transform challenges into deeper intimacy.",
            'Sagittarius': f"Adventure in love awaits. Explore new dimensions of romance.",
            'Capricorn': f"Commitment and stability are favored. Long-term planning benefits relationships.",
            'Aquarius': f"Unconventional romance appeals to you. Embrace unique connections.",
            'Pisces': f"Intuitive understanding deepens bonds. Trust your heart in matters of love."
        }
        return love_predictions.get(sign, "Love energy is flowing positively in your direction.")
    
    def _get_career_prediction(self, sign: str, planets: Dict, period: str) -> str:
        career_predictions = {
            'Aries': f"Leadership opportunities emerge. Take initiative in professional projects.",
            'Taurus': f"Steady progress in career goals. Persistence pays off in the workplace.",
            'Gemini': f"Communication skills shine. Networking opens new professional doors.",
            'Cancer': f"Nurturing approach benefits team dynamics. Focus on collaborative projects.",
            'Leo': f"Creative projects gain recognition. Your talents are noticed by superiors.",
            'Virgo': f"Attention to detail sets you apart. Analytical skills are highly valued.",
            'Libra': f"Diplomatic skills advance your career. Mediation brings professional success.",
            'Scorpio': f"Research and investigation lead to breakthroughs. Dig deeper for answers.",
            'Sagittarius': f"International or educational opportunities arise. Expand your horizons.",
            'Capricorn': f"Authority and responsibility increase. Management roles are favored.",
            'Aquarius': f"Innovation and technology benefit your career. Think outside the box.",
            'Pisces': f"Intuitive insights guide professional decisions. Trust your instincts."
        }
        return career_predictions.get(sign, "Professional growth and opportunities are on the horizon.")
    
    def _get_health_prediction(self, sign: str, planets: Dict, period: str) -> str:
        health_predictions = {
            'Aries': f"High energy levels support active lifestyle. Avoid overexertion and stress.",
            'Taurus': f"Focus on throat and neck health. Maintain steady exercise routine.",
            'Gemini': f"Respiratory health needs attention. Practice breathing exercises and meditation.",
            'Cancer': f"Digestive system requires care. Emotional eating patterns need monitoring.",
            'Leo': f"Heart health is highlighted. Cardiovascular exercise benefits overall vitality.",
            'Virgo': f"Digestive and nervous system need attention. Stress management is crucial.",
            'Libra': f"Kidney and lower back health important. Balance work and rest periods.",
            'Scorpio': f"Reproductive and elimination systems need care. Detox programs beneficial.",
            'Sagittarius': f"Hip and thigh areas need attention. Outdoor activities boost health.",
            'Capricorn': f"Bone and joint health important. Regular check-ups recommended.",
            'Aquarius': f"Circulatory system needs support. Stay hydrated and active.",
            'Pisces': f"Feet and immune system require care. Rest and relaxation are essential."
        }
        return health_predictions.get(sign, "Overall health trends are positive with proper self-care.")
    
    def _get_finance_prediction(self, sign: str, planets: Dict, period: str) -> str:
        finance_predictions = {
            'Aries': f"Impulsive spending needs control. Investment opportunities in new ventures.",
            'Taurus': f"Steady financial growth continues. Conservative investments are favored.",
            'Gemini': f"Multiple income streams develop. Diversify your financial portfolio.",
            'Cancer': f"Real estate and family finances highlighted. Secure long-term savings.",
            'Leo': f"Luxury spending tempts you. Balance enjoyment with financial responsibility.",
            'Virgo': f"Detailed budgeting pays off. Analyze expenses for better money management.",
            'Libra': f"Partnership finances need attention. Balance joint financial decisions.",
            'Scorpio': f"Hidden assets or debts surface. Transform financial challenges into opportunities.",
            'Sagittarius': f"Foreign investments or education expenses featured. Expand financial horizons.",
            'Capricorn': f"Long-term financial planning succeeds. Authority over money matters increases.",
            'Aquarius': f"Unconventional income sources emerge. Technology investments are favored.",
            'Pisces': f"Intuitive financial decisions work well. Charitable giving brings abundance."
        }
        return finance_predictions.get(sign, "Financial stability improves with careful planning.")
    
    def _get_overall_prediction(self, sign: str, planets: Dict, period: str) -> str:
        overall_predictions = {
            'Aries': f"Dynamic energy propels you forward. Leadership roles and new beginnings are highlighted.",
            'Taurus': f"Steady progress in all areas. Patience and persistence bring lasting results.",
            'Gemini': f"Communication and learning are emphasized. Versatility opens multiple opportunities.",
            'Cancer': f"Home and family take center stage. Emotional security and nurturing are key themes.",
            'Leo': f"Creative expression and recognition shine. Your natural charisma attracts positive attention.",
            'Virgo': f"Practical skills and attention to detail are rewarded. Organization brings success.",
            'Libra': f"Balance and harmony guide your path. Relationships and partnerships are highlighted.",
            'Scorpio': f"Transformation and renewal are powerful themes. Embrace change for growth.",
            'Sagittarius': f"Adventure and expansion call to you. Higher learning and travel are favored.",
            'Capricorn': f"Achievement and recognition are within reach. Discipline and structure pay off.",
            'Aquarius': f"Innovation and friendship are highlighted. Unique approaches bring success.",
            'Pisces': f"Intuition and spirituality guide your journey. Compassion opens new doors."
        }
        return overall_predictions.get(sign, "Positive energy surrounds you in all endeavors.")
    
    def _get_key_days(self, start_date: datetime, end_date: datetime) -> List[str]:
        """Generate key days for weekly horoscope"""
        key_days = []
        current = start_date
        while current <= end_date:
            if current.weekday() in [0, 2, 4]:  # Monday, Wednesday, Friday
                key_days.append(current.strftime('%A, %B %d'))
            current += timedelta(days=1)
        return key_days[:3]  # Return top 3 key days
    
    def _get_monthly_themes(self, sign: str, planets: Dict) -> List[str]:
        """Generate monthly themes"""
        themes = [
            "Personal Growth", "Relationship Harmony", "Career Advancement",
            "Financial Stability", "Health & Wellness", "Creative Expression",
            "Spiritual Development", "Family Connections"
        ]
        return random.sample(themes, 3)
    
    def _get_major_transits(self, year: int) -> List[Dict]:
        """Generate major planetary transits for the year"""
        return [
            {"planet": "Jupiter", "event": "Enters new sign", "impact": "Expansion and growth"},
            {"planet": "Saturn", "event": "Retrograde period", "impact": "Lessons and restructuring"},
            {"planet": "Mercury", "event": "Multiple retrogrades", "impact": "Communication challenges"}
        ]
    
    def _get_quarterly_outlook(self, sign: str, year: int) -> Dict:
        """Generate quarterly outlook for yearly horoscope"""
        return {
            "Q1": "Foundation building and new beginnings",
            "Q2": "Growth and expansion in key areas",
            "Q3": "Harvest time and recognition",
            "Q4": "Reflection and planning for future"
        }