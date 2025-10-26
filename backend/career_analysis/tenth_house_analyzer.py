from fastapi import HTTPException

class TenthHouseAnalyzer:
    def __init__(self, chart_data):
        self.chart_data = chart_data
        self.sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                          'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        self.house_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon',
            4: 'Sun', 5: 'Mercury', 6: 'Venus', 7: 'Mars',
            8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
    
    def analyze(self):
        """Analyze 10th house using real chart data"""
        try:
            # Calculate 10th house from ascendant
            ascendant_degrees = self.chart_data.get('ascendant', 0)
            ascendant_sign = int(ascendant_degrees / 30)
            tenth_house_sign = (ascendant_sign + 9) % 12
            tenth_lord = self.house_lords[tenth_house_sign]
            
            # Find planets in actual 10th house
            planets_in_tenth = []
            for planet_name, planet_data in self.chart_data.get('planets', {}).items():
                if planet_data.get('house') == 10:
                    effect = self._get_planet_career_effect(planet_name)
                    planets_in_tenth.append({
                        'name': planet_name,
                        'effect': effect
                    })
            
            # Get 10th lord position
            tenth_lord_data = self.chart_data.get('planets', {}).get(tenth_lord, {})
            
            return {
                'house_sign': self.sign_names[tenth_house_sign],
                'house_lord': tenth_lord,
                'house_lord_position': {
                    'sign': self.sign_names[tenth_lord_data.get('sign', 0)],
                    'house': tenth_lord_data.get('house', 1),
                    'degree': round(tenth_lord_data.get('degree', 0), 2)
                },
                'strength': self._calculate_house_strength(planets_in_tenth, tenth_lord_data),
                'planets_in_house': planets_in_tenth,
                'aspects': self._get_aspects_to_tenth(),
                'interpretation': self._get_career_interpretation(tenth_house_sign, tenth_lord, planets_in_tenth)
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"10th house analysis failed: {str(e)}")
    
    def _calculate_house_strength(self, planets_in_house, tenth_lord_data):
        """Calculate 10th house strength"""
        strength_score = 50  # Base strength
        
        # Add strength for planets in 10th house
        if planets_in_house:
            strength_score += len(planets_in_house) * 15
        
        # Add strength for 10th lord position
        if tenth_lord_data.get('house') in [1, 4, 7, 10]:  # Kendra houses
            strength_score += 20
        
        # Return strength category
        if strength_score >= 75:
            return 'High'
        elif strength_score >= 50:
            return 'Medium'
        else:
            return 'Low'
    
    def _get_aspects_to_tenth(self):
        """Get aspects to 10th house"""
        aspects = []
        for planet_name, planet_data in self.chart_data.get('planets', {}).items():
            house = planet_data.get('house', 1)
            # Planets that aspect 10th house (simplified)
            if house in [1, 4, 7]:  # Houses that aspect 10th
                aspect_type = '7th aspect' if house == 4 else '4th aspect'
                effect = 'Positive influence' if planet_name in ['Jupiter', 'Venus'] else 'Challenging influence'
                aspects.append({
                    'planet': planet_name,
                    'type': aspect_type,
                    'effect': effect
                })
        return aspects
    
    def _process_tenth_house_data(self, chart_data, house_analysis, d10_data, friendship_data):
        """Process all data into 10th house career analysis"""
        ascendant_sign = int(chart_data['ascendant'] / 30) if isinstance(chart_data['ascendant'], (int, float)) else chart_data['ascendant']
        tenth_house_sign = (ascendant_sign + 9) % 12
        tenth_lord = self.house_lords[tenth_house_sign]
        
        # Find 10th lord position
        tenth_lord_position = chart_data['planets'].get(tenth_lord, {})
        
        # Get planets in 10th house with their effects
        planets_in_tenth = []
        for planet_name, planet_data in chart_data['planets'].items():
            if planet_data.get('house') == 10:
                effect = self._get_planet_career_effect(planet_name)
                planets_in_tenth.append({
                    'name': planet_name,
                    'effect': effect
                })
        
        # Calculate house strength
        strength_score = house_analysis.get('house_strength', 50)
        strength = 'High' if strength_score >= 75 else 'Medium' if strength_score >= 50 else 'Low'
        
        # Get aspects to 10th house
        aspects = self._get_aspects_to_tenth(chart_data, friendship_data)
        
        # D10 analysis
        d10_ascendant_sign = int(d10_data['ascendant'] / 30) if isinstance(d10_data['ascendant'], (int, float)) else d10_data['ascendant']
        
        return {
            'house_sign': self.sign_names[tenth_house_sign],
            'house_lord': tenth_lord,
            'house_lord_position': {
                'sign': self.sign_names[tenth_lord_position.get('sign', 0)],
                'house': tenth_lord_position.get('house', 1),
                'degree': tenth_lord_position.get('degree', 0)
            },
            'strength': strength,
            'planets_in_house': planets_in_tenth,
            'aspects': aspects,
            'd10_analysis': {
                'd10_ascendant': self.sign_names[d10_ascendant_sign],
                'career_potential': self._get_d10_interpretation(d10_ascendant_sign)
            },
            'interpretation': self._get_career_interpretation(tenth_house_sign, tenth_lord, planets_in_tenth, strength)
        }
    
    def _get_planet_career_effect(self, planet):
        """Get career effect of planet in 10th house"""
        effects = {
            'Sun': 'Leadership roles, government positions, authority-based careers',
            'Moon': 'Public relations, healthcare, hospitality, nurturing professions',
            'Mars': 'Engineering, military, sports, real estate, surgery',
            'Mercury': 'Business, communication, writing, IT, media, trading',
            'Jupiter': 'Teaching, law, finance, spirituality, consulting, advisory roles',
            'Venus': 'Arts, entertainment, beauty, luxury goods, fashion, creativity',
            'Saturn': 'Service sector, manufacturing, hard work, discipline-based careers'
        }
        return effects.get(planet, 'General career influence')
    
    def _get_aspects_to_tenth(self):
        """Get aspects to 10th house"""
        aspects = []
        for planet_name, planet_data in self.chart_data.get('planets', {}).items():
            house = planet_data.get('house', 1)
            if house in [1, 4, 7]:  # Houses that aspect 10th
                aspect_type = '7th aspect' if house == 4 else '4th aspect'
                
                # Proper aspect interpretation
                if planet_name in ['Jupiter', 'Venus']:
                    effect = 'Positive influence'
                elif planet_name in ['Moon']:
                    effect = 'Emotional influence on career, public recognition'
                elif planet_name in ['Sun']:
                    effect = 'Authority and leadership in career'
                elif planet_name in ['Mercury']:
                    effect = 'Communication and intellectual skills in career'
                elif planet_name in ['Mars']:
                    effect = 'Drive and ambition, but potential conflicts'
                elif planet_name in ['Saturn']:
                    effect = 'Discipline and hard work, delays but steady progress'
                else:
                    effect = 'Mixed influence'
                
                aspects.append({
                    'planet': planet_name,
                    'type': aspect_type,
                    'effect': effect
                })
        return aspects
    
    def _get_d10_interpretation(self, d10_ascendant_sign):
        """Get D10 career interpretation"""
        interpretations = {
            0: 'Leadership and pioneering roles',
            1: 'Stable, luxury-oriented careers',
            2: 'Communication and versatile careers',
            3: 'Nurturing and public-oriented careers',
            4: 'Authority and creative leadership',
            5: 'Analytical and service-oriented careers',
            6: 'Balanced and partnership-based careers',
            7: 'Transformative and research-oriented careers',
            8: 'Teaching and advisory roles',
            9: 'Disciplined and structured careers',
            10: 'Innovative and humanitarian careers',
            11: 'Spiritual and intuitive careers'
        }
        return interpretations.get(d10_ascendant_sign, 'General career potential')
    
    def _get_career_interpretation(self, tenth_sign, tenth_lord, planets_in_tenth):
        """Get overall career interpretation"""
        base_interpretation = f"With {self.sign_names[tenth_sign]} in the 10th house and {tenth_lord} as the career lord, "
        
        # Add sign-specific interpretation
        sign_interpretations = {
            0: "you have pioneering leadership qualities and excel in competitive fields.",
            1: "you prefer stable, luxury-oriented careers with steady growth.",
            2: "you excel in communication, versatile roles, and intellectual pursuits.",
            3: "you are drawn to nurturing professions and public service.",
            4: "you have natural authority and excel in creative leadership roles.",
            5: "you are analytical and excel in service-oriented, detail-focused careers.",
            6: "you seek balanced, partnership-based careers and diplomatic roles.",
            7: "you are drawn to transformative, research-oriented, and investigative careers.",
            8: "you excel in teaching, advisory roles, and knowledge-based professions.",
            9: "you prefer disciplined, structured careers with long-term stability.",
            10: "you are innovative and drawn to humanitarian, technology-based careers.",
            11: "you have intuitive abilities and excel in spiritual, creative professions."
        }
        
        base_interpretation += sign_interpretations.get(tenth_sign, "you have unique career potential.")
        
        if planets_in_tenth:
            planet_names = [p['name'] for p in planets_in_tenth]
            base_interpretation += f" The presence of {', '.join(planet_names)} in the 10th house adds specific career advantages and opportunities."
        
        return base_interpretation