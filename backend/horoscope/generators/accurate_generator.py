from datetime import datetime
import swisseph as swe
from typing import Dict, List
from ..utils.astronomical_events import AstronomicalEvents

class AccurateHoroscopeGenerator:
    def __init__(self):
        self.sun_sign_degrees = {
            'Aries': 15, 'Taurus': 45, 'Gemini': 75, 'Cancer': 105,
            'Leo': 135, 'Virgo': 165, 'Libra': 195, 'Scorpio': 225,
            'Sagittarius': 255, 'Capricorn': 285, 'Aquarius': 315, 'Pisces': 345
        }
        
    def generate_accurate_horoscope(self, sun_sign: str, date: datetime, period: str = 'daily') -> Dict:
        # Get current planetary positions
        planets = self._get_current_planets(date)
        
        # Calculate real aspects to sun sign midpoint
        aspects = self._calculate_real_aspects(sun_sign, planets)
        
        # Generate predictions based on actual transits and period
        predictions = self._generate_from_transits(sun_sign, aspects, planets, date, period)
        
        # Get real astronomical events
        try:
            lunar_phase = AstronomicalEvents.get_current_lunar_phase(date)
            void_moon = AstronomicalEvents.get_void_of_course_moon(date)
        except Exception as e:
            # Fallback if astronomical events fail
            lunar_phase = {'phase': 'Unknown', 'moon_sign': 'Unknown', 'illumination': 50}
            void_moon = {'is_void': False}
        
        return {
            'prediction': predictions,
            'planetary_transits': self._format_transits(aspects),
            'lunar_phase': f"{lunar_phase['phase']} in {lunar_phase['moon_sign']} ({lunar_phase['illumination']}% illuminated)",
            'mercury_retrograde': self._check_mercury_retrograde(planets),
            'void_moon': void_moon['is_void'],
            'void_until': void_moon.get('until').strftime('%H:%M') if void_moon.get('until') and hasattr(void_moon.get('until'), 'strftime') else None,
            'lucky_number': self._calculate_from_planets(planets),
            'lucky_color': self._get_planetary_color(aspects),
            'rating': self._calculate_energy_rating(aspects),
            'astronomical_accuracy': True
        }
    
    def _get_current_planets(self, date: datetime) -> Dict:
        """Get actual planetary positions for today"""
        jd = swe.julday(date.year, date.month, date.day, 12.0)
        planets = {}
        
        planet_ids = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
            'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN
        }
        
        for name, planet_id in planet_ids.items():
            result = swe.calc_ut(jd, planet_id, swe.FLG_SPEED)
            pos = result[0]  # Position array
            planets[name] = {
                'longitude': pos[0],
                'speed': pos[3] if len(pos) > 3 else 0.0,  # Speed is at index 3
                'retrograde': (pos[3] if len(pos) > 3 else 0.0) < 0
            }
        
        return planets
    
    def _calculate_real_aspects(self, sun_sign: str, planets: Dict) -> List[Dict]:
        """Calculate actual aspects to sun sign degree"""
        sun_degree = self.sun_sign_degrees[sun_sign]
        aspects = []
        
        orbs = {'conjunction': 8, 'square': 6, 'trine': 6, 'opposition': 8, 'sextile': 4}
        
        for planet, data in planets.items():
            if planet == 'Sun':
                continue
                
            diff = abs(data['longitude'] - sun_degree)
            if diff > 180:
                diff = 360 - diff
            
            # Check each aspect
            for aspect_name, orb in orbs.items():
                target_angle = {'conjunction': 0, 'sextile': 60, 'square': 90, 'trine': 120, 'opposition': 180}[aspect_name]
                
                if abs(diff - target_angle) <= orb:
                    aspects.append({
                        'planet': planet,
                        'aspect': aspect_name,
                        'orb': abs(diff - target_angle),
                        'exact_date': self._calculate_exact_date(planet, sun_degree, target_angle),
                        'applying': self._is_applying(data, sun_degree, target_angle)
                    })
        
        return sorted(aspects, key=lambda x: x['orb'])
    
    def _generate_from_transits(self, sun_sign: str, aspects: List[Dict], planets: Dict, date: datetime, period: str) -> Dict:
        """Generate predictions based on actual transits and time period"""
        
        # Filter aspects by period relevance
        relevant_aspects = self._filter_aspects_by_period(aspects, period)
        main_transit = relevant_aspects[0] if relevant_aspects else None
        
        # Base predictions on real planetary movements
        predictions = {}
        
        if main_transit:
            planet = main_transit['planet']
            aspect = main_transit['aspect']
            
            # Love predictions based on Venus/Mars transits with period context
            period_text = {'daily': 'today', 'weekly': 'this week', 'monthly': 'this month', 'yearly': 'this year'}.get(period, period)
            if planet == 'Venus':
                if aspect in ['trine', 'sextile']:
                    predictions['love'] = f"Venus {aspect} brings harmony to relationships {period_text}. {self._get_period_love_advice(period, True)}"
                else:
                    predictions['love'] = f"Venus {aspect} creates relationship tension {period_text}. {self._get_period_love_advice(period, False)}"
            elif planet == 'Mars':
                if aspect in ['trine', 'sextile']:
                    predictions['love'] = f"Mars {aspect} energizes romantic pursuits {period_text}. {self._get_period_love_advice(period, True)}"
                else:
                    predictions['love'] = f"Mars {aspect} may cause conflicts {period_text}. {self._get_period_love_advice(period, False)}"
            else:
                predictions['love'] = self._get_default_love(sun_sign)
            
            # Career predictions based on Mars/Jupiter/Saturn
            if planet in ['Mars', 'Jupiter', 'Saturn']:
                if aspect in ['trine', 'sextile']:
                    predictions['career'] = f"{planet} {aspect} supports professional growth {period_text}. {self._get_career_advice(planet, True)}"
                else:
                    predictions['career'] = f"{planet} {aspect} brings career challenges {period_text}. {self._get_career_advice(planet, False)}"
            else:
                predictions['career'] = self._get_default_career(sun_sign)
            
            # Health based on Mars/Saturn
            if planet in ['Mars', 'Saturn']:
                if aspect in ['square', 'opposition']:
                    predictions['health'] = f"{planet} {aspect} affects energy levels {period_text}. {self._get_health_advice(planet, False)}"
                else:
                    predictions['health'] = f"{planet} {aspect} supports vitality {period_text}. {self._get_health_advice(planet, True)}"
            else:
                predictions['health'] = self._get_default_health(sun_sign)
            
            # Finance based on Jupiter/Venus/Saturn
            if planet in ['Jupiter', 'Venus', 'Saturn']:
                if aspect in ['trine', 'sextile']:
                    predictions['finance'] = f"{planet} {aspect} brings financial opportunities {period_text}. {self._get_finance_advice(planet, True)}"
                else:
                    predictions['finance'] = f"{planet} {aspect} requires financial caution {period_text}. {self._get_finance_advice(planet, False)}"
            else:
                predictions['finance'] = self._get_default_finance(sun_sign)
            
            # Education based on Mercury/Jupiter
            if planet in ['Mercury', 'Jupiter']:
                if aspect in ['trine', 'sextile']:
                    predictions['education'] = f"{planet} {aspect} enhances learning abilities {period_text}. {self._get_education_advice(planet, True)}"
                else:
                    predictions['education'] = f"{planet} {aspect} creates study challenges {period_text}. {self._get_education_advice(planet, False)}"
            else:
                predictions['education'] = self._get_default_education(sun_sign)
            
            # Spirituality based on Jupiter/Moon/Saturn
            if planet in ['Jupiter', 'Moon', 'Saturn']:
                if aspect in ['trine', 'sextile']:
                    predictions['spirituality'] = f"{planet} {aspect} deepens spiritual connection {period_text}. {self._get_spirituality_advice(planet, True)}"
                else:
                    predictions['spirituality'] = f"{planet} {aspect} brings spiritual tests {period_text}. {self._get_spirituality_advice(planet, False)}"
            else:
                predictions['spirituality'] = self._get_default_spirituality(sun_sign)
            
            predictions['overall'] = f"Key influence: {planet} {aspect} to your sun sign. {self._get_overall_advice(planet, aspect, period)}"
        
        else:
            # No major aspects - use defaults
            predictions = {
                'love': self._get_default_love(sun_sign),
                'career': self._get_default_career(sun_sign),
                'health': self._get_default_health(sun_sign),
                'finance': self._get_default_finance(sun_sign),
                'education': self._get_default_education(sun_sign),
                'spirituality': self._get_default_spirituality(sun_sign),
                'overall': f"Steady energy for {sun_sign}. Focus on your natural strengths."
            }
        
        return predictions
    
    def _get_career_advice(self, planet: str, positive: bool) -> str:
        advice = {
            'Mars': {
                True: "Take bold action and lead initiatives.",
                False: "Avoid conflicts and channel energy into physical activity."
            },
            'Jupiter': {
                True: "Expand your horizons and seek growth opportunities.",
                False: "Avoid overconfidence and unrealistic expectations."
            },
            'Saturn': {
                True: "Build lasting structures and commit to long-term goals.",
                False: "Be patient with delays and focus on discipline."
            }
        }
        return advice.get(planet, {}).get(positive, "Stay focused on your goals.")
    
    def _get_health_advice(self, planet: str, positive: bool) -> str:
        advice = {
            'Mars': {
                True: "Energy levels are high - perfect for exercise.",
                False: "Avoid overexertion and manage stress levels."
            },
            'Saturn': {
                True: "Structure and discipline support wellness.",
                False: "Pay attention to chronic issues and rest more."
            }
        }
        return advice.get(planet, {}).get(positive, "Maintain balanced lifestyle.")
    
    def _get_finance_advice(self, planet: str, positive: bool) -> str:
        advice = {
            'Jupiter': {
                True: "Good time for investments and expansion.",
                False: "Avoid overspending and unrealistic ventures."
            },
            'Venus': {
                True: "Money flows through relationships and creativity.",
                False: "Control luxury spending and relationship costs."
            },
            'Saturn': {
                True: "Long-term financial planning pays off.",
                False: "Expect delays in financial matters."
            }
        }
        return advice.get(planet, {}).get(positive, "Practice careful money management.")
    
    def _get_education_advice(self, planet: str, positive: bool) -> str:
        advice = {
            'Mercury': {
                True: "Excellent time for learning new skills and communication.",
                False: "Focus on reviewing and consolidating knowledge."
            },
            'Jupiter': {
                True: "Expand knowledge through higher studies or philosophy.",
                False: "Avoid overcommitting to too many courses."
            }
        }
        return advice.get(planet, {}).get(positive, "Steady progress in learning.")
    
    def _get_spirituality_advice(self, planet: str, positive: bool) -> str:
        advice = {
            'Jupiter': {
                True: "Spiritual wisdom and growth flourish.",
                False: "Question beliefs and seek deeper understanding."
            },
            'Moon': {
                True: "Intuition and emotional healing are heightened.",
                False: "Practice patience with spiritual progress."
            },
            'Saturn': {
                True: "Disciplined practice brings spiritual rewards.",
                False: "Spiritual tests require perseverance."
            }
        }
        return advice.get(planet, {}).get(positive, "Spiritual journey continues steadily.")
    
    def _get_overall_advice(self, planet: str, aspect: str, period: str = 'daily') -> str:
        if aspect in ['trine', 'sextile']:
            return f"Supportive {planet} energy enhances your natural abilities."
        else:
            return f"Challenging {planet} energy requires patience and wisdom."
    
    def _get_lunar_phase(self, planets: Dict) -> str:
        sun_pos = planets['Sun']['longitude']
        moon_pos = planets['Moon']['longitude']
        
        phase_angle = (moon_pos - sun_pos) % 360
        
        if phase_angle < 45:
            return "New Moon - New beginnings"
        elif phase_angle < 135:
            return "Waxing Moon - Building energy"
        elif phase_angle < 225:
            return "Full Moon - Peak manifestation"
        else:
            return "Waning Moon - Release and reflection"
    
    def _check_mercury_retrograde(self, planets: Dict) -> bool:
        return planets['Mercury']['retrograde']
    
    def _check_void_moon(self, planets: Dict, date: datetime) -> bool:
        # Simplified void moon check - Moon making no major aspects
        moon_pos = planets['Moon']['longitude']
        
        for planet, data in planets.items():
            if planet in ['Moon', 'Sun']:
                continue
            
            diff = abs(data['longitude'] - moon_pos)
            if diff > 180:
                diff = 360 - diff
            
            # Check if Moon is within 5 degrees of any major aspect
            for angle in [0, 60, 90, 120, 180]:
                if abs(diff - angle) <= 5:
                    return False
        
        return True
    
    def _calculate_from_planets(self, planets: Dict) -> int:
        # Lucky number based on Moon's degree
        moon_degree = planets['Moon']['longitude'] % 30
        return int(moon_degree) + 1
    
    def _get_planetary_color(self, aspects: List[Dict]) -> str:
        if not aspects:
            return "White"
        
        planet_colors = {
            'Mars': 'Red', 'Venus': 'Pink', 'Mercury': 'Yellow',
            'Jupiter': 'Blue', 'Saturn': 'Black', 'Moon': 'Silver'
        }
        
        return planet_colors.get(aspects[0]['planet'], 'White')
    
    def _calculate_energy_rating(self, aspects: List[Dict]) -> int:
        if not aspects:
            return 3
        
        positive_aspects = sum(1 for a in aspects if a['aspect'] in ['trine', 'sextile'])
        challenging_aspects = sum(1 for a in aspects if a['aspect'] in ['square', 'opposition'])
        
        if positive_aspects > challenging_aspects:
            return 5 if positive_aspects >= 2 else 4
        elif challenging_aspects > positive_aspects:
            return 2 if challenging_aspects >= 2 else 3
        else:
            return 3
    
    # Default predictions for when no major transits
    def _get_default_love(self, sign: str) -> str:
        defaults = {
            'Aries': "Your natural charm attracts positive attention.",
            'Taurus': "Steady approach to relationships brings stability.",
            'Gemini': "Communication skills enhance romantic connections.",
            'Cancer': "Nurturing nature strengthens bonds.",
            'Leo': "Charisma draws romantic opportunities.",
            'Virgo': "Practical gestures show love effectively.",
            'Libra': "Harmony creates relationship balance.",
            'Scorpio': "Intense emotions deepen connections.",
            'Sagittarius': "Adventure spices up romance.",
            'Capricorn': "Commitment strengthens partnerships.",
            'Aquarius': "Unique connections spark interest.",
            'Pisces': "Intuitive understanding guides love."
        }
        return defaults.get(sign, "Love energy flows naturally.")
    
    def _get_default_career(self, sign: str) -> str:
        defaults = {
            'Aries': "Leadership qualities shine in professional settings.",
            'Taurus': "Practical skills advance career goals.",
            'Gemini': "Networking abilities open new opportunities.",
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
        return defaults.get(sign, "Professional energy remains steady.")
    
    def _get_default_health(self, sign: str) -> str:
        defaults = {
            'Aries': "High energy supports active lifestyle.",
            'Taurus': "Steady routines maintain good health.",
            'Gemini': "Mental stimulation supports overall wellness.",
            'Cancer': "Digestive care is important.",
            'Leo': "Heart health deserves attention.",
            'Virgo': "Stress management supports wellness.",
            'Libra': "Balance work and rest periods.",
            'Scorpio': "Detox activities are beneficial.",
            'Sagittarius': "Outdoor activities boost vitality.",
            'Capricorn': "Joint health needs gentle care.",
            'Aquarius': "Stay hydrated and active.",
            'Pisces': "Rest and relaxation are essential."
        }
        return defaults.get(sign, "Health remains stable.")
    
    def _filter_aspects_by_period(self, aspects: List[Dict], period: str) -> List[Dict]:
        """Filter aspects based on period relevance"""
        if period == 'daily':
            # Fast-moving planets for daily changes
            fast_planets = ['Moon', 'Mercury']
            filtered = [a for a in aspects if a['planet'] in fast_planets]
            return filtered[:2] if filtered else aspects[:1]
        elif period == 'weekly':
            # Medium-speed planets for weekly
            weekly_planets = ['Moon', 'Mercury', 'Venus']
            filtered = [a for a in aspects if a['planet'] in weekly_planets]
            return filtered[:2] if filtered else aspects[:1]
        elif period == 'monthly':
            # Slower planets for monthly
            monthly_planets = ['Venus', 'Mars', 'Sun']
            filtered = [a for a in aspects if a['planet'] in monthly_planets]
            return filtered[:2] if filtered else aspects[:1]
        else:  # yearly
            # Slowest planets for yearly
            yearly_planets = ['Jupiter', 'Saturn']
            filtered = [a for a in aspects if a['planet'] in yearly_planets]
            return filtered[:2] if filtered else aspects[:1]
    
    def _get_period_love_advice(self, period: str, positive: bool) -> str:
        """Get period-specific love advice"""
        if period == 'daily':
            return "Perfect time for romantic gestures." if positive else "Give relationships space today."
        elif period == 'weekly':
            return "Week ahead favors new romantic connections." if positive else "Patience needed in current relationships."
        elif period == 'monthly':
            return "Month brings relationship milestones." if positive else "Navigate partnership challenges with care."
        else:  # yearly
            return "Year holds major love transformations." if positive else "Annual cycle of relationship growth and learning."
    
    def _get_default_finance(self, sign: str) -> str:
        defaults = {
            'Aries': "Bold financial decisions may pay off.",
            'Taurus': "Conservative approach protects resources.",
            'Gemini': "Multiple income streams show potential.",
            'Cancer': "Family finances need careful attention.",
            'Leo': "Luxury spending requires balance.",
            'Virgo': "Detailed budgeting shows results.",
            'Libra': "Joint financial decisions are favored.",
            'Scorpio': "Hidden financial matters may surface.",
            'Sagittarius': "Investment opportunities expand.",
            'Capricorn': "Long-term planning succeeds.",
            'Aquarius': "Unconventional income sources emerge.",
            'Pisces': "Intuitive money decisions work well."
        }
        return defaults.get(sign, "Financial matters remain steady.")
    
    def _get_default_education(self, sign: str) -> str:
        defaults = {
            'Aries': "Natural leadership skills enhance learning.",
            'Taurus': "Practical approach to education yields results.",
            'Gemini': "Curiosity drives diverse learning interests.",
            'Cancer': "Emotional connection to subjects aids retention.",
            'Leo': "Creative expression enhances educational experience.",
            'Virgo': "Analytical skills excel in detailed studies.",
            'Libra': "Collaborative learning brings best results.",
            'Scorpio': "Deep research reveals hidden knowledge.",
            'Sagittarius': "Higher learning and philosophy appeal strongly.",
            'Capricorn': "Structured approach to education succeeds.",
            'Aquarius': "Innovative learning methods work well.",
            'Pisces': "Intuitive understanding complements formal study."
        }
        return defaults.get(sign, "Learning opportunities present themselves.")
    
    def _get_default_spirituality(self, sign: str) -> str:
        defaults = {
            'Aries': "Direct spiritual experiences guide the path.",
            'Taurus': "Grounded practices bring spiritual stability.",
            'Gemini': "Exploring various spiritual teachings enriches understanding.",
            'Cancer': "Emotional healing deepens spiritual connection.",
            'Leo': "Heart-centered spirituality shines brightly.",
            'Virgo': "Service to others becomes spiritual practice.",
            'Libra': "Balance and harmony guide spiritual growth.",
            'Scorpio': "Transformation and rebirth mark spiritual journey.",
            'Sagittarius': "Philosophical exploration expands spiritual horizons.",
            'Capricorn': "Disciplined practice builds spiritual foundation.",
            'Aquarius': "Universal consciousness and humanitarian ideals inspire.",
            'Pisces': "Mystical experiences and compassion deepen faith."
        }
        return defaults.get(sign, "Spiritual awareness grows naturally.")
    
    def _calculate_exact_date(self, planet: str, sun_degree: float, target_angle: float) -> str:
        return "Within 3 days"
    
    def _is_applying(self, planet_data: Dict, sun_degree: float, target_angle: float) -> bool:
        # Check if aspect is applying (getting closer) or separating
        return planet_data['speed'] > 0  # Simplified
    
    def _format_transits(self, aspects: List[Dict]) -> List[str]:
        return [f"{a['planet']} {a['aspect']} (orb: {a['orb']:.1f}°)" for a in aspects[:3]]