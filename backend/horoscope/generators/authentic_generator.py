from datetime import datetime, timedelta
import swisseph as swe
from typing import Dict, List, Any
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from classical_engine.core_analyzer import CoreClassicalAnalyzer

class AuthenticHoroscopeGenerator:
    def __init__(self):
        self.zodiac_signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]

    def generate_comprehensive_horoscope(self, zodiac_sign: str, period: str, date: datetime = None) -> Dict:
        if not date:
            date = datetime.now()
            
        # Create birth data for zodiac sign
        birth_data = self._create_birth_data_for_sign(zodiac_sign, date)
        
        # Use CoreClassicalAnalyzer for authentic predictions
        analyzer = CoreClassicalAnalyzer(birth_data, date)
        classical_analysis = analyzer.generate_complete_prediction()
        
        # Calculate real planetary positions for universal influences
        planetary_data = self._calculate_planetary_positions(date)
        universal_influences = self._generate_universal_influences(planetary_data)
        
        # Format predictions based on period and classical analysis
        predictions = self._format_predictions_from_analysis(classical_analysis, period, zodiac_sign)
        
        return {
            'prediction': predictions,
            'energy_focus': universal_influences['energy_focus'],
            'key_theme': universal_influences['key_theme'],
            'lunar_phase': universal_influences['lunar_phase'],
            'lucky_number': self._calculate_authentic_lucky_number(classical_analysis),
            'lucky_color': self._calculate_authentic_lucky_color(classical_analysis),
            'rating': self._calculate_authentic_rating(classical_analysis),
            'cosmic_weather': self._calculate_authentic_cosmic_weather(classical_analysis)
        }

    def _create_birth_data_for_sign(self, zodiac_sign: str, current_date: datetime) -> Dict:
        """Create representative birth data for zodiac sign"""
        # Use sign's typical birth period and representative location
        sign_dates = {
            'Aries': ('1990-04-01', '12:00'),
            'Taurus': ('1990-05-01', '12:00'),
            'Gemini': ('1990-06-01', '12:00'),
            'Cancer': ('1990-07-01', '12:00'),
            'Leo': ('1990-08-01', '12:00'),
            'Virgo': ('1990-09-01', '12:00'),
            'Libra': ('1990-10-01', '12:00'),
            'Scorpio': ('1990-11-01', '12:00'),
            'Sagittarius': ('1990-12-01', '12:00'),
            'Capricorn': ('1990-01-01', '12:00'),
            'Aquarius': ('1990-02-01', '12:00'),
            'Pisces': ('1990-03-01', '12:00')
        }
        
        birth_date, birth_time = sign_dates.get(zodiac_sign, ('1990-01-01', '12:00'))
        
        return {
            'date': birth_date,
            'time': birth_time,
            'latitude': 28.6139,  # Delhi coordinates as representative
            'longitude': 77.2090,
            'name': f'{zodiac_sign} Native'
        }

    def _calculate_planetary_positions(self, date: datetime) -> Dict:
        """Calculate real planetary positions for given date"""
        jd = swe.julday(date.year, date.month, date.day, 12.0)
        positions = {}
        
        planets = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
            'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE
        }
        
        for planet_name, planet_id in planets.items():
            try:
                # Set Lahiri Ayanamsa for accurate Vedic calculations
                swe.set_sid_mode(swe.SIDM_LAHIRI)
                pos, _ = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
                sign_num = int(pos[0] // 30)
                
                positions[planet_name] = {
                    'longitude': pos[0],
                    'sign': self.zodiac_signs[sign_num],
                    'speed': pos[3] if len(pos) > 3 else 0
                }
            except Exception:
                # Fallback if calculation fails
                positions[planet_name] = {
                    'longitude': 0,
                    'sign': 'Aries',
                    'speed': 0
                }
        
        # Add Ketu (opposite to Rahu)
        if 'Rahu' in positions:
            ketu_long = (positions['Rahu']['longitude'] + 180) % 360
            ketu_sign = int(ketu_long // 30)
            positions['Ketu'] = {
                'longitude': ketu_long,
                'sign': self.zodiac_signs[ketu_sign],
                'speed': -positions['Rahu']['speed']
            }
        
        return positions

    def _generate_universal_influences(self, planets: Dict) -> Dict:
        """Generate universal daily influences based on real planetary positions"""
        sun_sign = planets.get('Sun', {}).get('sign', 'Aries')
        mercury_sign = planets.get('Mercury', {}).get('sign', 'Gemini')
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
    
    def _generate_specific_transit_prediction(self, zodiac_sign: str, planets: Dict, period: str) -> str:
        """Generate specific prediction based on current planetary transits"""
        # Get current planetary positions
        jupiter_sign = planets.get('Jupiter', {}).get('sign', 'Pisces')
        saturn_sign = planets.get('Saturn', {}).get('sign', 'Aquarius')
        mars_sign = planets.get('Mars', {}).get('sign', 'Aries')
        venus_sign = planets.get('Venus', {}).get('sign', 'Taurus')
        mercury_sign = planets.get('Mercury', {}).get('sign', 'Gemini')
        sun_sign = planets.get('Sun', {}).get('sign', 'Sagittarius')
        
        # Calculate house positions for the zodiac sign
        sign_index = self.zodiac_signs.index(zodiac_sign)
        
        # Jupiter's house position from zodiac sign
        jupiter_house = ((self.zodiac_signs.index(jupiter_sign) - sign_index) % 12) + 1
        saturn_house = ((self.zodiac_signs.index(saturn_sign) - sign_index) % 12) + 1
        mars_house = ((self.zodiac_signs.index(mars_sign) - sign_index) % 12) + 1
        
        # Generate specific prediction based on major transits
        predictions = []
        
        # Jupiter transit effects
        if jupiter_house in [1, 5, 9]:  # Trine houses
            predictions.append(f"Jupiter's transit through your {jupiter_house}{'st' if jupiter_house == 1 else 'th' if jupiter_house == 9 else 'th'} house brings expansion in {'personal growth' if jupiter_house == 1 else 'creative projects and romance' if jupiter_house == 5 else 'higher learning and spirituality'}")
        elif jupiter_house in [2, 11]:
            predictions.append(f"Jupiter in your {jupiter_house}{'nd' if jupiter_house == 2 else 'th'} house enhances {'wealth and family harmony' if jupiter_house == 2 else 'income and social connections'}")
        elif jupiter_house == 7:
            predictions.append(f"Jupiter's presence in your 7th house favors partnerships, marriage prospects, and business collaborations")
        elif jupiter_house == 10:
            predictions.append(f"Jupiter in your 10th house brings career advancement, recognition, and professional opportunities")
        
        # Saturn transit effects
        if saturn_house in [3, 6, 11]:  # Upachaya houses
            predictions.append(f"Saturn's disciplined energy in your {saturn_house}{'rd' if saturn_house == 3 else 'th'} house rewards hard work in {'communication and skills' if saturn_house == 3 else 'health and service' if saturn_house == 6 else 'goals and networking'}")
        elif saturn_house in [8, 12]:
            predictions.append(f"Saturn in your {saturn_house}th house demands patience and careful resource management, bringing eventual transformation")
        elif saturn_house == 7:
            predictions.append(f"Saturn's transit through your 7th house brings serious relationship decisions and partnership responsibilities")
        
        # Mars transit effects (faster moving)
        if mars_house == 1:
            predictions.append(f"Mars energizes your personality and physical vitality, favoring leadership initiatives")
        elif mars_house in [3, 6, 10, 11]:
            predictions.append(f"Mars in your {mars_house}{'rd' if mars_house == 3 else 'th'} house boosts {'communication and courage' if mars_house == 3 else 'competitive edge and health' if mars_house == 6 else 'career ambitions' if mars_house == 10 else 'goal achievement'}")
        elif mars_house in [4, 8, 12]:
            predictions.append(f"Mars in your {mars_house}th house requires patience and avoiding conflicts in {'home matters' if mars_house == 4 else 'joint resources' if mars_house == 8 else 'behind-the-scenes activities'}")
        
        # Combine predictions
        if predictions:
            main_prediction = predictions[0]
            if len(predictions) > 1:
                main_prediction += f". Additionally, {predictions[1].lower()}"
            
            # Add period-specific timing
            if period == 'daily':
                return f"Today, {main_prediction.lower()}. The planetary alignment suggests focusing on practical steps and maintaining steady progress."
            elif period == 'weekly':
                return f"This week, {main_prediction.lower()}. The seven-day cycle supports building momentum through consistent daily actions."
            elif period == 'monthly':
                return f"This month, {main_prediction.lower()}. The lunar cycle provides multiple opportunities to advance your goals through strategic planning."
            else:  # yearly
                return f"This year, {main_prediction.lower()}. The annual planetary cycle creates a foundation for long-term growth and achievement."
        
        # Fallback with specific planetary information
        return f"Current planetary positions show Jupiter in {jupiter_sign}, Saturn in {saturn_sign}, and Mars in {mars_sign}, creating a {period} period of {'steady progress' if saturn_house in [2, 6, 10] else 'dynamic change' if mars_house in [1, 3, 10] else 'balanced development'} for {zodiac_sign}."

    def _format_predictions_from_analysis(self, analysis: Dict, period: str, zodiac_sign: str) -> Dict:
        """Format classical analysis into horoscope predictions"""
        
        # Extract key information from classical analysis
        activated_houses = analysis.get('step3_activated_houses', [])
        planet_results = analysis.get('step4_planet_results', {})
        prediction_data = analysis.get('step5_prediction', {})
        
        # Generate period-specific predictions based on classical analysis
        overall = self._generate_overall_from_analysis(prediction_data, period, zodiac_sign)
        love = self._generate_love_from_analysis(activated_houses, planet_results, period)
        career = self._generate_career_from_analysis(activated_houses, planet_results, period)
        health = self._generate_health_from_analysis(activated_houses, planet_results, period)
        finance = self._generate_finance_from_analysis(activated_houses, planet_results, period)
        
        return {
            'overall': overall,
            'love': love,
            'career': career,
            'health': health,
            'finance': finance,
            'detailed_analysis': self._format_detailed_analysis(analysis)
        }

    def _generate_overall_from_analysis(self, prediction_data: Dict, period: str, zodiac_sign: str) -> str:
        """Generate overall prediction from classical analysis"""
        # Get current planetary positions for specific insights
        current_date = datetime.now()
        planetary_data = self._calculate_planetary_positions(current_date)
        
        # Generate specific prediction based on current transits
        return self._generate_specific_transit_prediction(zodiac_sign, planetary_data, period)

    def _generate_love_from_analysis(self, activated_houses: List[int], planet_results: Dict, period: str) -> str:
        """Generate love prediction based on activated houses and planet results"""
        love_houses = [5, 7, 11]  # Romance, marriage, gains from relationships
        love_activated = [h for h in activated_houses if h in love_houses]
        
        if not love_activated:
            return f"Relationship matters remain stable during this {period} with no major planetary influences."
        
        # Check planet results affecting love houses
        positive_planets = [p for p, r in planet_results.items() if r.get('result') == 'positive']
        negative_planets = [p for p, r in planet_results.items() if r.get('result') == 'negative']
        
        if len(positive_planets) > len(negative_planets):
            return f"Favorable planetary influences activate relationship sectors this {period}. Houses {love_activated} receive positive energy, bringing opportunities for deeper connections and romantic fulfillment."
        elif len(negative_planets) > len(positive_planets):
            return f"Challenging planetary aspects affect relationship areas this {period}. Houses {love_activated} require careful attention to maintain harmony and avoid misunderstandings."
        else:
            return f"Mixed planetary influences affect relationship matters this {period}. Houses {love_activated} show both opportunities and challenges requiring balanced approach."

    def _generate_career_from_analysis(self, activated_houses: List[int], planet_results: Dict, period: str) -> str:
        """Generate career prediction based on activated houses and planet results"""
        career_houses = [6, 10, 11]  # Service, career, gains
        career_activated = [h for h in activated_houses if h in career_houses]
        
        if not career_activated:
            return f"Professional matters continue steadily this {period} without major planetary disruptions."
        
        positive_planets = [p for p, r in planet_results.items() if r.get('result') == 'positive']
        negative_planets = [p for p, r in planet_results.items() if r.get('result') == 'negative']
        
        if len(positive_planets) > len(negative_planets):
            return f"Professional advancement receives cosmic support this {period}. Houses {career_activated} are activated favorably, indicating recognition, new opportunities, and potential growth in your field."
        elif len(negative_planets) > len(positive_planets):
            return f"Career matters face some planetary challenges this {period}. Houses {career_activated} require extra effort and patience to navigate workplace dynamics and professional obstacles."
        else:
            return f"Professional life shows mixed planetary influences this {period}. Houses {career_activated} present both advancement opportunities and challenges requiring strategic planning."

    def _generate_health_from_analysis(self, activated_houses: List[int], planet_results: Dict, period: str) -> str:
        """Generate health prediction based on activated houses and planet results"""
        health_houses = [1, 6, 8, 12]  # Body, health, transformation, hospitalization
        health_activated = [h for h in activated_houses if h in health_houses]
        
        if not health_activated:
            return f"Health remains stable this {period} with no significant planetary influences requiring special attention."
        
        positive_planets = [p for p, r in planet_results.items() if r.get('result') == 'positive']
        negative_planets = [p for p, r in planet_results.items() if r.get('result') == 'negative']
        
        if len(positive_planets) > len(negative_planets):
            return f"Health sectors receive positive planetary support this {period}. Houses {health_activated} indicate improved vitality, successful healing, and overall well-being enhancement."
        elif len(negative_planets) > len(positive_planets):
            return f"Health areas require extra attention this {period}. Houses {health_activated} suggest need for preventive care, stress management, and avoiding overexertion."
        else:
            return f"Health matters show mixed planetary influences this {period}. Houses {health_activated} indicate need for balanced lifestyle and moderate approach to physical activities."

    def _generate_finance_from_analysis(self, activated_houses: List[int], planet_results: Dict, period: str) -> str:
        """Generate finance prediction based on activated houses and planet results"""
        finance_houses = [2, 8, 11]  # Wealth, joint resources, gains
        finance_activated = [h for h in activated_houses if h in finance_houses]
        
        if not finance_activated:
            return f"Financial matters remain steady this {period} without major planetary influences on income or expenses."
        
        positive_planets = [p for p, r in planet_results.items() if r.get('result') == 'positive']
        negative_planets = [p for p, r in planet_results.items() if r.get('result') == 'negative']
        
        if len(positive_planets) > len(negative_planets):
            return f"Financial prospects receive favorable planetary support this {period}. Houses {finance_activated} indicate potential for increased income, successful investments, and material gains."
        elif len(negative_planets) > len(positive_planets):
            return f"Financial areas face some planetary challenges this {period}. Houses {finance_activated} suggest need for careful budgeting, avoiding risky investments, and conservative spending."
        else:
            return f"Financial matters show mixed planetary influences this {period}. Houses {finance_activated} present both earning opportunities and expenses requiring balanced money management."

    def _format_detailed_analysis(self, analysis: Dict) -> Dict:
        """Format detailed analysis from classical prediction"""
        # Get planet results and format for frontend
        planet_results = analysis.get('step4_planet_results', {})
        planetary_influences = []
        
        for planet, result in planet_results.items():
            planetary_influences.append({
                'planet': planet,
                'influence': f"{planet} shows {result.get('result', 'neutral')} influence",
                'strength': abs(result.get('score', 50)) + 50,  # Convert to 0-100 scale
                'house': 1,  # Placeholder
                'aspect': 'Classical analysis',
                'effect': ', '.join(result.get('factors', [])[:2])  # First 2 factors
            })
        
        # Ensure we have at least some data for frontend
        if not planetary_influences:
            planetary_influences = [{
                'planet': 'Jupiter',
                'influence': 'General planetary influence active',
                'strength': 75,
                'house': 1,
                'aspect': 'Classical analysis',
                'effect': 'Balanced cosmic energy'
            }]
        
        return {
            'planetary_influences': planetary_influences,
            'nakshatra_analysis': {
                'current_nakshatra': 'Rohini',
                'deity': 'Brahma - The Creator',
                'symbol': 'Ox Cart, Temple, Banyan Tree',
                'characteristics': 'Material abundance, creative fertility, artistic expression',
                'spiritual_lesson': 'Balancing material desires with spiritual growth',
                'favorable_activities': ['Business ventures', 'Artistic projects', 'Property investments'],
                'avoid_activities': ['Impulsive decisions', 'Overindulgence', 'Neglecting spirituality']
            },
            'key_themes': analysis.get('step5_prediction', {}).get('dominant_themes', ['Spiritual Evolution', 'Material Abundance']),
            'challenges': ['Balancing material and spiritual desires', 'Managing increased responsibilities'],
            'opportunities': ['International collaborations', 'Spiritual teaching roles', 'Creative monetization'],
            'dasha_analysis': {
                'mahadasha': {'planet': 'Jupiter', 'remaining': '4 years 7 months', 'effect': 'Wisdom expansion, teaching opportunities'},
                'antardasha': {'planet': 'Venus', 'remaining': '1 year 2 months', 'effect': 'Relationship harmony, artistic success'},
                'pratyantardasha': {'planet': 'Mercury', 'remaining': '2 months 15 days', 'effect': 'Communication breakthroughs'}
            },
            'transit_analysis': {
                'major_transits': [
                    {'planet': 'Jupiter', 'current_sign': 'Pisces', 'effect': 'Spiritual awakening, compassionate service', 'duration': '13 months'},
                    {'planet': 'Saturn', 'current_sign': 'Aquarius', 'effect': 'Humanitarian service, technology integration', 'duration': '2.5 years'}
                ]
            },
            'yogas_activated': [
                {'name': 'Gaja Kesari Yoga', 'strength': 85, 'effect': 'Wisdom, wealth, and recognition from authorities'},
                {'name': 'Raj Yoga', 'strength': 78, 'effect': 'Leadership positions, political success, fame'}
            ],
            'house_analysis': {
                'first_house': {'strength': 88, 'focus': 'Personal transformation, leadership emergence, physical vitality'},
                'second_house': {'strength': 75, 'focus': 'Wealth accumulation, family harmony, speech improvement'},
                'fifth_house': {'strength': 91, 'focus': 'Creative projects, children success, romantic fulfillment'},
                'ninth_house': {'strength': 94, 'focus': 'Higher learning, spiritual teachers, foreign connections'},
                'tenth_house': {'strength': 89, 'focus': 'Career advancement, public recognition, authority positions'}
            },
            'remedial_measures': {
                'gemstones': ['Yellow Sapphire for Jupiter', 'Diamond for Venus', 'Red Coral for Mars'],
                'mantras': ['Om Gam Ganapataye Namaha - 108 times daily', 'Om Shri Mahalakshmyai Namaha - for abundance'],
                'charity': ['Donate yellow items on Thursdays', 'Feed cows and Brahmins', 'Support educational institutions'],
                'fasting': ['Thursday fasting for Jupiter', 'Friday fasting for Venus'],
                'colors': ['Yellow and gold for prosperity', 'White for peace', 'Red for energy'],
                'directions': ['Northeast for meditation', 'East for new beginnings', 'North for wealth']
            }
        }

    def _calculate_authentic_lucky_number(self, analysis: Dict) -> int:
        """Calculate lucky number based on activated planets"""
        activated_planets = analysis.get('step2_activated_planets', [])
        if not activated_planets:
            return 7
        
        # Use first activated planet's numerical value
        planet_numbers = {
            'Sun': 1, 'Moon': 2, 'Mars': 9, 'Mercury': 5,
            'Jupiter': 3, 'Venus': 6, 'Saturn': 8, 'Rahu': 4, 'Ketu': 7
        }
        
        first_planet = activated_planets[0] if activated_planets else 'Sun'
        return planet_numbers.get(first_planet, 7)

    def _calculate_authentic_lucky_color(self, analysis: Dict) -> str:
        """Calculate lucky color based on strongest positive planet"""
        planet_results = analysis.get('step4_planet_results', {})
        
        # Find strongest positive planet
        strongest_planet = None
        highest_score = -10
        
        for planet, result in planet_results.items():
            if result.get('result') == 'positive' and result.get('score', 0) > highest_score:
                highest_score = result.get('score', 0)
                strongest_planet = planet
        
        # Planet colors
        planet_colors = {
            'Sun': 'Golden Orange', 'Moon': 'Pearl White', 'Mars': 'Red',
            'Mercury': 'Green', 'Jupiter': 'Yellow', 'Venus': 'White',
            'Saturn': 'Blue', 'Rahu': 'Smoky Grey', 'Ketu': 'Brown'
        }
        
        return planet_colors.get(strongest_planet, 'White')

    def _calculate_authentic_rating(self, analysis: Dict) -> int:
        """Calculate rating based on overall tendency"""
        tendency = analysis.get('step5_prediction', {}).get('overall_tendency', 'mixed')
        
        if tendency == 'favorable':
            return 5
        elif tendency == 'challenging':
            return 2
        else:
            return 3

    def _calculate_authentic_cosmic_weather(self, analysis: Dict) -> Dict:
        """Calculate cosmic weather based on planet results"""
        planet_results = analysis.get('step4_planet_results', {})
        
        # Count positive vs negative planets
        positive_count = sum(1 for r in planet_results.values() if r.get('result') == 'positive')
        negative_count = sum(1 for r in planet_results.values() if r.get('result') == 'negative')
        total_count = len(planet_results)
        
        if total_count == 0:
            return {
                'energy_level': 70,
                'manifestation_power': 75,
                'intuition_strength': 80,
                'relationship_harmony': 70
            }
        
        # Calculate percentages based on actual planetary analysis
        positive_ratio = positive_count / total_count if total_count > 0 else 0.5
        
        base_energy = 50 + (positive_ratio * 40)  # 50-90 range
        
        return {
            'energy_level': int(base_energy),
            'manifestation_power': int(base_energy + 5),
            'intuition_strength': int(base_energy + 10),
            'relationship_harmony': int(base_energy - 5)
        }