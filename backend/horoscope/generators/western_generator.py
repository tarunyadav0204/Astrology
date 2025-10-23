from datetime import datetime, timedelta
import swisseph as swe
from typing import Dict, List, Tuple
import math

class WesternHoroscopeGenerator:
    def __init__(self):
        self.zodiac_signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        
        # Traditional planetary rulers
        self.traditional_rulers = {
            'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury',
            'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury',
            'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter',
            'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
        }
        
        # Sun sign date ranges (approximate midpoints)
        self.sun_sign_degrees = {
            'Aries': 15, 'Taurus': 45, 'Gemini': 75, 'Cancer': 105,
            'Leo': 135, 'Virgo': 165, 'Libra': 195, 'Scorpio': 225,
            'Sagittarius': 255, 'Capricorn': 285, 'Aquarius': 315, 'Pisces': 345
        }

    def generate_comprehensive_horoscope(self, zodiac_sign: str, period: str, date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()
            
        # Calculate tropical planetary positions
        planetary_data = self._calculate_tropical_positions(date)
        
        # Generate universal influences
        universal_influences = self._generate_universal_influences(planetary_data)
        
        # Calculate aspects to sun sign
        aspects = self._calculate_aspects_to_sun_sign(zodiac_sign, planetary_data)
        self._store_aspects_for_timing(aspects)
        
        # Generate period-specific predictions
        predictions = self._generate_predictions_from_aspects(zodiac_sign, aspects, period, planetary_data, date)
        
        return {
            'prediction': predictions,
            'todays_energy': self._calculate_todays_energy(planetary_data, date) if period == 'daily' else None,
            'best_time': self._calculate_best_time(zodiac_sign, date) if period == 'daily' else None,
            'key_focus': self._calculate_key_focus(zodiac_sign, aspects, date) if period == 'daily' else None,
            'what_to_avoid': self._calculate_what_to_avoid(zodiac_sign, aspects, date) if period == 'daily' else None,
            'lucky_element': self._calculate_lucky_element(zodiac_sign, aspects, date) if period == 'daily' else None,
            'love_guidance': self._calculate_love_guidance(zodiac_sign, aspects, date) if period == 'daily' else None,
            'daily_actions': self._calculate_daily_actions(zodiac_sign, aspects, date) if period == 'daily' else None,
            'energy_forecast': self._calculate_energy_forecast(zodiac_sign, aspects, planetary_data, date) if period == 'daily' else None,
            'daily_summary': self._calculate_daily_summary(zodiac_sign, aspects, date) if period == 'daily' else None,
            'moon_timing': self._calculate_moon_timing(planetary_data, date) if period == 'daily' else None,
            'intuitive_insights': self._calculate_intuitive_insights(zodiac_sign, aspects, planetary_data, date) if period == 'daily' else None,
            'energy_focus': universal_influences['energy_focus'],
            'key_theme': universal_influences['key_theme'],
            'lunar_phase': universal_influences['lunar_phase'],
            'lucky_number': self._calculate_lucky_number(date),
            'lucky_color': self._calculate_lucky_color(zodiac_sign, aspects),
            'rating': self._calculate_rating(aspects),
            'cosmic_weather': self._calculate_cosmic_weather(aspects),
            'action_plan': self._calculate_personalized_action_plan(zodiac_sign, aspects, planetary_data, date)
        }

    def _calculate_tropical_positions(self, date: datetime) -> Dict:
        """Calculate tropical (Western) planetary positions"""
        jd = swe.julday(date.year, date.month, date.day, 12.0)
        positions = {}
        
        planets = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
            'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE,
            'Pluto': swe.PLUTO
        }
        
        for planet_name, planet_id in planets.items():
            try:
                # Use tropical zodiac (default - no sidereal flag)
                pos, _ = swe.calc_ut(jd, planet_id, swe.FLG_SPEED)
                longitude = pos[0]
                sign_num = int(longitude // 30)
                degree = longitude % 30
                
                positions[planet_name] = {
                    'longitude': longitude,
                    'sign': self.zodiac_signs[sign_num],
                    'degree': degree,
                    'speed': pos[3]
                }
            except Exception:
                # Fallback
                positions[planet_name] = {
                    'longitude': 0,
                    'sign': 'Aries',
                    'degree': 0,
                    'speed': 0
                }
        
        return positions

    def _calculate_aspects_to_sun_sign(self, sun_sign: str, planets: Dict) -> List[Dict]:
        """Calculate aspects from transiting planets to sun sign midpoint"""
        sun_sign_degree = self.sun_sign_degrees[sun_sign]
        aspects = []
        
        # Aspect orbs
        aspect_orbs = {
            'conjunction': 8, 'opposition': 8, 'square': 6,
            'trine': 6, 'sextile': 4
        }
        
        for planet_name, planet_data in planets.items():
            if planet_name == 'Sun':
                continue  # Skip sun aspecting itself
                
            planet_degree = planet_data['longitude']
            
            # Calculate angular difference
            diff = abs(planet_degree - sun_sign_degree)
            if diff > 180:
                diff = 360 - diff
            
            # Check for aspects
            aspect_type = None
            orb_used = 0
            
            if diff <= aspect_orbs['conjunction']:
                aspect_type = 'conjunction'
                orb_used = diff
            elif abs(diff - 60) <= aspect_orbs['sextile']:
                aspect_type = 'sextile'
                orb_used = abs(diff - 60)
            elif abs(diff - 90) <= aspect_orbs['square']:
                aspect_type = 'square'
                orb_used = abs(diff - 90)
            elif abs(diff - 120) <= aspect_orbs['trine']:
                aspect_type = 'trine'
                orb_used = abs(diff - 120)
            elif abs(diff - 180) <= aspect_orbs['opposition']:
                aspect_type = 'opposition'
                orb_used = abs(diff - 180)
            
            if aspect_type:
                aspects.append({
                    'planet': planet_name,
                    'aspect': aspect_type,
                    'orb': orb_used,
                    'strength': self._calculate_aspect_strength(aspect_type, orb_used, planet_name),
                    'nature': self._get_aspect_nature(aspect_type)
                })
        
        # Sort by strength (strongest first)
        aspects.sort(key=lambda x: x['strength'], reverse=True)
        return aspects

    def _calculate_aspect_strength(self, aspect_type: str, orb: float, planet: str) -> float:
        """Calculate aspect strength based on type, orb, and planet"""
        # Base strength by aspect type
        aspect_strength = {
            'conjunction': 10, 'opposition': 8, 'square': 7,
            'trine': 6, 'sextile': 4
        }
        
        # Planet strength multiplier
        planet_strength = {
            'Sun': 1.0, 'Moon': 0.9, 'Mercury': 0.7, 'Venus': 0.8,
            'Mars': 0.8, 'Jupiter': 0.9, 'Saturn': 0.8,
            'Uranus': 0.6, 'Neptune': 0.5, 'Pluto': 0.7
        }
        
        base = aspect_strength.get(aspect_type, 5)
        planet_mult = planet_strength.get(planet, 0.5)
        orb_reduction = (orb / 8) * 0.3  # Reduce strength for wider orbs
        
        return base * planet_mult * (1 - orb_reduction)

    def _get_aspect_nature(self, aspect_type: str) -> str:
        """Get aspect nature (harmonious/challenging)"""
        harmonious = ['conjunction', 'trine', 'sextile']
        challenging = ['square', 'opposition']
        
        if aspect_type in harmonious:
            return 'harmonious'
        elif aspect_type in challenging:
            return 'challenging'
        else:
            return 'neutral'

    def _generate_predictions_from_aspects(self, sun_sign: str, aspects: List[Dict], period: str, planets: Dict, date: datetime) -> Dict:
        """Generate predictions based on actual aspects"""
        
        # Get most significant aspects for the period
        significant_aspects = self._filter_aspects_by_period(aspects, period)
        
        return {
            'overall': self._generate_overall_from_aspects(sun_sign, significant_aspects, period),
            'love': self._calculate_love_guidance(sun_sign, aspects, date) if period == 'daily' else self._generate_love_from_aspects(sun_sign, significant_aspects, period),
            'career': self._calculate_career_guidance(sun_sign, aspects, date) if period == 'daily' else self._generate_career_from_aspects(sun_sign, significant_aspects, period),
            'health': self._calculate_health_guidance(sun_sign, aspects, date) if period == 'daily' else self._generate_health_from_aspects(sun_sign, significant_aspects, period),
            'finance': self._calculate_finance_guidance(sun_sign, aspects, date) if period == 'daily' else self._generate_finance_from_aspects(sun_sign, significant_aspects, period),
            'education': self._calculate_education_guidance(sun_sign, aspects, date) if period == 'daily' else self._generate_education_from_aspects(sun_sign, significant_aspects, period),
            'spirituality': self._calculate_spirituality_guidance(sun_sign, aspects, date) if period == 'daily' else self._generate_spirituality_from_aspects(sun_sign, significant_aspects, period),
            'detailed_analysis': self._format_detailed_analysis(aspects, planets)
        }

    def _filter_aspects_by_period(self, aspects: List[Dict], period: str) -> List[Dict]:
        """Filter aspects based on period relevance"""
        if period == 'daily':
            # Only Moon and Mercury for daily changes
            fast_planets = ['Moon', 'Mercury']
            filtered = [a for a in aspects if a['planet'] in fast_planets]
            return filtered[:2] if filtered else aspects[:1]
        elif period == 'weekly':
            # Moon, Mercury, Venus for weekly
            weekly_planets = ['Moon', 'Mercury', 'Venus']
            filtered = [a for a in aspects if a['planet'] in weekly_planets]
            return filtered[:2] if filtered else aspects[:1]
        elif period == 'monthly':
            # Venus, Mars for monthly
            monthly_planets = ['Venus', 'Mars', 'Sun']
            filtered = [a for a in aspects if a['planet'] in monthly_planets]
            return filtered[:2] if filtered else aspects[:1]
        else:  # yearly
            # Slower planets for yearly
            yearly_planets = ['Jupiter', 'Saturn', 'Mars']
            filtered = [a for a in aspects if a['planet'] in yearly_planets]
            return filtered[:2] if filtered else aspects[:1]

    def _calculate_lucky_number(self, date: datetime) -> int:
        """Calculate lucky number based on planetary day ruler"""
        weekday = date.weekday()  # 0=Monday, 6=Sunday
        
        # Traditional planetary day rulers and their numbers
        day_numbers = {
            6: [1, 10, 19, 28],  # Sunday (Sun)
            0: [2, 11, 20, 29],  # Monday (Moon)
            1: [9, 18, 27],      # Tuesday (Mars)
            2: [5, 14, 23],      # Wednesday (Mercury)
            3: [3, 12, 21, 30],  # Thursday (Jupiter)
            4: [6, 15, 24],      # Friday (Venus)
            5: [8, 17, 26]       # Saturday (Saturn)
        }
        
        # Return first number for the day
        return day_numbers[weekday][0]

    def _calculate_todays_energy(self, planets: Dict, date: datetime) -> str:
        """Calculate today's energy based on Moon sign, day ruler, and lunar phase"""
        moon_data = planets.get('Moon', {})
        sun_data = planets.get('Sun', {})
        
        # Moon sign energy
        moon_sign = moon_data.get('sign', 'Aries')
        moon_energies = {
            'Aries': 'dynamic and action-oriented',
            'Taurus': 'grounded and practical', 
            'Gemini': 'communicative and mentally active',
            'Cancer': 'emotional and nurturing',
            'Leo': 'creative and expressive',
            'Virgo': 'analytical and detail-focused',
            'Libra': 'harmonious and relationship-focused',
            'Scorpio': 'intense and transformative',
            'Sagittarius': 'optimistic and expansive',
            'Capricorn': 'structured and goal-oriented',
            'Aquarius': 'innovative and independent',
            'Pisces': 'intuitive and compassionate'
        }
        
        # Day ruler energy
        weekday = date.weekday()
        day_rulers = {
            0: ('Moon', 'reflective and emotionally sensitive'),
            1: ('Mars', 'energetic and action-focused'),
            2: ('Mercury', 'communicative and mentally sharp'),
            3: ('Jupiter', 'optimistic and growth-oriented'),
            4: ('Venus', 'harmonious and relationship-centered'),
            5: ('Saturn', 'disciplined and structured'),
            6: ('Sun', 'confident and leadership-focused')
        }
        
        # Lunar phase energy
        moon_longitude = moon_data.get('longitude', 0)
        sun_longitude = sun_data.get('longitude', 0)
        phase_angle = abs(moon_longitude - sun_longitude)
        if phase_angle > 180:
            phase_angle = 360 - phase_angle
            
        if phase_angle < 45:
            phase_energy = 'new beginnings and fresh starts'
        elif phase_angle < 90:
            phase_energy = 'building momentum and taking action'
        elif phase_angle < 135:
            phase_energy = 'overcoming challenges and making decisions'
        elif phase_angle < 180:
            phase_energy = 'refinement and preparation'
        else:
            phase_energy = 'culmination and manifestation'
        
        moon_energy = moon_energies.get(moon_sign, 'balanced')
        day_ruler, day_energy = day_rulers.get(weekday, ('Sun', 'balanced'))
        
        return f"Today's energy is {moon_energy} (Moon in {moon_sign}) with {day_energy} influence ({day_ruler}'s day), supporting {phase_energy}."
    
    def _calculate_best_time(self, sign: str, date: datetime) -> str:
        """Calculate personalized best time guidance for the sign"""
        # Get sign's ruling planet and element
        ruler = self.traditional_rulers.get(sign, 'Sun')
        element = {
            'Aries': 'fire', 'Leo': 'fire', 'Sagittarius': 'fire',
            'Taurus': 'earth', 'Virgo': 'earth', 'Capricorn': 'earth', 
            'Gemini': 'air', 'Libra': 'air', 'Aquarius': 'air',
            'Cancer': 'water', 'Scorpio': 'water', 'Pisces': 'water'
        }.get(sign, 'fire')
        
        # Planetary hour preferences
        ruler_times = {
            'Sun': 'morning hours (6-10 AM)',
            'Moon': 'evening hours (6-10 PM)',
            'Mars': 'early morning (5-8 AM)',
            'Mercury': 'mid-morning (9 AM-12 PM)',
            'Jupiter': 'late morning (10 AM-1 PM)',
            'Venus': 'afternoon (2-6 PM)',
            'Saturn': 'late evening (8-11 PM)'
        }
        
        # Element-based timing
        element_guidance = {
            'fire': 'Peak energy in morning, decisive action before noon',
            'earth': 'Steady progress throughout day, practical tasks afternoon',
            'air': 'Mental clarity mid-morning, communication peak midday',
            'water': 'Intuitive insights evening, emotional matters after sunset'
        }
        
        return f"{ruler_times.get(ruler, 'balanced throughout day')} favor your {sign} nature. {element_guidance.get(element, 'Maintain steady rhythm.')}"
    
    def _calculate_key_focus(self, sign: str, aspects: List[Dict], date: datetime) -> str:
        """Calculate one main thing to prioritize today"""
        # Get strongest daily aspect (Moon/Mercury)
        daily_aspects = [a for a in aspects if a['planet'] in ['Moon', 'Mercury']]
        strongest_aspect = daily_aspects[0] if daily_aspects else (aspects[0] if aspects else None)
        
        # Sign-based focus areas
        sign_focuses = {
            'Aries': 'Take bold action on a new initiative',
            'Taurus': 'Build something tangible and lasting',
            'Gemini': 'Connect and communicate with others',
            'Cancer': 'Nurture important relationships',
            'Leo': 'Express your authentic creative self',
            'Virgo': 'Perfect a skill or organize your space',
            'Libra': 'Create harmony in a key relationship',
            'Scorpio': 'Transform something that no longer serves',
            'Sagittarius': 'Expand your knowledge or horizons',
            'Capricorn': 'Make progress on a long-term goal',
            'Aquarius': 'Innovate or help your community',
            'Pisces': 'Trust your intuition in decision-making'
        }
        
        # Modify based on strongest aspect
        if strongest_aspect:
            planet = strongest_aspect['planet']
            nature = strongest_aspect['nature']
            
            if planet == 'Moon':
                if nature == 'harmonious':
                    return f"Trust your emotional intelligence - {sign_focuses.get(sign, 'follow your heart')}"
                else:
                    return f"Process emotions mindfully - {sign_focuses.get(sign, 'stay centered')}"
            elif planet == 'Mercury':
                if nature == 'harmonious':
                    return f"Communicate your ideas clearly - {sign_focuses.get(sign, 'share your thoughts')}"
                else:
                    return f"Think before speaking - {sign_focuses.get(sign, 'choose words wisely')}"
        
        return sign_focuses.get(sign, 'Stay true to your authentic self')
    
    def _calculate_what_to_avoid(self, sign: str, aspects: List[Dict], date: datetime) -> str:
        """Calculate one specific thing to be careful about today"""
        # Find strongest challenging aspect (Moon/Mercury)
        challenging_aspects = [a for a in aspects if a['planet'] in ['Moon', 'Mercury'] and a['nature'] == 'challenging']
        strongest_challenging = challenging_aspects[0] if challenging_aspects else None
        
        # Sign-specific weaknesses
        sign_weaknesses = {
            'Aries': 'impulsive decisions without considering consequences',
            'Taurus': 'stubborn resistance to necessary changes',
            'Gemini': 'spreading unverified information or gossip',
            'Cancer': 'dwelling on past hurts or emotional overwhelm',
            'Leo': 'ego conflicts or attention-seeking behavior',
            'Virgo': 'over-criticism of yourself or others',
            'Libra': 'indecision or excessive people-pleasing',
            'Scorpio': 'jealousy or power struggles in relationships',
            'Sagittarius': 'over-promising or being tactlessly blunt',
            'Capricorn': 'pessimistic thinking or workaholism',
            'Aquarius': 'emotional detachment or rebellious behavior',
            'Pisces': 'escapism or poor boundary setting'
        }
        
        # Modify based on challenging aspect
        if strongest_challenging:
            planet = strongest_challenging['planet']
            
            if planet == 'Moon':
                return f"Avoid emotional reactions - {sign_weaknesses.get(sign, 'reactive behavior')}"
            elif planet == 'Mercury':
                return f"Avoid miscommunication - {sign_weaknesses.get(sign, 'hasty words')}"
        
        return f"Avoid {sign_weaknesses.get(sign, 'your typical shadow tendencies')}"
    
    def _calculate_lucky_element(self, sign: str, aspects: List[Dict], date: datetime) -> str:
        """Calculate lucky color, number, and direction based on planetary influences"""
        # Find strongest beneficial aspect
        beneficial_aspects = [a for a in aspects if a['nature'] == 'harmonious']
        influence_planet = beneficial_aspects[0]['planet'] if beneficial_aspects else self.traditional_rulers.get(sign, 'Sun')
        
        # Planetary correspondences
        planet_elements = {
            'Sun': {'color': 'Gold', 'direction': 'East'},
            'Moon': {'color': 'Silver', 'direction': 'Northwest'},
            'Mercury': {'color': 'Light Blue', 'direction': 'North'},
            'Venus': {'color': 'Pink', 'direction': 'Southeast'},
            'Mars': {'color': 'Red', 'direction': 'South'},
            'Jupiter': {'color': 'Royal Blue', 'direction': 'Northeast'},
            'Saturn': {'color': 'Dark Blue', 'direction': 'West'}
        }
        
        # Get lucky number (already calculated)
        lucky_number = self._calculate_lucky_number(date)
        
        # Get planetary correspondences
        elements = planet_elements.get(influence_planet, planet_elements['Sun'])
        
        return f"Color: {elements['color']} • Number: {lucky_number} • Direction: {elements['direction']} ({influence_planet}'s energy enhances your {sign} nature)"
    
    def _calculate_love_guidance(self, sign: str, aspects: List[Dict], date: datetime) -> str:
        """Calculate romantic guidance combining sign style with day ruler and Venus/Moon aspects"""
        # Get day ruler
        weekday = date.weekday()
        day_rulers = {
            0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter',
            4: 'Venus', 5: 'Saturn', 6: 'Sun'
        }
        day_ruler = day_rulers.get(weekday, 'Sun')
        
        # Find Venus or Moon aspects
        venus_aspects = [a for a in aspects if a['planet'] == 'Venus']
        moon_aspects = [a for a in aspects if a['planet'] == 'Moon']
        
        # Sign romantic styles
        sign_romance = {
            'Aries': {'style': 'direct bold moves', 'action': 'text that person'},
            'Taurus': {'style': 'sensual steady approach', 'action': 'plan a romantic dinner'},
            'Gemini': {'style': 'playful communication', 'action': 'text that person'},
            'Cancer': {'style': 'nurturing emotional connection', 'action': 'plan a cozy date'},
            'Leo': {'style': 'grand romantic gestures', 'action': 'plan a special date'},
            'Virgo': {'style': 'thoughtful practical romance', 'action': 'plan a meaningful activity'},
            'Libra': {'style': 'harmonious balanced approach', 'action': 'plan a beautiful date'},
            'Scorpio': {'style': 'intense passionate connection', 'action': 'text that person'},
            'Sagittarius': {'style': 'adventurous spontaneous dates', 'action': 'plan an adventure'},
            'Capricorn': {'style': 'traditional committed approach', 'action': 'plan a serious conversation'},
            'Aquarius': {'style': 'unique friendship-first romance', 'action': 'text that person'},
            'Pisces': {'style': 'dreamy intuitive timing', 'action': 'trust your intuition'}
        }
        
        # Day ruler effects on romance
        day_effects = {
            'Venus': 'enhances all romantic activities',
            'Mars': 'adds passion but may be too aggressive',
            'Moon': 'perfect for emotional connection',
            'Mercury': 'great for romantic communication',
            'Jupiter': 'favors commitment and expansion',
            'Saturn': 'better for serious relationship talks',
            'Sun': 'good for confident romantic expression'
        }
        
        romance_info = sign_romance.get(sign, {'style': 'authentic expression', 'action': 'follow your heart'})
        
        # Determine guidance based on aspects and day
        if venus_aspects:
            aspect = venus_aspects[0]
            if aspect['nature'] == 'harmonious':
                return f"{romance_info['action'].title()} - Venus {aspect['aspect']} {day_effects.get(day_ruler, 'supports')} your {sign} {romance_info['style']}"
            else:
                return f"Give space - Venus {aspect['aspect']} creates tension, avoid pushing your {sign} {romance_info['style']} today"
        elif moon_aspects:
            aspect = moon_aspects[0]
            if aspect['nature'] == 'harmonious':
                return f"{romance_info['action'].title()} - Moon {aspect['aspect']} supports emotional connection with your {sign} {romance_info['style']}"
            else:
                return f"Give space - Moon {aspect['aspect']} may cause emotional instability, pause your {sign} {romance_info['style']}"
        else:
            # No Venus/Moon aspects, use day ruler + sign combination
            if day_ruler == 'Venus':
                return f"{romance_info['action'].title()} - Venus day {day_effects['Venus']} your {sign} {romance_info['style']}"
            elif day_ruler == 'Mars' and sign in ['Aries', 'Leo', 'Sagittarius', 'Scorpio']:
                return f"{romance_info['action'].title()} - Mars day adds passion to your {sign} {romance_info['style']}"
            elif day_ruler == 'Mars':
                return f"Give space - Mars day may be too aggressive for your {sign} {romance_info['style']}"
            elif day_ruler == 'Moon':
                return f"{romance_info['action'].title()} - Moon day {day_effects['Moon']} your {sign} {romance_info['style']}"
            else:
                return f"{romance_info['action'].title()} - {day_ruler} day {day_effects.get(day_ruler, 'supports')} your {sign} {romance_info['style']}"

    def _calculate_career_guidance(self, sign: str, aspects: List[Dict], date: datetime) -> str:
        """Calculate career guidance using real planetary positions and aspects"""
        # Get day ruler
        weekday = date.weekday()
        day_rulers = {
            0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter',
            4: 'Venus', 5: 'Saturn', 6: 'Sun'
        }
        day_ruler = day_rulers.get(weekday, 'Sun')
        
        # Find career-relevant aspects (Mars, Jupiter, Saturn, Mercury)
        career_aspects = [a for a in aspects if a['planet'] in ['Mars', 'Jupiter', 'Saturn', 'Mercury']]
        
        # Sign career styles
        sign_career = {
            'Aries': {'style': 'bold leadership initiatives', 'action': 'pitch that idea'},
            'Taurus': {'style': 'steady practical progress', 'action': 'focus on quality work'},
            'Gemini': {'style': 'networking and communication', 'action': 'connect with colleagues'},
            'Cancer': {'style': 'nurturing team relationships', 'action': 'support your team'},
            'Leo': {'style': 'creative confident leadership', 'action': 'showcase your talents'},
            'Virgo': {'style': 'detailed analytical work', 'action': 'perfect that project'},
            'Libra': {'style': 'collaborative diplomatic approach', 'action': 'mediate that conflict'},
            'Scorpio': {'style': 'strategic transformative work', 'action': 'research deeply'},
            'Sagittarius': {'style': 'visionary expansive thinking', 'action': 'explore new opportunities'},
            'Capricorn': {'style': 'structured goal achievement', 'action': 'advance that long-term plan'},
            'Aquarius': {'style': 'innovative team collaboration', 'action': 'propose that innovation'},
            'Pisces': {'style': 'intuitive creative solutions', 'action': 'trust your instincts'}
        }
        
        # Day ruler effects on career
        day_effects = {
            'Mars': 'adds drive and competitive edge',
            'Jupiter': 'expands opportunities and recognition',
            'Saturn': 'demands discipline and long-term thinking',
            'Mercury': 'enhances communication and networking',
            'Venus': 'improves collaboration and creative work',
            'Moon': 'heightens intuition and people skills',
            'Sun': 'boosts confidence and leadership'
        }
        
        career_info = sign_career.get(sign, {'style': 'authentic professional expression', 'action': 'stay true to your values'})
        
        # Determine guidance based on career aspects and day
        if career_aspects:
            aspect = career_aspects[0]  # Strongest career aspect
            planet = aspect['planet']
            
            if aspect['nature'] == 'harmonious':
                if planet == 'Mars':
                    return f"{career_info['action'].title()} - Mars {aspect['aspect']} energizes your {sign} {career_info['style']}, perfect for taking initiative"
                elif planet == 'Jupiter':
                    return f"{career_info['action'].title()} - Jupiter {aspect['aspect']} expands opportunities for your {sign} {career_info['style']}"
                elif planet == 'Saturn':
                    return f"{career_info['action'].title()} - Saturn {aspect['aspect']} rewards your {sign} {career_info['style']} with lasting results"
                elif planet == 'Mercury':
                    return f"{career_info['action'].title()} - Mercury {aspect['aspect']} enhances communication in your {sign} {career_info['style']}"
            else:  # challenging
                if planet == 'Mars':
                    return f"Avoid conflicts - Mars {aspect['aspect']} may make your {sign} {career_info['style']} too aggressive today"
                elif planet == 'Jupiter':
                    return f"Stay realistic - Jupiter {aspect['aspect']} may cause overconfidence in your {sign} {career_info['style']}"
                elif planet == 'Saturn':
                    return f"Be patient - Saturn {aspect['aspect']} tests your {sign} {career_info['style']} with obstacles"
                elif planet == 'Mercury':
                    return f"Double-check details - Mercury {aspect['aspect']} may cause miscommunication in your {sign} {career_info['style']}"
        
        # No career aspects, use day ruler + sign combination
        if day_ruler == 'Mars' and sign in ['Aries', 'Leo', 'Sagittarius', 'Capricorn']:
            return f"{career_info['action'].title()} - Mars day {day_effects['Mars']} your {sign} {career_info['style']}"
        elif day_ruler == 'Jupiter':
            return f"{career_info['action'].title()} - Jupiter day {day_effects['Jupiter']} your {sign} {career_info['style']}"
        elif day_ruler == 'Saturn':
            return f"{career_info['action'].title()} - Saturn day {day_effects['Saturn']} your {sign} {career_info['style']}"
        elif day_ruler == 'Mercury':
            return f"{career_info['action'].title()} - Mercury day {day_effects['Mercury']} your {sign} {career_info['style']}"
        else:
            return f"{career_info['action'].title()} - {day_ruler} day {day_effects.get(day_ruler, 'supports')} your {sign} {career_info['style']}"

    def _calculate_health_guidance(self, sign: str, aspects: List[Dict], date: datetime) -> str:
        """Calculate health guidance using real planetary positions and aspects"""
        # Get day ruler
        weekday = date.weekday()
        day_rulers = {
            0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter',
            4: 'Venus', 5: 'Saturn', 6: 'Sun'
        }
        day_ruler = day_rulers.get(weekday, 'Sun')
        
        # Find health-relevant aspects (Mars, Moon, Saturn, Sun)
        health_aspects = [a for a in aspects if a['planet'] in ['Mars', 'Moon', 'Saturn', 'Sun']]
        
        # Sign health focus areas
        sign_health = {
            'Aries': {'focus': 'head and energy levels', 'action': 'do cardio exercise'},
            'Taurus': {'focus': 'throat and metabolism', 'action': 'eat nourishing foods'},
            'Gemini': {'focus': 'lungs and nervous system', 'action': 'practice breathing exercises'},
            'Cancer': {'focus': 'stomach and emotional wellness', 'action': 'nurture your digestive health'},
            'Leo': {'focus': 'heart and vitality', 'action': 'get sunlight and movement'},
            'Virgo': {'focus': 'digestion and daily routines', 'action': 'maintain healthy habits'},
            'Libra': {'focus': 'kidneys and balance', 'action': 'stay hydrated and balanced'},
            'Scorpio': {'focus': 'reproductive health and detox', 'action': 'support your body\'s cleansing'},
            'Sagittarius': {'focus': 'hips and liver health', 'action': 'stay active and mobile'},
            'Capricorn': {'focus': 'bones and joints', 'action': 'strengthen your structure'},
            'Aquarius': {'focus': 'circulation and ankles', 'action': 'improve blood flow'},
            'Pisces': {'focus': 'feet and immune system', 'action': 'rest and restore'}
        }
        
        # Day ruler effects on health
        day_effects = {
            'Mars': 'boosts energy but may cause inflammation',
            'Moon': 'affects emotions and fluid balance',
            'Saturn': 'tests endurance and structural health',
            'Sun': 'enhances vitality and immune function',
            'Mercury': 'affects nervous system and mental clarity',
            'Venus': 'supports beauty and hormonal balance',
            'Jupiter': 'promotes healing and overall wellness'
        }
        
        health_info = sign_health.get(sign, {'focus': 'overall wellness', 'action': 'listen to your body'})
        
        # Determine guidance based on health aspects and day
        if health_aspects:
            aspect = health_aspects[0]  # Strongest health aspect
            planet = aspect['planet']
            
            if aspect['nature'] == 'harmonious':
                if planet == 'Mars':
                    return f"{health_info['action'].title()} - Mars {aspect['aspect']} energizes your {sign} {health_info['focus']}, perfect for physical activity"
                elif planet == 'Moon':
                    return f"{health_info['action'].title()} - Moon {aspect['aspect']} supports your {sign} {health_info['focus']} through emotional wellness"
                elif planet == 'Saturn':
                    return f"{health_info['action'].title()} - Saturn {aspect['aspect']} strengthens your {sign} {health_info['focus']} with discipline"
                elif planet == 'Sun':
                    return f"{health_info['action'].title()} - Sun {aspect['aspect']} vitalizes your {sign} {health_info['focus']} naturally"
            else:  # challenging
                if planet == 'Mars':
                    return f"Avoid overexertion - Mars {aspect['aspect']} may stress your {sign} {health_info['focus']} today"
                elif planet == 'Moon':
                    return f"Manage stress - Moon {aspect['aspect']} may affect your {sign} {health_info['focus']} emotionally"
                elif planet == 'Saturn':
                    return f"Be gentle - Saturn {aspect['aspect']} may create tension in your {sign} {health_info['focus']}"
                elif planet == 'Sun':
                    return f"Conserve energy - Sun {aspect['aspect']} may drain your {sign} {health_info['focus']} vitality"
        
        # No health aspects, use day ruler + sign combination
        if day_ruler == 'Mars':
            return f"{health_info['action'].title()} - Mars day {day_effects['Mars']} your {sign} {health_info['focus']}"
        elif day_ruler == 'Moon':
            return f"{health_info['action'].title()} - Moon day {day_effects['Moon']} your {sign} {health_info['focus']}"
        elif day_ruler == 'Saturn':
            return f"{health_info['action'].title()} - Saturn day {day_effects['Saturn']} your {sign} {health_info['focus']}"
        elif day_ruler == 'Sun':
            return f"{health_info['action'].title()} - Sun day {day_effects['Sun']} your {sign} {health_info['focus']}"
        else:
            return f"{health_info['action'].title()} - {day_ruler} day {day_effects.get(day_ruler, 'supports overall wellness')} your {sign} {health_info['focus']}"

    def _calculate_finance_guidance(self, sign: str, aspects: List[Dict], date: datetime) -> str:
        """Calculate finance guidance using real planetary positions and aspects"""
        # Get day ruler
        weekday = date.weekday()
        day_rulers = {
            0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter',
            4: 'Venus', 5: 'Saturn', 6: 'Sun'
        }
        day_ruler = day_rulers.get(weekday, 'Sun')
        
        # Find finance-relevant aspects (Jupiter, Venus, Saturn, Mars)
        finance_aspects = [a for a in aspects if a['planet'] in ['Jupiter', 'Venus', 'Saturn', 'Mars']]
        
        # Sign financial approaches
        sign_finance = {
            'Aries': {'style': 'bold investment decisions', 'action': 'take calculated risks'},
            'Taurus': {'style': 'steady wealth building', 'action': 'focus on long-term savings'},
            'Gemini': {'style': 'diverse income streams', 'action': 'explore new opportunities'},
            'Cancer': {'style': 'security-focused planning', 'action': 'protect your resources'},
            'Leo': {'style': 'confident financial moves', 'action': 'invest in your talents'},
            'Virgo': {'style': 'detailed budget analysis', 'action': 'review your expenses'},
            'Libra': {'style': 'balanced portfolio approach', 'action': 'seek financial harmony'},
            'Scorpio': {'style': 'strategic wealth transformation', 'action': 'research investments deeply'},
            'Sagittarius': {'style': 'expansive financial vision', 'action': 'explore global markets'},
            'Capricorn': {'style': 'structured wealth accumulation', 'action': 'stick to your financial plan'},
            'Aquarius': {'style': 'innovative investment strategies', 'action': 'consider new financial tech'},
            'Pisces': {'style': 'intuitive money decisions', 'action': 'trust your financial instincts'}
        }
        
        # Day ruler effects on finances
        day_effects = {
            'Jupiter': 'expands financial opportunities and luck',
            'Venus': 'attracts money through beauty and relationships',
            'Saturn': 'demands disciplined financial planning',
            'Mars': 'energizes earning potential but may cause impulsive spending',
            'Mercury': 'enhances financial communication and deals',
            'Moon': 'affects emotional spending and family finances',
            'Sun': 'boosts confidence in financial decisions'
        }
        
        finance_info = sign_finance.get(sign, {'style': 'balanced financial approach', 'action': 'make wise money choices'})
        
        # Determine guidance based on finance aspects and day
        if finance_aspects:
            aspect = finance_aspects[0]  # Strongest finance aspect
            planet = aspect['planet']
            
            if aspect['nature'] == 'harmonious':
                if planet == 'Jupiter':
                    return f"{finance_info['action'].title()} - Jupiter {aspect['aspect']} expands your {sign} {finance_info['style']}, perfect for growth investments"
                elif planet == 'Venus':
                    return f"{finance_info['action'].title()} - Venus {aspect['aspect']} attracts money through your {sign} {finance_info['style']}"
                elif planet == 'Saturn':
                    return f"{finance_info['action'].title()} - Saturn {aspect['aspect']} rewards your {sign} {finance_info['style']} with lasting wealth"
                elif planet == 'Mars':
                    return f"{finance_info['action'].title()} - Mars {aspect['aspect']} energizes your {sign} {finance_info['style']}, act on opportunities"
            else:  # challenging
                if planet == 'Jupiter':
                    return f"Avoid overconfidence - Jupiter {aspect['aspect']} may cause overextension in your {sign} {finance_info['style']}"
                elif planet == 'Venus':
                    return f"Control spending - Venus {aspect['aspect']} may tempt overspending on your {sign} {finance_info['style']}"
                elif planet == 'Saturn':
                    return f"Be patient - Saturn {aspect['aspect']} tests your {sign} {finance_info['style']} with restrictions"
                elif planet == 'Mars':
                    return f"Avoid impulsive decisions - Mars {aspect['aspect']} may rush your {sign} {finance_info['style']}"
        
        # No finance aspects, use day ruler + sign combination
        if day_ruler == 'Jupiter':
            return f"{finance_info['action'].title()} - Jupiter day {day_effects['Jupiter']} your {sign} {finance_info['style']}"
        elif day_ruler == 'Venus':
            return f"{finance_info['action'].title()} - Venus day {day_effects['Venus']} your {sign} {finance_info['style']}"
        elif day_ruler == 'Saturn':
            return f"{finance_info['action'].title()} - Saturn day {day_effects['Saturn']} your {sign} {finance_info['style']}"
        elif day_ruler == 'Mars':
            return f"{finance_info['action'].title()} - Mars day {day_effects['Mars']} your {sign} {finance_info['style']}"
        else:
            return f"{finance_info['action'].title()} - {day_ruler} day {day_effects.get(day_ruler, 'supports financial awareness')} your {sign} {finance_info['style']}"

    def _calculate_education_guidance(self, sign: str, aspects: List[Dict], date: datetime) -> str:
        """Calculate education guidance using real planetary positions and aspects"""
        # Get day ruler
        weekday = date.weekday()
        day_rulers = {
            0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter',
            4: 'Venus', 5: 'Saturn', 6: 'Sun'
        }
        day_ruler = day_rulers.get(weekday, 'Sun')
        
        # Find education-relevant aspects (Mercury, Jupiter, Saturn, Moon)
        education_aspects = [a for a in aspects if a['planet'] in ['Mercury', 'Jupiter', 'Saturn', 'Moon']]
        
        # Sign learning styles
        sign_education = {
            'Aries': {'style': 'hands-on active learning', 'action': 'start that course'},
            'Taurus': {'style': 'practical step-by-step study', 'action': 'build consistent study habits'},
            'Gemini': {'style': 'diverse multi-topic learning', 'action': 'explore new subjects'},
            'Cancer': {'style': 'emotional memory-based learning', 'action': 'create study groups'},
            'Leo': {'style': 'creative presentation-focused study', 'action': 'teach others what you learn'},
            'Virgo': {'style': 'detailed analytical study methods', 'action': 'organize your study materials'},
            'Libra': {'style': 'collaborative balanced learning', 'action': 'find study partners'},
            'Scorpio': {'style': 'deep research-intensive study', 'action': 'dive into specialized topics'},
            'Sagittarius': {'style': 'philosophical broad-scope learning', 'action': 'explore higher education'},
            'Capricorn': {'style': 'structured goal-oriented study', 'action': 'plan your educational path'},
            'Aquarius': {'style': 'innovative technology-based learning', 'action': 'try online courses'},
            'Pisces': {'style': 'intuitive creative learning', 'action': 'trust your learning instincts'}
        }
        
        # Day ruler effects on education
        day_effects = {
            'Mercury': 'enhances mental clarity and information processing',
            'Jupiter': 'expands learning opportunities and wisdom',
            'Saturn': 'demands disciplined study and long-term commitment',
            'Moon': 'supports memory retention and intuitive learning',
            'Mars': 'energizes active learning but may cause impatience',
            'Venus': 'makes learning enjoyable and artistic',
            'Sun': 'boosts confidence in educational pursuits'
        }
        
        education_info = sign_education.get(sign, {'style': 'balanced learning approach', 'action': 'pursue knowledge wisely'})
        
        # Determine guidance based on education aspects and day
        if education_aspects:
            aspect = education_aspects[0]  # Strongest education aspect
            planet = aspect['planet']
            
            if aspect['nature'] == 'harmonious':
                if planet == 'Mercury':
                    return f"{education_info['action'].title()} - Mercury {aspect['aspect']} sharpens your {sign} {education_info['style']}, perfect for learning"
                elif planet == 'Jupiter':
                    return f"{education_info['action'].title()} - Jupiter {aspect['aspect']} expands your {sign} {education_info['style']} with wisdom"
                elif planet == 'Saturn':
                    return f"{education_info['action'].title()} - Saturn {aspect['aspect']} rewards your {sign} {education_info['style']} with mastery"
                elif planet == 'Moon':
                    return f"{education_info['action'].title()} - Moon {aspect['aspect']} enhances memory in your {sign} {education_info['style']}"
            else:  # challenging
                if planet == 'Mercury':
                    return f"Stay focused - Mercury {aspect['aspect']} may scatter your {sign} {education_info['style']} today"
                elif planet == 'Jupiter':
                    return f"Avoid overcommitting - Jupiter {aspect['aspect']} may overwhelm your {sign} {education_info['style']}"
                elif planet == 'Saturn':
                    return f"Be patient - Saturn {aspect['aspect']} tests your {sign} {education_info['style']} with challenges"
                elif planet == 'Moon':
                    return f"Manage distractions - Moon {aspect['aspect']} may affect focus in your {sign} {education_info['style']}"
        
        # No education aspects, use day ruler + sign combination
        if day_ruler == 'Mercury':
            return f"{education_info['action'].title()} - Mercury day {day_effects['Mercury']} your {sign} {education_info['style']}"
        elif day_ruler == 'Jupiter':
            return f"{education_info['action'].title()} - Jupiter day {day_effects['Jupiter']} your {sign} {education_info['style']}"
        elif day_ruler == 'Saturn':
            return f"{education_info['action'].title()} - Saturn day {day_effects['Saturn']} your {sign} {education_info['style']}"
        elif day_ruler == 'Moon':
            return f"{education_info['action'].title()} - Moon day {day_effects['Moon']} your {sign} {education_info['style']}"
        else:
            return f"{education_info['action'].title()} - {day_ruler} day {day_effects.get(day_ruler, 'supports learning')} your {sign} {education_info['style']}"

    def _calculate_spirituality_guidance(self, sign: str, aspects: List[Dict], date: datetime) -> str:
        """Calculate spirituality guidance using real planetary positions and aspects"""
        # Get day ruler
        weekday = date.weekday()
        day_rulers = {
            0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter',
            4: 'Venus', 5: 'Saturn', 6: 'Sun'
        }
        day_ruler = day_rulers.get(weekday, 'Sun')
        
        # Find spirituality-relevant aspects (Jupiter, Neptune, Moon, Saturn)
        spiritual_aspects = [a for a in aspects if a['planet'] in ['Jupiter', 'Neptune', 'Moon', 'Saturn']]
        
        # Sign spiritual approaches
        sign_spirituality = {
            'Aries': {'style': 'dynamic action-based practice', 'action': 'start a new spiritual discipline'},
            'Taurus': {'style': 'grounded earth-based rituals', 'action': 'connect with nature daily'},
            'Gemini': {'style': 'diverse study of wisdom traditions', 'action': 'explore different spiritual paths'},
            'Cancer': {'style': 'emotional devotional practices', 'action': 'practice heart-centered meditation'},
            'Leo': {'style': 'creative expressive spirituality', 'action': 'express your spiritual gifts'},
            'Virgo': {'style': 'detailed systematic practice', 'action': 'establish daily spiritual routines'},
            'Libra': {'style': 'harmonious balanced approach', 'action': 'seek spiritual partnerships'},
            'Scorpio': {'style': 'deep transformative practices', 'action': 'embrace shadow work'},
            'Sagittarius': {'style': 'philosophical truth-seeking', 'action': 'study sacred texts'},
            'Capricorn': {'style': 'disciplined traditional methods', 'action': 'commit to long-term practice'},
            'Aquarius': {'style': 'innovative group consciousness', 'action': 'join spiritual communities'},
            'Pisces': {'style': 'intuitive mystical connection', 'action': 'trust your spiritual visions'}
        }
        
        # Day ruler effects on spirituality
        day_effects = {
            'Jupiter': 'expands spiritual wisdom and divine connection',
            'Neptune': 'enhances mystical experiences and intuition',
            'Moon': 'deepens emotional and psychic sensitivity',
            'Saturn': 'demands disciplined spiritual practice',
            'Sun': 'illuminates spiritual purpose and divine self',
            'Venus': 'brings beauty and love to spiritual practice',
            'Mercury': 'enhances spiritual communication and study'
        }
        
        spiritual_info = sign_spirituality.get(sign, {'style': 'authentic spiritual expression', 'action': 'follow your spiritual calling'})
        
        # Determine guidance based on spiritual aspects and day
        if spiritual_aspects:
            aspect = spiritual_aspects[0]  # Strongest spiritual aspect
            planet = aspect['planet']
            
            if aspect['nature'] == 'harmonious':
                if planet == 'Jupiter':
                    return f"{spiritual_info['action'].title()} - Jupiter {aspect['aspect']} expands your {sign} {spiritual_info['style']}, perfect for spiritual growth"
                elif planet == 'Neptune':
                    return f"{spiritual_info['action'].title()} - Neptune {aspect['aspect']} enhances mystical experiences in your {sign} {spiritual_info['style']}"
                elif planet == 'Moon':
                    return f"{spiritual_info['action'].title()} - Moon {aspect['aspect']} deepens intuition in your {sign} {spiritual_info['style']}"
                elif planet == 'Saturn':
                    return f"{spiritual_info['action'].title()} - Saturn {aspect['aspect']} rewards disciplined {sign} {spiritual_info['style']}"
            else:  # challenging
                if planet == 'Jupiter':
                    return f"Stay grounded - Jupiter {aspect['aspect']} may cause spiritual overconfidence in your {sign} {spiritual_info['style']}"
                elif planet == 'Neptune':
                    return f"Seek clarity - Neptune {aspect['aspect']} may create spiritual confusion in your {sign} {spiritual_info['style']}"
                elif planet == 'Moon':
                    return f"Center yourself - Moon {aspect['aspect']} may cause emotional spiritual turbulence in your {sign} {spiritual_info['style']}"
                elif planet == 'Saturn':
                    return f"Be patient - Saturn {aspect['aspect']} tests your {sign} {spiritual_info['style']} with spiritual challenges"
        
        # No spiritual aspects, use day ruler + sign combination
        if day_ruler == 'Jupiter':
            return f"{spiritual_info['action'].title()} - Jupiter day {day_effects['Jupiter']} your {sign} {spiritual_info['style']}"
        elif day_ruler == 'Moon':
            return f"{spiritual_info['action'].title()} - Moon day {day_effects['Moon']} your {sign} {spiritual_info['style']}"
        elif day_ruler == 'Saturn':
            return f"{spiritual_info['action'].title()} - Saturn day {day_effects['Saturn']} your {sign} {spiritual_info['style']}"
        elif day_ruler == 'Sun':
            return f"{spiritual_info['action'].title()} - Sun day {day_effects['Sun']} your {sign} {spiritual_info['style']}"
        else:
            return f"{spiritual_info['action'].title()} - {day_ruler} day {day_effects.get(day_ruler, 'supports spiritual awareness')} your {sign} {spiritual_info['style']}"

    def _calculate_daily_actions(self, sign: str, aspects: List[Dict], date: datetime) -> Dict:
        """Calculate 3 daily actions and 1 avoidance using real planetary data"""
        strongest_aspect = aspects[0] if aspects else None
        challenging_aspects = [a for a in aspects if a['nature'] == 'challenging']
        
        # Sign-specific action styles
        sign_actions = {
            'Aries': ['Take bold initiative', 'Start new project', 'Lead team meeting'],
            'Taurus': ['Build lasting foundation', 'Focus on quality work', 'Nurture relationships'],
            'Gemini': ['Connect with others', 'Learn new skill', 'Share information'],
            'Cancer': ['Support family member', 'Create safe space', 'Trust emotions'],
            'Leo': ['Express creativity', 'Showcase talents', 'Inspire others'],
            'Virgo': ['Organize workspace', 'Perfect details', 'Serve others'],
            'Libra': ['Create harmony', 'Mediate conflict', 'Beautify environment'],
            'Scorpio': ['Research deeply', 'Transform situation', 'Face truth'],
            'Sagittarius': ['Explore opportunity', 'Expand knowledge', 'Share wisdom'],
            'Capricorn': ['Plan long-term', 'Build authority', 'Achieve goal'],
            'Aquarius': ['Innovate solution', 'Help community', 'Think differently'],
            'Pisces': ['Trust intuition', 'Practice compassion', 'Create art']
        }
        
        actions = sign_actions.get(sign, ['Take authentic action', 'Stay true to self', 'Follow heart'])
        
        # Modify based on strongest aspect
        if strongest_aspect and strongest_aspect['nature'] == 'harmonious':
            actions[0] = f"{actions[0]} ({strongest_aspect['planet']} {strongest_aspect['aspect']} supports)"
        
        # Calculate avoidance
        avoid = 'impulsive reactions'
        if challenging_aspects:
            planet = challenging_aspects[0]['planet']
            if planet == 'Mars':
                avoid = 'aggressive confrontations'
            elif planet == 'Mercury':
                avoid = 'hasty communications'
            elif planet == 'Venus':
                avoid = 'emotional overspending'
            elif planet == 'Saturn':
                avoid = 'pessimistic thinking'
        
        return {
            'actions': actions,
            'avoid': avoid
        }

    def _calculate_energy_forecast(self, sign: str, aspects: List[Dict], planets: Dict, date: datetime) -> Dict:
        """Calculate morning/afternoon/evening energy levels using real planetary data"""
        mars_data = planets.get('Mars', {})
        sun_data = planets.get('Sun', {})
        moon_data = planets.get('Moon', {})
        
        # Base energy by sign element
        element_energy = {
            'Aries': {'morning': 85, 'afternoon': 70, 'evening': 60},
            'Leo': {'morning': 80, 'afternoon': 85, 'evening': 65},
            'Sagittarius': {'morning': 75, 'afternoon': 80, 'evening': 70},
            'Taurus': {'morning': 60, 'afternoon': 80, 'evening': 75},
            'Virgo': {'morning': 70, 'afternoon': 85, 'evening': 65},
            'Capricorn': {'morning': 75, 'afternoon': 80, 'evening': 60},
            'Gemini': {'morning': 70, 'afternoon': 85, 'evening': 70},
            'Libra': {'morning': 65, 'afternoon': 75, 'evening': 80},
            'Aquarius': {'morning': 60, 'afternoon': 70, 'evening': 85},
            'Cancer': {'morning': 55, 'afternoon': 65, 'evening': 85},
            'Scorpio': {'morning': 60, 'afternoon': 70, 'evening': 90},
            'Pisces': {'morning': 50, 'afternoon': 60, 'evening': 85}
        }
        
        base_energy = element_energy.get(sign, {'morning': 70, 'afternoon': 75, 'evening': 70})
        
        # Modify based on Mars aspects (energy planet)
        mars_aspects = [a for a in aspects if a['planet'] == 'Mars']
        energy_modifier = 0
        if mars_aspects:
            if mars_aspects[0]['nature'] == 'harmonious':
                energy_modifier = 15
            else:
                energy_modifier = -10
        
        return {
            'morning': min(100, max(0, base_energy['morning'] + energy_modifier)),
            'afternoon': min(100, max(0, base_energy['afternoon'] + energy_modifier)),
            'evening': min(100, max(0, base_energy['evening'] + energy_modifier)),
            'peak_time': 'morning' if base_energy['morning'] >= max(base_energy['afternoon'], base_energy['evening']) else ('afternoon' if base_energy['afternoon'] >= base_energy['evening'] else 'evening')
        }

    def _calculate_daily_summary(self, sign: str, aspects: List[Dict], date: datetime) -> Dict:
        """Calculate one-line theme, emoji, and 3-word essence"""
        strongest_aspect = aspects[0] if aspects else None
        
        # Sign themes
        sign_themes = {
            'Aries': 'Bold action leads to breakthrough',
            'Taurus': 'Steady progress builds lasting value',
            'Gemini': 'Communication opens new doors',
            'Cancer': 'Emotional wisdom guides decisions',
            'Leo': 'Creative expression shines bright',
            'Virgo': 'Attention to detail pays off',
            'Libra': 'Balance creates beautiful harmony',
            'Scorpio': 'Deep transformation brings power',
            'Sagittarius': 'Adventure expands your horizons',
            'Capricorn': 'Discipline achieves ambitious goals',
            'Aquarius': 'Innovation serves greater good',
            'Pisces': 'Intuition reveals hidden truth'
        }
        
        # Modify theme based on strongest aspect
        theme = sign_themes.get(sign, 'Authentic self expression flows')
        if strongest_aspect:
            if strongest_aspect['nature'] == 'challenging':
                theme = theme.replace('leads to', 'requires patience for').replace('creates', 'needs work to create')
        
        # Emoji based on aspect harmony
        harmonious_count = sum(1 for a in aspects if a['nature'] == 'harmonious')
        challenging_count = sum(1 for a in aspects if a['nature'] == 'challenging')
        
        if harmonious_count > challenging_count:
            emoji = '⚡'
        elif challenging_count > harmonious_count:
            emoji = '🌊'
        else:
            emoji = '⚖️'
        
        # 3-word essence
        essences = {
            'Aries': 'Dynamic Bold Leadership',
            'Taurus': 'Grounded Steady Growth',
            'Gemini': 'Curious Social Connection',
            'Cancer': 'Nurturing Emotional Depth',
            'Leo': 'Creative Confident Expression',
            'Virgo': 'Practical Detailed Service',
            'Libra': 'Harmonious Balanced Beauty',
            'Scorpio': 'Intense Transformative Power',
            'Sagittarius': 'Adventurous Philosophical Expansion',
            'Capricorn': 'Disciplined Ambitious Achievement',
            'Aquarius': 'Innovative Humanitarian Vision',
            'Pisces': 'Intuitive Compassionate Flow'
        }
        
        return {
            'theme': theme,
            'emoji': emoji,
            'essence': essences.get(sign, 'Authentic Self Expression')
        }

    def _calculate_moon_timing(self, planets: Dict, date: datetime) -> Dict:
        """Calculate moon phase and void of course periods using real data"""
        moon_data = planets.get('Moon', {})
        sun_data = planets.get('Sun', {})
        
        # Calculate exact phase angle
        moon_longitude = moon_data.get('longitude', 0)
        sun_longitude = sun_data.get('longitude', 0)
        phase_angle = abs(moon_longitude - sun_longitude)
        if phase_angle > 180:
            phase_angle = 360 - phase_angle
        
        # Determine phase
        if phase_angle < 45:
            phase = 'New Moon'
            phase_meaning = 'Perfect for new beginnings and setting intentions'
        elif phase_angle < 90:
            phase = 'Waxing Crescent'
            phase_meaning = 'Build momentum and take action on goals'
        elif phase_angle < 135:
            phase = 'First Quarter'
            phase_meaning = 'Push through obstacles and make decisions'
        elif phase_angle < 180:
            phase = 'Waxing Gibbous'
            phase_meaning = 'Refine plans and prepare for manifestation'
        else:
            phase = 'Full Moon'
            phase_meaning = 'Harvest results and celebrate achievements'
        
        # Moon sign timing
        moon_sign = moon_data.get('sign', 'Aries')
        moon_activities = {
            'Aries': 'Start new projects, take bold action',
            'Taurus': 'Focus on finances, enjoy sensual pleasures',
            'Gemini': 'Communicate, learn, make connections',
            'Cancer': 'Nurture family, process emotions',
            'Leo': 'Express creativity, seek recognition',
            'Virgo': 'Organize, analyze, serve others',
            'Libra': 'Create harmony, focus on relationships',
            'Scorpio': 'Transform, research, heal deeply',
            'Sagittarius': 'Explore, teach, seek truth',
            'Capricorn': 'Plan long-term, build authority',
            'Aquarius': 'Innovate, help community, think big',
            'Pisces': 'Meditate, create art, trust intuition'
        }
        
        return {
            'phase': phase,
            'phase_meaning': phase_meaning,
            'moon_sign': moon_sign,
            'best_activities': moon_activities.get(moon_sign, 'Follow natural rhythms')
        }

    def _calculate_intuitive_insights(self, sign: str, aspects: List[Dict], planets: Dict, date: datetime) -> Dict:
        """Calculate psychic sensitivity and synchronicity levels using real planetary data"""
        neptune_aspects = [a for a in aspects if a['planet'] == 'Neptune']
        moon_aspects = [a for a in aspects if a['planet'] == 'Moon']
        
        # Base psychic sensitivity by sign
        base_sensitivity = {
            'Pisces': 90, 'Cancer': 85, 'Scorpio': 80,
            'Virgo': 70, 'Capricorn': 65, 'Taurus': 60,
            'Libra': 75, 'Aquarius': 70, 'Gemini': 65,
            'Sagittarius': 75, 'Leo': 60, 'Aries': 55
        }
        
        sensitivity = base_sensitivity.get(sign, 70)
        
        # Modify based on Neptune aspects
        if neptune_aspects:
            if neptune_aspects[0]['nature'] == 'harmonious':
                sensitivity += 20
            else:
                sensitivity += 10  # Even challenging Neptune increases sensitivity
        
        # Synchronicity level based on Jupiter aspects
        jupiter_aspects = [a for a in aspects if a['planet'] == 'Jupiter']
        synchronicity = 60
        if jupiter_aspects:
            if jupiter_aspects[0]['nature'] == 'harmonious':
                synchronicity = 85
            else:
                synchronicity = 70
        
        # Dream significance
        dream_significance = 'moderate'
        if moon_aspects:
            if moon_aspects[0]['nature'] == 'harmonious':
                dream_significance = 'high'
            else:
                dream_significance = 'intense but confusing'
        
        # Calculate signs to watch based on actual planetary positions
        signs_to_watch = []
        
        # Add Moon sign (emotional/intuitive significance)
        moon_sign = planets.get('Moon', {}).get('sign', 'Aries')
        signs_to_watch.append(f"{moon_sign} themes (Moon's emotional influence)")
        
        # Add signs of planets making strong aspects
        for aspect in aspects[:2]:  # Top 2 aspects
            planet_sign = None
            for planet_name, planet_data in planets.items():
                if planet_name == aspect['planet']:
                    planet_sign = planet_data.get('sign', 'Aries')
                    break
            if planet_sign:
                signs_to_watch.append(f"{planet_sign} symbols ({aspect['planet']} {aspect['aspect']})")
        
        # If no strong aspects, use day ruler sign
        if len(signs_to_watch) == 1:
            weekday = date.weekday()
            day_rulers = {0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Sun'}
            day_ruler = day_rulers.get(weekday, 'Sun')
            for planet_name, planet_data in planets.items():
                if planet_name == day_ruler:
                    ruler_sign = planet_data.get('sign', 'Aries')
                    signs_to_watch.append(f"{ruler_sign} energy ({day_ruler}'s day)")
                    break
        
        signs_text = "Watch for: " + ", ".join(signs_to_watch[:3])  # Limit to 3 signs
        
        return {
            'psychic_sensitivity': min(100, sensitivity),
            'synchronicity_level': synchronicity,
            'dream_significance': dream_significance,
            'signs_to_watch': self._get_detailed_signs_to_watch(sign, aspects, planets, date)
        }

    def _generate_spirituality_from_aspects(self, sun_sign: str, aspects: List[Dict], period: str) -> str:
        """Generate spirituality prediction from aspects"""
        spiritual_planets = ['Jupiter', 'Neptune', 'Moon', 'Saturn']
        spiritual_aspects = [a for a in aspects if a['planet'] in spiritual_planets]
        
        if spiritual_aspects:
            aspect = spiritual_aspects[0]
            planet = aspect['planet']
            
            if aspect['nature'] == 'harmonious':
                return f"{planet}'s supportive {aspect['aspect']} enhances spiritual connection and divine guidance. This {period} favors meditation, prayer, and sacred practices that align with your soul purpose."
            else:
                return f"{planet}'s challenging {aspect['aspect']} requires deeper spiritual commitment. Use this {period} to overcome spiritual obstacles through disciplined practice and faith."
        
        else:
            return f"Spiritual matters flow steadily this {period}. Maintain your regular practices and stay open to divine guidance through your natural {sun_sign} spiritual expression."

    def _generate_education_from_aspects(self, sun_sign: str, aspects: List[Dict], period: str) -> str:
        """Generate education prediction from aspects"""
        education_planets = ['Mercury', 'Jupiter', 'Saturn']
        education_aspects = [a for a in aspects if a['planet'] in education_planets]
        
        if education_aspects:
            aspect = education_aspects[0]
            planet = aspect['planet']
            themes = self._get_planet_themes(planet)
            
            if aspect['nature'] == 'harmonious':
                return f"{planet}'s supportive {aspect['aspect']} enhances learning opportunities, particularly in {themes.get('education', 'knowledge acquisition')}. This {period} favors educational advancement and skill development."
            else:
                return f"{planet}'s challenging {aspect['aspect']} requires focused study habits. Overcome learning obstacles through persistence in {themes.get('education', 'educational pursuits')} this {period}."
        
        else:
            return f"Educational matters proceed steadily this {period}. Apply your natural {sun_sign} learning style and stay committed to knowledge acquisition."

    def _generate_overall_from_aspects(self, sun_sign: str, aspects: List[Dict], period: str) -> str:
        """Generate overall prediction from aspects"""
        if not aspects:
            return f"This {period} brings steady energy for {sun_sign} with no major planetary aspects affecting your sun sign."
        
        # Use different aspects based on period, fallback to strongest if none match
        target_aspect = None
        
        if period == 'daily':
            # Look for Moon or Mercury aspects first
            target_aspect = next((a for a in aspects if a['planet'] in ['Moon', 'Mercury']), aspects[0])
        elif period == 'weekly':
            # Look for Mercury or Venus aspects first  
            target_aspect = next((a for a in aspects if a['planet'] in ['Mercury', 'Venus']), aspects[0])
        elif period == 'monthly':
            # Look for Venus or Mars aspects first
            target_aspect = next((a for a in aspects if a['planet'] in ['Venus', 'Mars']), aspects[0])
        else:  # yearly
            # Look for Jupiter or Saturn aspects first
            target_aspect = next((a for a in aspects if a['planet'] in ['Jupiter', 'Saturn']), aspects[0])
        
        planet = target_aspect['planet']
        aspect_type = target_aspect['aspect']
        nature = target_aspect['nature']
        
        # Generate period-specific prediction
        if period == 'daily':
            if nature == 'harmonious':
                return f"Today's {planet} {aspect_type} brings immediate opportunities in {self._get_planet_themes(planet)['areas']}. Take action on fresh ideas."
            else:
                return f"Today's {planet} {aspect_type} requires careful navigation. Focus on patience in {self._get_planet_themes(planet)['areas']}."
        elif period == 'weekly':
            if nature == 'harmonious':
                return f"This week's {planet} {aspect_type} creates supportive energy for {self._get_planet_themes(planet)['areas']}. Plan important activities mid-week."
            else:
                return f"This week's {planet} {aspect_type} brings challenges requiring strategic thinking in {self._get_planet_themes(planet)['areas']}."
        elif period == 'monthly':
            if nature == 'harmonious':
                return f"This month's {planet} {aspect_type} supports long-term progress in {self._get_planet_themes(planet)['areas']}. Build lasting foundations."
            else:
                return f"This month's {planet} {aspect_type} presents obstacles that strengthen your resolve in {self._get_planet_themes(planet)['areas']}."
        else:  # yearly
            if nature == 'harmonious':
                return f"This year's {planet} {aspect_type} marks significant growth in {self._get_planet_themes(planet)['areas']}. Major developments unfold gradually."
            else:
                return f"This year's {planet} {aspect_type} brings transformative challenges in {self._get_planet_themes(planet)['areas']}. Embrace change as catalyst."

    def _get_planet_themes(self, planet: str) -> Dict:
        """Get thematic meanings for planets"""
        themes = {
            'Moon': {
                'positive': 'emotional clarity and intuitive insights',
                'areas': 'emotions, home, and family matters',
                'love': 'emotional connection and nurturing',
                'career': 'public relations and caring professions',
                'health': 'emotional well-being and digestive health',
                'finance': 'real estate and family resources'
            },
            'Mercury': {
                'positive': 'clear communication and mental agility',
                'areas': 'communication, learning, and short travels',
                'love': 'meaningful conversations and intellectual connection',
                'career': 'networking, writing, and skill development',
                'health': 'nervous system and mental clarity',
                'finance': 'business deals and quick transactions'
            },
            'Venus': {
                'positive': 'love, beauty, and harmonious relationships',
                'areas': 'relationships, art, and pleasure',
                'love': 'romance, attraction, and partnership harmony',
                'career': 'creative fields and collaborative projects',
                'health': 'beauty treatments and stress relief',
                'finance': 'luxury purchases and artistic investments'
            },
            'Mars': {
                'positive': 'dynamic action and courageous leadership',
                'areas': 'action, competition, and physical energy',
                'love': 'passion, desire, and taking romantic initiative',
                'career': 'leadership roles and competitive advantages',
                'health': 'physical fitness and energy levels',
                'finance': 'bold investments and entrepreneurial ventures'
            },
            'Jupiter': {
                'positive': 'expansion, wisdom, and good fortune',
                'areas': 'growth, education, and philosophical pursuits',
                'love': 'commitment, marriage, and spiritual connection',
                'career': 'advancement, teaching, and international opportunities',
                'health': 'overall vitality and healing',
                'finance': 'major investments and long-term prosperity'
            },
            'Saturn': {
                'positive': 'discipline, structure, and lasting achievements',
                'areas': 'responsibility, career, and long-term goals',
                'love': 'serious commitment and relationship maturity',
                'career': 'authority, recognition, and career milestones',
                'health': 'bone health and chronic condition management',
                'finance': 'savings, real estate, and retirement planning'
            }
        }
        
        return themes.get(planet, {
            'positive': 'personal growth and new experiences',
            'areas': 'life changes and transformation',
            'love': 'relationship evolution',
            'career': 'professional development',
            'health': 'wellness focus',
            'finance': 'financial planning'
        })

    def _generate_love_from_aspects(self, sun_sign: str, aspects: List[Dict], period: str) -> str:
        """Generate love prediction from aspects"""
        venus_aspects = [a for a in aspects if a['planet'] == 'Venus']
        mars_aspects = [a for a in aspects if a['planet'] == 'Mars']
        
        if venus_aspects:
            aspect = venus_aspects[0]
            themes = self._get_planet_themes('Venus')
            if aspect['nature'] == 'harmonious':
                return f"Venus's {aspect['aspect']} brings harmony to your love life, favoring {themes['love']}. This {period} is excellent for deepening bonds and attracting positive relationships."
            else:
                return f"Venus's challenging {aspect['aspect']} requires patience in relationships. Focus on communication and avoid making hasty romantic decisions this {period}."
        
        elif mars_aspects:
            aspect = mars_aspects[0]
            themes = self._get_planet_themes('Mars')
            if aspect['nature'] == 'harmonious':
                return f"Mars energizes your romantic sector with its {aspect['aspect']}, encouraging {themes['love']}. Take initiative in matters of the heart this {period}."
            else:
                return f"Mars's {aspect['aspect']} may create tension in relationships. Channel this energy constructively and avoid conflicts this {period}."
        
        else:
            return f"Love matters remain stable this {period} with no major planetary influences. Focus on nurturing existing relationships and being open to new connections."

    def _generate_career_from_aspects(self, sun_sign: str, aspects: List[Dict], period: str) -> str:
        """Generate career prediction from aspects"""
        career_planets = ['Mars', 'Jupiter', 'Saturn', 'Mercury']
        career_aspects = [a for a in aspects if a['planet'] in career_planets]
        
        if career_aspects:
            aspect = career_aspects[0]
            planet = aspect['planet']
            themes = self._get_planet_themes(planet)
            
            if aspect['nature'] == 'harmonious':
                return f"{planet}'s supportive {aspect['aspect']} enhances your professional life, bringing opportunities in {themes['career']}. This {period} favors career advancement and recognition."
            else:
                return f"{planet}'s challenging {aspect['aspect']} presents obstacles that ultimately strengthen your professional resolve. Focus on {themes['career']} this {period}."
        
        else:
            return f"Professional matters proceed steadily this {period}. Focus on consistent effort and building upon your existing {sun_sign} strengths in the workplace."

    def _generate_health_from_aspects(self, sun_sign: str, aspects: List[Dict], period: str) -> str:
        """Generate health prediction from aspects"""
        health_planets = ['Mars', 'Moon', 'Saturn']
        health_aspects = [a for a in aspects if a['planet'] in health_planets]
        
        if health_aspects:
            aspect = health_aspects[0]
            planet = aspect['planet']
            themes = self._get_planet_themes(planet)
            
            if aspect['nature'] == 'harmonious':
                return f"{planet}'s positive {aspect['aspect']} supports your well-being, particularly {themes['health']}. This {period} is favorable for health improvements and vitality."
            else:
                return f"{planet}'s {aspect['aspect']} suggests paying extra attention to {themes['health']}. Maintain healthy routines and avoid overexertion this {period}."
        
        else:
            return f"Health remains stable this {period}. Maintain your regular wellness routines and listen to your body's {sun_sign} natural rhythms."

    def _generate_finance_from_aspects(self, sun_sign: str, aspects: List[Dict], period: str) -> str:
        """Generate finance prediction from aspects"""
        money_planets = ['Jupiter', 'Venus', 'Saturn']
        money_aspects = [a for a in aspects if a['planet'] in money_planets]
        
        if money_aspects:
            aspect = money_aspects[0]
            planet = aspect['planet']
            themes = self._get_planet_themes(planet)
            
            if aspect['nature'] == 'harmonious':
                return f"{planet}'s favorable {aspect['aspect']} brings financial opportunities, particularly in {themes['finance']}. This {period} supports monetary growth and wise investments."
            else:
                return f"{planet}'s challenging {aspect['aspect']} requires careful financial planning. Avoid impulsive spending and focus on {themes['finance']} this {period}."
        
        else:
            return f"Financial matters remain steady this {period}. Apply your natural {sun_sign} approach to money management and avoid major financial risks."

    def _generate_universal_influences(self, planets: Dict) -> Dict:
        """Generate universal influences based on current planetary positions"""
        sun_sign = planets.get('Sun', {}).get('sign', 'Sagittarius')
        mercury_sign = planets.get('Mercury', {}).get('sign', 'Sagittarius')
        moon_longitude = planets.get('Moon', {}).get('longitude', 0)
        sun_longitude = planets.get('Sun', {}).get('longitude', 0)
        
        # Energy Focus based on Sun's current sign
        energy_themes = {
            'Aries': 'Dynamic Action and Leadership',
            'Taurus': 'Stability and Material Security', 
            'Gemini': 'Communication and Learning',
            'Cancer': 'Emotional Nurturing and Home',
            'Leo': 'Creative Expression and Recognition',
            'Virgo': 'Organization and Service',
            'Libra': 'Balance and Relationships',
            'Scorpio': 'Transformation and Deep Insights',
            'Sagittarius': 'Expansion and Higher Wisdom',
            'Capricorn': 'Achievement and Structure',
            'Aquarius': 'Innovation and Humanitarian Ideals',
            'Pisces': 'Intuition and Spiritual Connection'
        }
        
        # Key Theme based on Mercury's current sign
        themes = {
            'Aries': 'Pioneering New Ventures',
            'Taurus': 'Building Lasting Foundations',
            'Gemini': 'Connecting and Communicating',
            'Cancer': 'Nurturing Relationships',
            'Leo': 'Shining Your Authentic Light',
            'Virgo': 'Perfecting Your Craft',
            'Libra': 'Creating Harmony',
            'Scorpio': 'Embracing Transformation',
            'Sagittarius': 'Seeking Truth and Meaning',
            'Capricorn': 'Climbing Toward Success',
            'Aquarius': 'Revolutionary Thinking',
            'Pisces': 'Flowing with Divine Guidance'
        }
        
        # Lunar Phase calculation
        phase_angle = abs(moon_longitude - sun_longitude)
        if phase_angle > 180:
            phase_angle = 360 - phase_angle
            
        if phase_angle < 45:
            lunar_phase = "New Moon - New Beginnings and Fresh Intentions"
        elif phase_angle < 90:
            lunar_phase = "Waxing Crescent - Building Momentum and Taking Action"
        elif phase_angle < 135:
            lunar_phase = "First Quarter - Overcoming Challenges and Making Decisions"
        elif phase_angle < 180:
            lunar_phase = "Waxing Gibbous - Refinement and Preparation"
        else:
            lunar_phase = "Full Moon - Culmination and Manifestation"
        
        return {
            'energy_focus': energy_themes.get(sun_sign, 'Balanced Energy Flow'),
            'key_theme': themes.get(mercury_sign, 'Mindful Progress'),
            'lunar_phase': lunar_phase
        }

    def _format_detailed_analysis(self, aspects: List[Dict], planets: Dict) -> Dict:
        """Format detailed analysis with authentic calculations"""
        planetary_influences = []
        
        for aspect in aspects[:6]:  # Top 6 aspects
            planet_sign = planets.get(aspect['planet'], {}).get('sign', 'Aries')
            dignity = self._calculate_planetary_dignity(aspect['planet'], planet_sign)
            
            planetary_influences.append({
                'planet': aspect['planet'],
                'influence': f"{aspect['planet']} in {planet_sign} {aspect['aspect']} creates {aspect['nature']} {dignity['status']} energy",
                'strength': int(aspect['strength'] * 10),
                'sign': planet_sign,
                'aspect': aspect['aspect'].title(),
                'effect': self._get_specific_aspect_effect(aspect['planet'], aspect['aspect'], aspect['nature'], dignity),
                'orb': f"{aspect['orb']:.1f}°"
            })
        
        # Calculate real challenges and opportunities from aspects
        challenges = self._calculate_real_challenges(aspects, planets)
        opportunities = self._calculate_real_opportunities(aspects, planets)
        
        return {
            'planetary_influences': planetary_influences,
            'challenges': challenges,
            'opportunities': opportunities
        }

    def _calculate_lucky_color(self, sun_sign: str, aspects: List[Dict]) -> str:
        """Calculate lucky color based on strongest beneficial aspect"""
        if aspects:
            beneficial_aspects = [a for a in aspects if a['nature'] == 'harmonious']
            if beneficial_aspects:
                planet = beneficial_aspects[0]['planet']
                planet_colors = {
                    'Sun': 'Golden Yellow', 'Moon': 'Silver White', 'Mercury': 'Light Blue',
                    'Venus': 'Pink', 'Mars': 'Red', 'Jupiter': 'Royal Blue',
                    'Saturn': 'Dark Blue', 'Uranus': 'Electric Blue',
                    'Neptune': 'Sea Green', 'Pluto': 'Deep Purple'
                }
                return planet_colors.get(planet, 'White')
        
        # Default sun sign colors
        sign_colors = {
            'Aries': 'Red', 'Taurus': 'Green', 'Gemini': 'Yellow',
            'Cancer': 'Silver', 'Leo': 'Gold', 'Virgo': 'Navy Blue',
            'Libra': 'Pink', 'Scorpio': 'Maroon', 'Sagittarius': 'Purple',
            'Capricorn': 'Brown', 'Aquarius': 'Turquoise', 'Pisces': 'Sea Green'
        }
        return sign_colors.get(sun_sign, 'White')

    def _calculate_rating(self, aspects: List[Dict]) -> int:
        """Calculate overall rating based on aspect balance"""
        if not aspects:
            return 3
        
        harmonious_count = sum(1 for a in aspects if a['nature'] == 'harmonious')
        challenging_count = sum(1 for a in aspects if a['nature'] == 'challenging')
        
        if harmonious_count > challenging_count:
            return 5 if harmonious_count >= 3 else 4
        elif challenging_count > harmonious_count:
            return 2 if challenging_count >= 3 else 3
        else:
            return 3

    def _calculate_cosmic_weather(self, aspects: List[Dict]) -> Dict:
        """Calculate cosmic weather based on real planetary dignities and aspects"""
        if not aspects:
            return {
                'energy_level': 70,
                'manifestation_power': 70,
                'intuition_strength': 70,
                'relationship_harmony': 70
            }
        
        # Energy level based on Mars and Sun aspects
        energy_aspects = [a for a in aspects if a['planet'] in ['Mars', 'Sun']]
        energy_level = 60
        for aspect in energy_aspects:
            if aspect['nature'] == 'harmonious':
                energy_level += aspect['strength'] * 3
            else:
                energy_level += aspect['strength'] * 1.5  # Challenging aspects still add energy
        
        # Manifestation power based on Jupiter and Saturn aspects
        manifestation_aspects = [a for a in aspects if a['planet'] in ['Jupiter', 'Saturn']]
        manifestation_power = 60
        for aspect in manifestation_aspects:
            if aspect['nature'] == 'harmonious':
                manifestation_power += aspect['strength'] * 4
            else:
                manifestation_power -= aspect['strength'] * 2
        
        # Intuition strength based on Moon and Neptune aspects
        intuition_aspects = [a for a in aspects if a['planet'] in ['Moon', 'Neptune']]
        intuition_strength = 65
        for aspect in intuition_aspects:
            if aspect['nature'] == 'harmonious':
                intuition_strength += aspect['strength'] * 3.5
            else:
                intuition_strength += aspect['strength'] * 1  # Challenging aspects can enhance psychic sensitivity
        
        # Relationship harmony based on Venus aspects
        venus_aspects = [a for a in aspects if a['planet'] == 'Venus']
        relationship_harmony = 65
        for aspect in venus_aspects:
            if aspect['nature'] == 'harmonious':
                relationship_harmony += aspect['strength'] * 4
            else:
                relationship_harmony -= aspect['strength'] * 3
        
        return {
            'energy_level': min(100, max(20, int(energy_level))),
            'manifestation_power': min(100, max(20, int(manifestation_power))),
            'intuition_strength': min(100, max(20, int(intuition_strength))),
            'relationship_harmony': min(100, max(20, int(relationship_harmony)))
        }

    def _get_detailed_signs_to_watch(self, sign: str, aspects: List[Dict], planets: Dict, date: datetime) -> Dict:
        """Get detailed signs to watch with specific guidance on what to look for"""
        signs_to_watch = []
        
        # Moon sign (emotional/intuitive significance)
        moon_sign = planets.get('Moon', {}).get('sign', 'Aries')
        signs_to_watch.append({
            'sign': moon_sign,
            'reason': f'Moon in {moon_sign} heightens emotional awareness and intuitive insights',
            'what_to_watch': self._get_sign_watch_guidance(moon_sign, 'emotional'),
            'symbols': self._get_sign_symbols(moon_sign),
            'how_to_use': f'Trust your {moon_sign.lower()} instincts today - they\'re especially accurate'
        })
        
        # Signs of planets making strongest aspects to sun sign
        strongest_aspects = sorted(aspects, key=lambda x: x['strength'], reverse=True)[:2]
        for aspect in strongest_aspects:
            planet_sign = planets.get(aspect['planet'], {}).get('sign', 'Aries')
            if planet_sign not in [s['sign'] for s in signs_to_watch]:
                signs_to_watch.append({
                    'sign': planet_sign,
                    'reason': f'{aspect["planet"]} in {planet_sign} creates {aspect["aspect"]} energy affecting your day',
                    'what_to_watch': self._get_sign_watch_guidance(planet_sign, 'planetary'),
                    'symbols': self._get_sign_symbols(planet_sign),
                    'how_to_use': f'Channel {planet_sign.lower()} energy through {aspect["planet"].lower()} activities'
                })
        
        # Day ruler position
        weekday = date.weekday()
        day_rulers = {
            0: ('Moon', 'reflective and emotionally sensitive'),
            1: ('Mars', 'energetic and action-focused'),
            2: ('Mercury', 'communicative and mentally sharp'),
            3: ('Jupiter', 'optimistic and growth-oriented'),
            4: ('Venus', 'harmonious and relationship-centered'),
            5: ('Saturn', 'disciplined and structured'),
            6: ('Sun', 'confident and leadership-focused')
        }
        day_ruler, _ = day_rulers[weekday]
        ruler_sign = planets.get(day_ruler, {}).get('sign', 'Aries')
        if ruler_sign not in [s['sign'] for s in signs_to_watch]:
            signs_to_watch.append({
                'sign': ruler_sign,
                'reason': f'Today\'s ruler {day_ruler} in {ruler_sign} influences the day\'s overall energy',
                'what_to_watch': self._get_sign_watch_guidance(ruler_sign, 'daily'),
                'symbols': self._get_sign_symbols(ruler_sign),
                'how_to_use': f'Align your day with {ruler_sign.lower()} themes for best results'
            })
        
        return {
            'signs': signs_to_watch,
            'overview': 'Pay attention to these zodiac signs appearing in your environment, conversations, or decisions today',
            'methods': [
                'Notice people born under these signs - they may bring important messages',
                'Look for visual symbols, colors, or themes associated with these signs',
                'When making decisions, consider how these signs\' qualities might guide you',
                'Be aware of synchronicities involving these signs\' elements or animals'
            ]
        }

    def _get_sign_watch_guidance(self, sign: str, context: str) -> str:
        """Get specific guidance on what to watch for each sign"""
        guidance = {
            'Aries': {
                'emotional': 'Bold impulses and sudden urges to take action',
                'planetary': 'Leadership opportunities and competitive situations',
                'daily': 'New beginnings and pioneering initiatives'
            },
            'Taurus': {
                'emotional': 'Strong desires for comfort and security',
                'planetary': 'Financial opportunities and material pleasures',
                'daily': 'Steady progress and practical solutions'
            },
            'Gemini': {
                'emotional': 'Curiosity and need for mental stimulation',
                'planetary': 'Communication opportunities and learning moments',
                'daily': 'Information exchange and social connections'
            },
            'Cancer': {
                'emotional': 'Family concerns and nurturing instincts',
                'planetary': 'Home-related matters and emotional healing',
                'daily': 'Protective feelings and caring gestures'
            },
            'Leo': {
                'emotional': 'Creative inspiration and desire for recognition',
                'planetary': 'Performance opportunities and leadership roles',
                'daily': 'Dramatic moments and generous expressions'
            },
            'Virgo': {
                'emotional': 'Perfectionist tendencies and analytical thinking',
                'planetary': 'Organization opportunities and health matters',
                'daily': 'Detail-oriented tasks and service to others'
            },
            'Libra': {
                'emotional': 'Desire for harmony and relationship balance',
                'planetary': 'Partnership opportunities and aesthetic beauty',
                'daily': 'Diplomatic solutions and fair decisions'
            },
            'Scorpio': {
                'emotional': 'Intense feelings and transformative insights',
                'planetary': 'Deep research and psychological breakthroughs',
                'daily': 'Hidden truths and powerful transformations'
            },
            'Sagittarius': {
                'emotional': 'Wanderlust and philosophical questioning',
                'planetary': 'Travel opportunities and higher learning',
                'daily': 'Expansive thinking and truth-seeking moments'
            },
            'Capricorn': {
                'emotional': 'Ambition and long-term planning thoughts',
                'planetary': 'Career advancement and authority recognition',
                'daily': 'Structured approaches and goal achievement'
            },
            'Aquarius': {
                'emotional': 'Humanitarian impulses and innovative ideas',
                'planetary': 'Group activities and technological solutions',
                'daily': 'Unique perspectives and community involvement'
            },
            'Pisces': {
                'emotional': 'Intuitive hunches and compassionate feelings',
                'planetary': 'Spiritual experiences and artistic inspiration',
                'daily': 'Mystical moments and empathetic connections'
            }
        }
        
        return guidance.get(sign, {}).get(context, 'General awareness and openness')

    def _get_sign_symbols(self, sign: str) -> Dict:
        """Get visual symbols and themes for each sign"""
        symbols = {
            'Aries': {
                'animal': 'Ram',
                'colors': ['Red', 'Orange', 'Bright colors'],
                'symbols': ['Ram horns', 'Fire', 'Sharp objects'],
                'themes': ['Leadership', 'Competition', 'New beginnings']
            },
            'Taurus': {
                'animal': 'Bull',
                'colors': ['Green', 'Pink', 'Earth tones'],
                'symbols': ['Bull', 'Flowers', 'Money/coins'],
                'themes': ['Stability', 'Luxury', 'Nature']
            },
            'Gemini': {
                'animal': 'Twins',
                'colors': ['Yellow', 'Light blue', 'Silver'],
                'symbols': ['Twins', 'Books', 'Communication devices'],
                'themes': ['Communication', 'Duality', 'Learning']
            },
            'Cancer': {
                'animal': 'Crab',
                'colors': ['Silver', 'White', 'Sea blue'],
                'symbols': ['Crab', 'Moon', 'Home/family images'],
                'themes': ['Family', 'Emotions', 'Protection']
            },
            'Leo': {
                'animal': 'Lion',
                'colors': ['Gold', 'Orange', 'Bright yellow'],
                'symbols': ['Lion', 'Sun', 'Crown/royal symbols'],
                'themes': ['Creativity', 'Drama', 'Recognition']
            },
            'Virgo': {
                'animal': 'Maiden',
                'colors': ['Navy blue', 'Brown', 'Beige'],
                'symbols': ['Wheat', 'Tools', 'Health symbols'],
                'themes': ['Organization', 'Health', 'Service']
            },
            'Libra': {
                'animal': 'Scales',
                'colors': ['Pink', 'Light blue', 'Pastels'],
                'symbols': ['Scales', 'Hearts', 'Beautiful objects'],
                'themes': ['Balance', 'Beauty', 'Relationships']
            },
            'Scorpio': {
                'animal': 'Scorpion/Eagle',
                'colors': ['Deep red', 'Black', 'Maroon'],
                'symbols': ['Scorpion', 'Phoenix', 'Water'],
                'themes': ['Transformation', 'Mystery', 'Intensity']
            },
            'Sagittarius': {
                'animal': 'Centaur/Horse',
                'colors': ['Purple', 'Turquoise', 'Bright colors'],
                'symbols': ['Bow and arrow', 'Horse', 'Maps/globes'],
                'themes': ['Adventure', 'Philosophy', 'Freedom']
            },
            'Capricorn': {
                'animal': 'Goat',
                'colors': ['Brown', 'Black', 'Dark green'],
                'symbols': ['Mountain goat', 'Mountains', 'Business symbols'],
                'themes': ['Achievement', 'Structure', 'Authority']
            },
            'Aquarius': {
                'animal': 'Water bearer',
                'colors': ['Electric blue', 'Silver', 'Neon colors'],
                'symbols': ['Water waves', 'Lightning', 'Technology'],
                'themes': ['Innovation', 'Community', 'Future']
            },
            'Pisces': {
                'animal': 'Fish',
                'colors': ['Sea green', 'Purple', 'Iridescent'],
                'symbols': ['Fish', 'Water', 'Mystical symbols'],
                'themes': ['Spirituality', 'Dreams', 'Compassion']
            }
        }
        
        return symbols.get(sign, {
            'animal': 'Universal',
            'colors': ['White'],
            'symbols': ['General'],
            'themes': ['Balance']
        })

    def _calculate_planetary_dignity(self, planet: str, sign: str) -> Dict:
        """Calculate planetary dignity (exaltation, rulership, detriment, fall)"""
        # Traditional dignities
        rulerships = {
            'Sun': ['Leo'], 'Moon': ['Cancer'], 'Mercury': ['Gemini', 'Virgo'],
            'Venus': ['Taurus', 'Libra'], 'Mars': ['Aries', 'Scorpio'],
            'Jupiter': ['Sagittarius', 'Pisces'], 'Saturn': ['Capricorn', 'Aquarius']
        }
        
        exaltations = {
            'Sun': 'Aries', 'Moon': 'Taurus', 'Mercury': 'Virgo',
            'Venus': 'Pisces', 'Mars': 'Capricorn', 'Jupiter': 'Cancer', 'Saturn': 'Libra'
        }
        
        detriments = {
            'Sun': ['Aquarius'], 'Moon': ['Capricorn'], 'Mercury': ['Sagittarius', 'Pisces'],
            'Venus': ['Scorpio', 'Aries'], 'Mars': ['Libra', 'Taurus'],
            'Jupiter': ['Gemini', 'Virgo'], 'Saturn': ['Cancer', 'Leo']
        }
        
        falls = {
            'Sun': 'Libra', 'Moon': 'Scorpio', 'Mercury': 'Pisces',
            'Venus': 'Virgo', 'Mars': 'Cancer', 'Jupiter': 'Capricorn', 'Saturn': 'Aries'
        }
        
        if sign in rulerships.get(planet, []):
            return {'status': 'dignified', 'strength': 5, 'description': f'{planet} rules {sign}'}
        elif sign == exaltations.get(planet):
            return {'status': 'exalted', 'strength': 4, 'description': f'{planet} exalted in {sign}'}
        elif sign in detriments.get(planet, []):
            return {'status': 'weakened', 'strength': 2, 'description': f'{planet} in detriment in {sign}'}
        elif sign == falls.get(planet):
            return {'status': 'debilitated', 'strength': 1, 'description': f'{planet} in fall in {sign}'}
        else:
            return {'status': 'neutral', 'strength': 3, 'description': f'{planet} neutral in {sign}'}

    def _get_specific_aspect_effect(self, planet: str, aspect: str, nature: str, dignity: Dict) -> str:
        """Get specific effect based on planet, aspect, and dignity"""
        planet_functions = {
            'Sun': 'identity and vitality',
            'Moon': 'emotions and instincts',
            'Mercury': 'communication and thinking',
            'Venus': 'love and values',
            'Mars': 'action and desire',
            'Jupiter': 'growth and wisdom',
            'Saturn': 'structure and discipline',
            'Uranus': 'innovation and change',
            'Neptune': 'spirituality and dreams',
            'Pluto': 'transformation and power'
        }
        
        function = planet_functions.get(planet, 'personal development')
        
        if nature == 'harmonious':
            if dignity['strength'] >= 4:
                return f"Powerfully enhances {function} with {dignity['description']}"
            else:
                return f"Supports {function} despite {dignity['description']}"
        else:
            if dignity['strength'] >= 4:
                return f"Creates productive tension in {function} through {dignity['description']}"
            else:
                return f"Challenges {function} requiring patience with {dignity['description']}"

    def _calculate_real_challenges(self, aspects: List[Dict], planets: Dict) -> List[str]:
        """Calculate specific challenges based on actual aspects"""
        challenges = []
        
        # Check for specific challenging patterns
        challenging_aspects = [a for a in aspects if a['nature'] == 'challenging']
        
        for aspect in challenging_aspects[:3]:  # Top 3 challenges
            planet = aspect['planet']
            aspect_type = aspect['aspect']
            
            if planet == 'Saturn' and aspect_type in ['square', 'opposition']:
                challenges.append(f"Overcoming {planet.lower()} {aspect_type} restrictions requiring patience and discipline")
            elif planet == 'Mars' and aspect_type in ['square', 'opposition']:
                challenges.append(f"Managing {planet.lower()} {aspect_type} impulsive energy and potential conflicts")
            elif planet == 'Mercury' and aspect_type in ['square', 'opposition']:
                challenges.append(f"Navigating {planet.lower()} {aspect_type} communication misunderstandings")
            elif planet == 'Venus' and aspect_type in ['square', 'opposition']:
                challenges.append(f"Balancing {planet.lower()} {aspect_type} relationship and value conflicts")
            else:
                challenges.append(f"Working with {planet.lower()} {aspect_type} energy constructively")
        
        if not challenges:
            challenges.append("Maintaining balance during this harmonious period")
        
        return challenges

    def _calculate_real_opportunities(self, aspects: List[Dict], planets: Dict) -> List[str]:
        """Calculate specific opportunities based on actual aspects"""
        opportunities = []
        
        # Check for specific harmonious patterns
        harmonious_aspects = [a for a in aspects if a['nature'] == 'harmonious']
        
        for aspect in harmonious_aspects[:3]:  # Top 3 opportunities
            planet = aspect['planet']
            aspect_type = aspect['aspect']
            planet_sign = planets.get(planet, {}).get('sign', 'Aries')
            
            if planet == 'Jupiter':
                opportunities.append(f"Expand knowledge, travel, or teach others - Jupiter {aspect_type} in {planet_sign} brings growth")
            elif planet == 'Venus':
                opportunities.append(f"Strengthen relationships, create art, or beautify surroundings - Venus {aspect_type} in {planet_sign} attracts harmony")
            elif planet == 'Mercury':
                opportunities.append(f"Write, speak publicly, or learn new skills - Mercury {aspect_type} in {planet_sign} sharpens communication")
            elif planet == 'Mars':
                opportunities.append(f"Start new projects, exercise, or take leadership - Mars {aspect_type} in {planet_sign} energizes action")
            elif planet == 'Moon':
                opportunities.append(f"Trust intuition, nurture family, or process emotions - Moon {aspect_type} in {planet_sign} enhances feelings")
            elif planet == 'Sun':
                opportunities.append(f"Express creativity, seek recognition, or lead others - Sun {aspect_type} in {planet_sign} boosts confidence")
            elif planet == 'Saturn':
                opportunities.append(f"Build long-term structures, commit to goals, or gain authority - Saturn {aspect_type} in {planet_sign} rewards discipline")
            else:
                opportunities.append(f"Channel {planet.lower()} energy constructively - {aspect_type} in {planet_sign} offers support")
        
        # If no harmonious aspects, find constructive uses of challenging ones
        if not opportunities:
            challenging_aspects = [a for a in aspects if a['nature'] == 'challenging'][:2]
            for aspect in challenging_aspects:
                planet = aspect['planet']
                planet_sign = planets.get(planet, {}).get('sign', 'Aries')
                
                if planet == 'Saturn':
                    opportunities.append(f"Develop patience and discipline - Saturn {aspect['aspect']} in {planet_sign} builds character")
                elif planet == 'Mars':
                    opportunities.append(f"Channel energy into physical activity - Mars {aspect['aspect']} in {planet_sign} needs outlet")
                else:
                    opportunities.append(f"Transform challenges into strength - {planet} {aspect['aspect']} in {planet_sign} teaches resilience")
        
        # Final fallback with specific guidance
        if not opportunities:
            opportunities.append("Focus on personal growth and self-reflection during this introspective period")
        
        return opportunities

    def _calculate_personalized_action_plan(self, sun_sign: str, aspects: List[Dict], planets: Dict, date: datetime) -> Dict:
        """Calculate authentic personalized action plan based on real planetary data"""
        
        # Primary focus based on strongest aspect
        strongest_aspect = aspects[0] if aspects else None
        primary_focus = self._get_primary_focus(sun_sign, strongest_aspect, planets)
        
        # Optimal timing based on planetary hours and day ruler
        optimal_timing = self._calculate_optimal_timing(sun_sign, planets, date)
        
        # Daily practices based on planetary dignities and aspects
        daily_practices = self._calculate_daily_practices(sun_sign, aspects, planets, date)
        
        # Growth opportunities from harmonious aspects
        growth_opportunities = self._calculate_growth_opportunities(aspects, planets, sun_sign)
        
        # Balance strategies from challenging aspects
        balance_strategies = self._calculate_balance_strategies(aspects, planets)
        
        # Manifestation techniques based on current lunar phase
        manifestation_techniques = self._calculate_manifestation_techniques(planets, date, sun_sign)
        
        return {
            'primary_focus': primary_focus,
            'optimal_timing': optimal_timing,
            'daily_practices': daily_practices,
            'growth_opportunities': growth_opportunities,
            'balance_strategies': balance_strategies,
            'manifestation_techniques': manifestation_techniques
        }

    def _get_primary_focus(self, sun_sign: str, strongest_aspect: Dict, planets: Dict) -> str:
        """Get primary focus based on strongest planetary aspect"""
        if not strongest_aspect:
            sign_focuses = {
                'Aries': 'Initiate bold new projects and lead with confidence',
                'Taurus': 'Build stable foundations and cultivate material security',
                'Gemini': 'Enhance communication skills and expand knowledge networks',
                'Cancer': 'Nurture family relationships and create emotional security',
                'Leo': 'Express creative talents and seek recognition for achievements',
                'Virgo': 'Perfect skills through detailed analysis and practical service',
                'Libra': 'Create harmony in relationships and beautify surroundings',
                'Scorpio': 'Transform deep patterns and investigate hidden truths',
                'Sagittarius': 'Expand horizons through learning and philosophical exploration',
                'Capricorn': 'Build authority and achieve long-term ambitious goals',
                'Aquarius': 'Innovate solutions and contribute to community progress',
                'Pisces': 'Develop intuitive abilities and practice compassionate service'
            }
            return sign_focuses.get(sun_sign, 'Focus on authentic self-expression')
        
        planet = strongest_aspect['planet']
        aspect_type = strongest_aspect['aspect']
        nature = strongest_aspect['nature']
        planet_sign = planets.get(planet, {}).get('sign', 'Aries')
        
        if planet == 'Jupiter':
            if nature == 'harmonious':
                return f'Expand knowledge and teaching abilities - Jupiter {aspect_type} in {planet_sign} opens doors to wisdom'
            else:
                return f'Avoid overconfidence and excessive optimism - Jupiter {aspect_type} in {planet_sign} requires moderation'
        elif planet == 'Saturn':
            if nature == 'harmonious':
                return f'Build lasting structures and commit to long-term goals - Saturn {aspect_type} in {planet_sign} rewards discipline'
            else:
                return f'Develop patience and work through limitations - Saturn {aspect_type} in {planet_sign} teaches perseverance'
        elif planet == 'Mars':
            if nature == 'harmonious':
                return f'Take decisive action and lead initiatives - Mars {aspect_type} in {planet_sign} energizes progress'
            else:
                return f'Channel aggressive energy constructively - Mars {aspect_type} in {planet_sign} needs physical outlet'
        elif planet == 'Venus':
            if nature == 'harmonious':
                return f'Strengthen relationships and create beauty - Venus {aspect_type} in {planet_sign} attracts harmony'
            else:
                return f'Resolve relationship conflicts and reassess values - Venus {aspect_type} in {planet_sign} requires balance'
        elif planet == 'Mercury':
            if nature == 'harmonious':
                return f'Improve communication and learn new skills - Mercury {aspect_type} in {planet_sign} sharpens mind'
            else:
                return f'Clarify misunderstandings and think before speaking - Mercury {aspect_type} in {planet_sign} needs careful words'
        else:
            return f'Work with {planet.lower()} energy in {planet_sign} through {aspect_type} aspect'

    def _calculate_optimal_timing(self, sun_sign: str, planets: Dict, date: datetime) -> str:
        """Calculate optimal timing personalized for sun sign"""
        weekday = date.weekday()
        day_rulers = {0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Sun'}
        day_ruler = day_rulers[weekday]
        
        # Get sun sign's ruling planet and element
        sun_ruler = self.traditional_rulers.get(sun_sign, 'Sun')
        sun_element = self._get_sign_element(sun_sign)
        day_ruler_element = self._get_planet_element(day_ruler)
        
        # Sign-specific optimal timing based on natural rhythms
        sign_timing = {
            'Aries': f'{day_ruler} day: Best for Aries during early morning (5-9 AM) when Mars energy peaks. Take bold action before others wake up.',
            'Taurus': f'{day_ruler} day: Best for Taurus during mid-morning (9 AM-12 PM) when steady earth energy builds. Focus on practical tasks.',
            'Gemini': f'{day_ruler} day: Best for Gemini during late morning (10 AM-1 PM) when mental clarity peaks. Schedule important communications.',
            'Cancer': f'{day_ruler} day: Best for Cancer during evening hours (6-9 PM) when Moon energy strengthens. Trust emotional instincts.',
            'Leo': f'{day_ruler} day: Best for Leo during midday (11 AM-2 PM) when Sun energy dominates. Showcase talents and lead meetings.',
            'Virgo': f'{day_ruler} day: Best for Virgo during afternoon (1-4 PM) when analytical powers peak. Perfect details and organize.',
            'Libra': f'{day_ruler} day: Best for Libra during late afternoon (3-6 PM) when Venus energy flows. Focus on relationships and beauty.',
            'Scorpio': f'{day_ruler} day: Best for Scorpio during late evening (8-11 PM) when transformative energy deepens. Research and investigate.',
            'Sagittarius': f'{day_ruler} day: Best for Sagittarius during morning (8-11 AM) when Jupiter expansion energy flows. Plan adventures and learning.',
            'Capricorn': f'{day_ruler} day: Best for Capricorn during business hours (9 AM-5 PM) when Saturn structure supports. Build authority and achieve goals.',
            'Aquarius': f'{day_ruler} day: Best for Aquarius during unconventional hours (11 PM-2 AM) when innovative energy flows. Think outside the box.',
            'Pisces': f'{day_ruler} day: Best for Pisces during dawn/dusk (6-8 AM or 6-8 PM) when mystical veils thin. Trust intuition and create.'
        }
        
        base_timing = sign_timing.get(sun_sign, f'{day_ruler} day: Follow your natural {sun_sign} rhythms.')
        
        # Add day ruler compatibility
        if day_ruler == sun_ruler:
            return f"{base_timing} PERFECT ALIGNMENT: {day_ruler} rules both the day and your {sun_sign} nature."
        elif self._elements_compatible(sun_element, day_ruler_element):
            return f"{base_timing} SUPPORTIVE: {day_ruler} {day_ruler_element} energy harmonizes with your {sun_sign} {sun_element} nature."
        else:
            return f"{base_timing} ADAPTIVE: {day_ruler} {day_ruler_element} energy requires adjustment to your {sun_sign} {sun_element} style."

    def _calculate_daily_practices(self, sun_sign: str, aspects: List[Dict], planets: Dict, date: datetime) -> str:
        """Calculate daily practices based on authentic planetary dignities and traditional remedies"""
        practices = []
        
        # Get day ruler and its dignity
        weekday = date.weekday()
        day_rulers = {0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Sun'}
        day_ruler = day_rulers[weekday]
        day_ruler_sign = planets.get(day_ruler, {}).get('sign', 'Aries')
        dignity = self._calculate_planetary_dignity(day_ruler, day_ruler_sign)
        
        # Traditional practices based on planetary dignity status
        if dignity['status'] == 'exalted':
            practices.append(f'Maximize {day_ruler.lower()} activities - {dignity["description"]} brings exceptional power')
        elif dignity['status'] == 'dignified':
            practices.append(f'Focus on {day_ruler.lower()} work - {dignity["description"]} supports natural expression')
        elif dignity['status'] == 'weakened':
            practices.append(f'Support {day_ruler.lower()} through remedial practices - {dignity["description"]} needs assistance')
        elif dignity['status'] == 'debilitated':
            practices.append(f'Gentle {day_ruler.lower()} activities only - {dignity["description"]} requires careful handling')
        else:
            practices.append(f'Balanced {day_ruler.lower()} expression - {dignity["description"]} allows steady progress')
        
        # Add traditional remedial practice for challenging aspects
        challenging_aspects = [a for a in aspects if a['nature'] == 'challenging']
        if challenging_aspects:
            strongest_challenge = challenging_aspects[0]
            planet = strongest_challenge['planet']
            aspect_type = strongest_challenge['aspect']
            planet_sign = planets.get(planet, {}).get('sign', 'Aries')
            
            if planet == 'Saturn':
                practices.append(f'Offer service to elders to appease Saturn {aspect_type} in {planet_sign}')
            elif planet == 'Mars':
                practices.append(f'Channel Mars {aspect_type} in {planet_sign} through physical discipline')
            elif planet == 'Mercury':
                practices.append(f'Practice clear speech to balance Mercury {aspect_type} in {planet_sign}')
            elif planet == 'Venus':
                practices.append(f'Cultivate beauty and harmony to soothe Venus {aspect_type} in {planet_sign}')
        
        # Traditional color therapy based on planetary dignity
        lucky_color = self._calculate_lucky_color(sun_sign, aspects)
        if dignity['strength'] >= 4:
            practices.append(f'Wear {lucky_color.lower()} to enhance {day_ruler} power in {day_ruler_sign}')
        else:
            practices.append(f'Meditate on {lucky_color.lower()} light to strengthen {day_ruler} in {day_ruler_sign}')
        
        return '. '.join(practices) + '.'

    def _calculate_growth_opportunities(self, aspects: List[Dict], planets: Dict, sun_sign: str) -> str:
        """Calculate growth opportunities personalized for sun sign"""
        # Always provide sign-specific growth opportunities regardless of aspects
        sign_growth = {
            'Aries': 'Leadership Development: Start a new project, mentor someone junior, or take charge of a team initiative. Your pioneering spirit opens doors.',
            'Taurus': 'Practical Skill Building: Learn a craft, invest in property, or develop expertise in luxury goods. Your persistence creates lasting value.',
            'Gemini': 'Communication Mastery: Write articles, start a podcast, or become a social media influencer. Your versatility attracts diverse opportunities.',
            'Cancer': 'Emotional Intelligence: Develop counseling skills, strengthen family bonds, or create nurturing spaces. Your empathy heals others.',
            'Leo': 'Creative Expression: Perform publicly, build your personal brand, or teach creative skills. Your charisma magnetizes recognition.',
            'Virgo': 'Service Excellence: Perfect a specialized skill, organize systems, or provide health services. Your attention to detail creates perfection.',
            'Libra': 'Relationship Building: Mediate conflicts, create beautiful partnerships, or study diplomacy. Your harmony-seeking nature brings peace.',
            'Scorpio': 'Transformation Mastery: Research psychology, facilitate healing, or investigate mysteries. Your depth reveals hidden truths.',
            'Sagittarius': 'Wisdom Expansion: Travel internationally, study philosophy, or teach higher concepts. Your quest for truth inspires others.',
            'Capricorn': 'Authority Building: Climb corporate ladder, start a business, or gain professional credentials. Your ambition achieves lasting success.',
            'Aquarius': 'Innovation Leadership: Develop new technology, lead humanitarian causes, or revolutionize systems. Your vision changes the world.',
            'Pisces': 'Spiritual Service: Develop healing abilities, create inspirational art, or practice compassionate service. Your intuition guides others.'
        }
        
        base_opportunity = sign_growth.get(sun_sign, 'Focus on authentic self-development')
        
        # Add planetary enhancement if harmonious aspects exist
        harmonious_aspects = [a for a in aspects if a['nature'] == 'harmonious']
        if harmonious_aspects:
            strongest_planet = harmonious_aspects[0]['planet']
            planet_sign = planets.get(strongest_planet, {}).get('sign', 'Aries')
            
            planet_benefits = {
                'Jupiter': f'ENHANCED by Jupiter in {planet_sign}: Opportunities multiply and expand beyond expectations.',
                'Venus': f'ENHANCED by Venus in {planet_sign}: Attracts partnerships and resources that beautify your path.',
                'Mars': f'ENHANCED by Mars in {planet_sign}: Energizes action and competitive advantages.',
                'Mercury': f'ENHANCED by Mercury in {planet_sign}: Improves communication and learning speed.',
                'Moon': f'ENHANCED by Moon in {planet_sign}: Heightens intuition and emotional intelligence.',
                'Sun': f'ENHANCED by Sun in {planet_sign}: Boosts confidence and leadership recognition.',
                'Saturn': f'ENHANCED by Saturn in {planet_sign}: Builds lasting structures and authority.'
            }
            
            enhancement = planet_benefits.get(strongest_planet, f'ENHANCED by {strongest_planet} in {planet_sign}: Adds supportive energy.')
            return f'{base_opportunity} {enhancement}'
        
        return base_opportunity

    def _calculate_balance_strategies(self, aspects: List[Dict], planets: Dict) -> str:
        """Calculate balance strategies from challenging aspects"""
        challenging_aspects = [a for a in aspects if a['nature'] == 'challenging']
        
        if not challenging_aspects:
            return 'Maintain current equilibrium and avoid major disruptions to established routines'
        
        strategies = []
        for aspect in challenging_aspects[:2]:  # Top 2 challenges
            planet = aspect['planet']
            aspect_type = aspect['aspect']
            planet_sign = planets.get(planet, {}).get('sign', 'Aries')
            
            if planet == 'Saturn':
                strategies.append(f'Create structured schedules to handle Saturn {aspect_type} in {planet_sign} restrictions')
            elif planet == 'Mars':
                strategies.append(f'Use physical exercise to balance Mars {aspect_type} in {planet_sign} tension')
            elif planet == 'Mercury':
                strategies.append(f'Double-check communications to avoid Mercury {aspect_type} in {planet_sign} misunderstandings')
            elif planet == 'Venus':
                strategies.append(f'Practice compromise in relationships during Venus {aspect_type} in {planet_sign}')
            else:
                strategies.append(f'Find constructive outlets for {planet.lower()} {aspect_type} energy in {planet_sign}')
        
        return '. '.join(strategies) + '.'

    def _store_aspects_for_timing(self, aspects: List[Dict]):
        """Store aspects for use in timing calculations"""
        self._current_aspects = aspects

    def _calculate_manifestation_techniques(self, planets: Dict, date: datetime, sun_sign: str) -> str:
        """Calculate manifestation techniques personalized for sun sign"""
        moon_data = planets.get('Moon', {})
        sun_data = planets.get('Sun', {})
        
        # Calculate precise lunar phase
        moon_longitude = moon_data.get('longitude', 0)
        sun_longitude = sun_data.get('longitude', 0)
        phase_angle = (moon_longitude - sun_longitude) % 360
        moon_sign = moon_data.get('sign', 'Aries')
        
        # Sign-specific manifestation approaches
        sign_manifestation = {
            'Aries': {
                'focus': 'Bold Leadership Goals',
                'method': 'Write goals on red paper, visualize taking immediate action, use fire ceremonies',
                'timing': 'Manifest during sunrise when Mars energy peaks'
            },
            'Taurus': {
                'focus': 'Material Security & Luxury',
                'method': 'Create vision boards with tangible items, use earth elements, plant seeds literally',
                'timing': 'Manifest during spring when Venus energy blooms'
            },
            'Gemini': {
                'focus': 'Communication & Learning Mastery',
                'method': 'Write affirmations, speak goals aloud, use yellow candles, journal extensively',
                'timing': 'Manifest during Mercury hours (Wednesday mornings)'
            },
            'Cancer': {
                'focus': 'Family Harmony & Emotional Security',
                'method': 'Use water rituals, moonlight meditation, family photos in manifestation space',
                'timing': 'Manifest during full moons when lunar energy peaks'
            },
            'Leo': {
                'focus': 'Creative Recognition & Personal Glory',
                'method': 'Perform manifestation rituals, use gold items, visualize applause and recognition',
                'timing': 'Manifest at noon when Sun energy dominates'
            },
            'Virgo': {
                'focus': 'Perfect Service & Health Mastery',
                'method': 'Create detailed manifestation plans, use herbs, organize sacred space perfectly',
                'timing': 'Manifest during harvest season when earth energy matures'
            },
            'Libra': {
                'focus': 'Beautiful Partnerships & Harmony',
                'method': 'Use pink candles, create balanced altar, manifest with partner, use rose quartz',
                'timing': 'Manifest during Venus hours (Friday evenings)'
            },
            'Scorpio': {
                'focus': 'Deep Transformation & Hidden Power',
                'method': 'Use intense visualization, dark moon rituals, transform fears into power',
                'timing': 'Manifest during dark moon when transformative energy peaks'
            },
            'Sagittarius': {
                'focus': 'Wisdom Expansion & Adventure',
                'method': 'Use purple candles, manifest while traveling, study sacred texts, aim high',
                'timing': 'Manifest during Jupiter hours (Thursday mornings)'
            },
            'Capricorn': {
                'focus': 'Authority Achievement & Legacy Building',
                'method': 'Create structured manifestation timeline, use mountain imagery, build altars',
                'timing': 'Manifest during winter solstice when Saturn energy structures'
            },
            'Aquarius': {
                'focus': 'Innovation & Humanitarian Impact',
                'method': 'Use technology in manifestation, group ceremonies, electric blue colors',
                'timing': 'Manifest during new moon when innovative energy flows'
            },
            'Pisces': {
                'focus': 'Spiritual Connection & Compassionate Service',
                'method': 'Use water ceremonies, dream manifestation, meditation, sea green colors',
                'timing': 'Manifest during dawn/dusk when mystical veils thin'
            }
        }
        
        sign_info = sign_manifestation.get(sun_sign, {
            'focus': 'Authentic Self-Expression',
            'method': 'Follow your natural intuition',
            'timing': 'Trust your inner timing'
        })
        
        # Add lunar phase guidance
        if phase_angle < 90:  # New/Waxing
            phase_guidance = f'PLANTING PHASE: Perfect time to begin manifesting {sign_info["focus"]}. {sign_info["method"]}. {sign_info["timing"]}.'
        elif phase_angle < 180:  # Full Moon approaching
            phase_guidance = f'BUILDING PHASE: Intensify manifestation of {sign_info["focus"]}. {sign_info["method"]}. {sign_info["timing"]}.'
        elif phase_angle < 270:  # Full Moon
            phase_guidance = f'HARVEST PHASE: Celebrate manifestation of {sign_info["focus"]}. {sign_info["method"]}. {sign_info["timing"]}.'
        else:  # Waning
            phase_guidance = f'RELEASE PHASE: Clear blocks to {sign_info["focus"]}. {sign_info["method"]}. {sign_info["timing"]}.'
        
        return f'Moon in {moon_sign}: {phase_guidance}'

    def _get_sign_element(self, sign: str) -> str:
        """Get element for zodiac sign"""
        elements = {
            'Aries': 'fire', 'Leo': 'fire', 'Sagittarius': 'fire',
            'Taurus': 'earth', 'Virgo': 'earth', 'Capricorn': 'earth',
            'Gemini': 'air', 'Libra': 'air', 'Aquarius': 'air',
            'Cancer': 'water', 'Scorpio': 'water', 'Pisces': 'water'
        }
        return elements.get(sign, 'fire')
    
    def _get_planet_element(self, planet: str) -> str:
        """Get element for planet"""
        planet_elements = {
            'Sun': 'fire', 'Mars': 'fire',
            'Moon': 'water', 'Venus': 'water',
            'Mercury': 'air', 'Jupiter': 'air',
            'Saturn': 'earth'
        }
        return planet_elements.get(planet, 'fire')
    
    def _elements_compatible(self, element1: str, element2: str) -> bool:
        """Check if two elements are compatible"""
        compatible_pairs = [
            ('fire', 'air'), ('air', 'fire'),
            ('earth', 'water'), ('water', 'earth')
        ]
        return (element1, element2) in compatible_pairs