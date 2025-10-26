from .base_calculator import BaseCalculator

class D10Analyzer(BaseCalculator):
    """D10 (Dasamsa) chart analyzer for career analysis"""
    
    def __init__(self, chart_data):
        super().__init__(chart_data)
        self.d10_chart = self._calculate_d10_chart()
    
    def _calculate_d10_chart(self):
        """Calculate D10 positions for all planets"""
        d10_positions = {}
        
        for planet, data in self.chart_data.get('planets', {}).items():
            longitude = data.get('longitude', 0)
            d10_positions[planet] = self._get_d10_position(longitude)
        
        # Calculate D10 ascendant
        ascendant_longitude = self.chart_data.get('ascendant', 0)
        d10_positions['Ascendant'] = self._get_d10_position(ascendant_longitude)
        
        return d10_positions
    
    def _get_d10_position(self, longitude):
        """Calculate D10 position from longitude"""
        sign = int(longitude / 30)
        degree_in_sign = longitude % 30
        
        # D10 division: each sign divided into 10 parts of 3 degrees each
        dasamsa_part = int(degree_in_sign / 3)
        
        # D10 calculation based on sign type
        if sign % 2 == 0:  # Even signs (0,2,4,6,8,10)
            d10_sign = (sign + dasamsa_part) % 12
        else:  # Odd signs (1,3,5,7,9,11)
            d10_sign = (sign + 8 + dasamsa_part) % 12
        
        return {
            'sign': d10_sign,
            'sign_name': self.get_sign_name(d10_sign),
            'dasamsa_part': dasamsa_part + 1
        }
    
    def analyze_d10_chart(self):
        """Complete D10 analysis for career"""
        return {
            'chart_positions': self.d10_chart,
            'ascendant_analysis': self._analyze_d10_ascendant(),
            'tenth_lord_analysis': self._analyze_d10_tenth_lord(),
            'planet_analysis': self._analyze_d10_planets(),
            'career_indicators': self._get_career_indicators(),
            'professional_strength': self._calculate_professional_strength(),
            'career_recommendations': self._get_career_recommendations()
        }
    
    def _analyze_d10_ascendant(self):
        """Analyze D10 ascendant for career approach"""
        d10_asc = self.d10_chart['Ascendant']
        sign = d10_asc['sign']
        
        career_approaches = {
            0: "Direct, pioneering leadership in career",
            1: "Steady, practical approach to profession", 
            2: "Versatile, communication-based careers",
            3: "Nurturing, service-oriented professions",
            4: "Authoritative, creative career expression",
            5: "Analytical, detail-oriented work approach",
            6: "Diplomatic, partnership-focused careers",
            7: "Transformative, research-oriented work",
            8: "Philosophical, teaching-oriented careers",
            9: "Structured, organizational career path",
            10: "Innovative, humanitarian work approach",
            11: "Intuitive, compassionate career expression"
        }
        
        return {
            'sign': d10_asc['sign_name'],
            'career_approach': career_approaches.get(sign, "Balanced career approach"),
            'strength': self._get_sign_strength_for_career(sign)
        }
    
    def _analyze_d10_tenth_lord(self):
        """Analyze 10th lord in D10 chart"""
        d10_asc_sign = self.d10_chart['Ascendant']['sign']
        tenth_house_sign = (d10_asc_sign + 9) % 12
        tenth_lord = self.get_sign_lord(tenth_house_sign)
        
        if tenth_lord not in self.d10_chart:
            return {'error': f'10th lord {tenth_lord} not found in D10 chart'}
        
        lord_position = self.d10_chart[tenth_lord]
        lord_house = self._get_house_from_ascendant(lord_position['sign'], d10_asc_sign)
        
        return {
            'tenth_lord': tenth_lord,
            'position_sign': lord_position['sign_name'],
            'position_house': lord_house,
            'career_impact': self._get_tenth_lord_career_impact(tenth_lord, lord_house),
            'strength_assessment': self._assess_tenth_lord_strength(tenth_lord, lord_position)
        }
    
    def _analyze_d10_planets(self):
        """Analyze all planets in D10 for career significance"""
        planet_analysis = {}
        d10_asc_sign = self.d10_chart['Ascendant']['sign']
        
        career_significators = ['Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for planet in career_significators:
            if planet in self.d10_chart:
                position = self.d10_chart[planet]
                house = self._get_house_from_ascendant(position['sign'], d10_asc_sign)
                
                planet_analysis[planet] = {
                    'sign': position['sign_name'],
                    'house': house,
                    'career_significance': self._get_planet_career_significance(planet),
                    'house_impact': self._get_house_career_impact(house),
                    'overall_effect': self._assess_planet_career_effect(planet, house, position['sign'])
                }
        
        return planet_analysis
    
    def _get_career_indicators(self):
        """Get specific career indicators from D10"""
        indicators = []
        d10_asc_sign = self.d10_chart['Ascendant']['sign']
        
        # Check 10th house occupants
        tenth_house_planets = []
        for planet, position in self.d10_chart.items():
            if planet != 'Ascendant':
                house = self._get_house_from_ascendant(position['sign'], d10_asc_sign)
                if house == 10:
                    tenth_house_planets.append(planet)
        
        if tenth_house_planets:
            indicators.append(f"Planets in 10th house: {', '.join(tenth_house_planets)} - Direct career influence")
        
        # Check Sun position (authority/government)
        if 'Sun' in self.d10_chart:
            sun_house = self._get_house_from_ascendant(self.d10_chart['Sun']['sign'], d10_asc_sign)
            if sun_house in [1, 10, 11]:
                indicators.append("Sun well-placed - Good for government/authority positions")
        
        # Check Mars position (technical/engineering)
        if 'Mars' in self.d10_chart:
            mars_house = self._get_house_from_ascendant(self.d10_chart['Mars']['sign'], d10_asc_sign)
            if mars_house in [3, 6, 10, 11]:
                indicators.append("Mars well-placed - Good for technical/engineering careers")
        
        # Check Mercury position (business/communication)
        if 'Mercury' in self.d10_chart:
            mercury_house = self._get_house_from_ascendant(self.d10_chart['Mercury']['sign'], d10_asc_sign)
            if mercury_house in [2, 3, 7, 10, 11]:
                indicators.append("Mercury well-placed - Good for business/communication careers")
        
        return indicators
    
    def _calculate_professional_strength(self):
        """Calculate overall professional strength from D10"""
        strength_score = 0
        d10_asc_sign = self.d10_chart['Ascendant']['sign']
        
        # D10 ascendant strength
        asc_strength = self._get_sign_strength_for_career(d10_asc_sign)
        if asc_strength == 'Strong':
            strength_score += 20
        elif asc_strength == 'Moderate':
            strength_score += 10
        
        # 10th lord strength
        tenth_house_sign = (d10_asc_sign + 9) % 12
        tenth_lord = self.get_sign_lord(tenth_house_sign)
        if tenth_lord in self.d10_chart:
            lord_position = self.d10_chart[tenth_lord]
            lord_house = self._get_house_from_ascendant(lord_position['sign'], d10_asc_sign)
            if lord_house in [1, 4, 7, 10]:  # Kendra
                strength_score += 25
            elif lord_house in [1, 5, 9]:  # Trikona
                strength_score += 30
            elif lord_house in [6, 8, 12]:  # Dusthana
                strength_score -= 15
        
        # Benefic planets in career houses
        benefics = ['Jupiter', 'Venus', 'Mercury']
        for planet in benefics:
            if planet in self.d10_chart:
                house = self._get_house_from_ascendant(self.d10_chart[planet]['sign'], d10_asc_sign)
                if house in [1, 4, 5, 7, 9, 10, 11]:
                    strength_score += 15
        
        # Malefic planets in upachaya houses (good)
        malefics = ['Sun', 'Mars', 'Saturn']
        for planet in malefics:
            if planet in self.d10_chart:
                house = self._get_house_from_ascendant(self.d10_chart[planet]['sign'], d10_asc_sign)
                if house in [3, 6, 10, 11]:  # Upachaya
                    strength_score += 10
        
        strength_score = max(0, min(100, strength_score))
        
        return {
            'score': strength_score,
            'grade': self._get_strength_grade(strength_score),
            'interpretation': self._interpret_professional_strength(strength_score)
        }
    
    def _get_career_recommendations(self):
        """Get career recommendations based on D10 analysis"""
        recommendations = []
        d10_asc_sign = self.d10_chart['Ascendant']['sign']
        
        # Based on D10 ascendant
        asc_recommendations = {
            0: "Leadership roles, military, sports, pioneering ventures",
            1: "Finance, agriculture, luxury goods, stable businesses",
            2: "Media, writing, teaching, communication, trade",
            3: "Healthcare, hospitality, real estate, public service",
            4: "Government, entertainment, politics, creative fields",
            5: "Service sector, healthcare, analysis, accounting",
            6: "Law, diplomacy, arts, partnerships, consulting",
            7: "Research, investigation, transformation industries",
            8: "Education, law, publishing, international business",
            9: "Corporate management, traditional businesses, administration",
            10: "Technology, innovation, social work, group activities",
            11: "Healing, spirituality, charitable work, creative arts"
        }
        
        recommendations.append(f"Primary career fields: {asc_recommendations.get(d10_asc_sign, 'Diverse career options')}")
        
        # Based on strongest planets
        strong_planets = []
        for planet, position in self.d10_chart.items():
            if planet != 'Ascendant':
                house = self._get_house_from_ascendant(position['sign'], d10_asc_sign)
                if house in [1, 4, 5, 7, 9, 10, 11]:
                    strong_planets.append(planet)
        
        if 'Sun' in strong_planets:
            recommendations.append("Government service, administration, leadership positions highly favored")
        if 'Mars' in strong_planets:
            recommendations.append("Technical fields, engineering, defense, sports recommended")
        if 'Mercury' in strong_planets:
            recommendations.append("Business, communication, writing, teaching fields beneficial")
        if 'Jupiter' in strong_planets:
            recommendations.append("Education, counseling, law, spiritual fields favorable")
        if 'Venus' in strong_planets:
            recommendations.append("Arts, entertainment, luxury goods, beauty industry suitable")
        if 'Saturn' in strong_planets:
            recommendations.append("Service roles, hard work-based careers, traditional fields good")
        
        return recommendations
    
    # Helper methods
    def _get_house_from_ascendant(self, sign, ascendant_sign):
        """Get house number from ascendant"""
        return ((sign - ascendant_sign) % 12) + 1
    
    def _get_sign_strength_for_career(self, sign):
        """Get sign strength for career matters"""
        strong_signs = [0, 4, 9, 10]  # Aries, Leo, Capricorn, Aquarius
        moderate_signs = [1, 2, 6, 8]  # Taurus, Gemini, Libra, Sagittarius
        
        if sign in strong_signs:
            return 'Strong'
        elif sign in moderate_signs:
            return 'Moderate'
        else:
            return 'Average'
    
    def _get_tenth_lord_career_impact(self, lord, house):
        """Get career impact of 10th lord placement"""
        impacts = {
            1: "Strong career identity and personal recognition",
            2: "Career brings wealth and family support",
            3: "Career involves communication and networking",
            4: "Career related to home, property, or education",
            5: "Creative career with good fortune",
            6: "Service-oriented career with challenges to overcome",
            7: "Career involves partnerships or foreign connections",
            8: "Career involves research, transformation, or obstacles",
            9: "Career brings fortune, teaching, or spiritual growth",
            10: "Excellent career success and public recognition",
            11: "Career brings gains, friendships, and aspirations fulfilled",
            12: "Career involves foreign lands, spirituality, or expenses"
        }
        return impacts.get(house, "Moderate career influence")
    
    def _assess_tenth_lord_strength(self, lord, position):
        """Assess 10th lord strength in D10"""
        # Simplified strength assessment
        sign = position['sign']
        
        # Check if in own sign or exaltation
        own_signs = {
            'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
            'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
        }
        
        exaltation_signs = {
            'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5,
            'Jupiter': 3, 'Venus': 11, 'Saturn': 6
        }
        
        if sign in own_signs.get(lord, []):
            return "Strong (Own sign)"
        elif sign == exaltation_signs.get(lord):
            return "Excellent (Exalted)"
        else:
            return "Moderate"
    
    def _get_planet_career_significance(self, planet):
        """Get career significance of planet"""
        significances = {
            'Sun': 'Government, authority, leadership',
            'Moon': 'Public service, hospitality, caregiving',
            'Mars': 'Engineering, military, sports, technical fields',
            'Mercury': 'Business, communication, writing, trade',
            'Jupiter': 'Education, law, counseling, spirituality',
            'Venus': 'Arts, entertainment, luxury, beauty',
            'Saturn': 'Service, labor, traditional professions'
        }
        return significances.get(planet, 'General career influence')
    
    def _get_house_career_impact(self, house):
        """Get career impact of house placement"""
        impacts = {
            1: "Personal career identity and recognition",
            2: "Career brings wealth and resources",
            3: "Career involves communication and effort",
            4: "Career related to home, education, property",
            5: "Creative and fortunate career expression",
            6: "Service career with competitive elements",
            7: "Partnership-based or foreign career",
            8: "Research, transformation, or challenging career",
            9: "Teaching, spiritual, or fortunate career",
            10: "Direct career success and public recognition",
            11: "Career brings gains and network benefits",
            12: "Foreign, spiritual, or behind-scenes career"
        }
        return impacts.get(house, "Moderate career impact")
    
    def _assess_planet_career_effect(self, planet, house, sign):
        """Assess planet's career effect in D10"""
        # Get planet-specific career effects
        planet_effects = {
            'Sun': {
                'kendra': 'Strong leadership and authority in career',
                'trikona': 'Excellent government/administrative opportunities', 
                'upachaya': 'Growing recognition and status',
                'dusthana': 'Authority challenges, ego conflicts at work',
                'default': 'Moderate leadership influence'
            },
            'Mars': {
                'kendra': 'Strong technical/engineering career potential',
                'trikona': 'Excellent for military/sports/surgery careers',
                'upachaya': 'Growing success in competitive fields',
                'dusthana': 'Workplace conflicts, aggressive competition',
                'default': 'Moderate technical career influence'
            },
            'Mercury': {
                'kendra': 'Strong business/communication career success',
                'trikona': 'Excellent for writing/teaching/trade careers',
                'upachaya': 'Growing success in intellectual fields',
                'dusthana': 'Communication challenges, analytical stress',
                'default': 'Moderate business/communication influence'
            },
            'Jupiter': {
                'kendra': 'Strong advisory/educational career potential',
                'trikona': 'Excellent for law/finance/spiritual careers',
                'upachaya': 'Growing wisdom-based career success',
                'dusthana': 'Ethical challenges, over-expansion issues',
                'default': 'Moderate advisory career influence'
            },
            'Venus': {
                'kendra': 'Strong creative/luxury industry success',
                'trikona': 'Excellent for arts/entertainment/beauty careers',
                'upachaya': 'Growing success in aesthetic fields',
                'dusthana': 'Creative blocks, relationship-based work issues',
                'default': 'Moderate creative career influence'
            },
            'Saturn': {
                'kendra': 'Strong disciplined/service career foundation',
                'trikona': 'Excellent for traditional/manufacturing careers',
                'upachaya': 'Slow but steady career growth',
                'dusthana': 'Career delays, hard work with limited recognition',
                'default': 'Moderate service-oriented career influence'
            }
        }
        
        effects = planet_effects.get(planet, {})
        
        if house in [1, 4, 7, 10]:  # Kendra
            return effects.get('kendra', 'Strong positive career influence')
        elif house in [1, 5, 9]:  # Trikona  
            return effects.get('trikona', 'Excellent career fortune')
        elif house in [3, 6, 10, 11]:  # Upachaya
            return effects.get('upachaya', 'Growing career success')
        elif house in [6, 8, 12]:  # Dusthana
            return effects.get('dusthana', 'Career challenges requiring effort')
        else:
            return effects.get('default', 'Moderate career influence')
    
    def _get_strength_grade(self, score):
        """Get strength grade from score"""
        if score >= 80:
            return 'Excellent'
        elif score >= 65:
            return 'Very Good'
        elif score >= 50:
            return 'Good'
        elif score >= 35:
            return 'Average'
        else:
            return 'Needs Improvement'
    
    def _interpret_professional_strength(self, score):
        """Interpret professional strength score"""
        if score >= 70:
            return "Strong professional potential with excellent career prospects"
        elif score >= 50:
            return "Good professional strength with steady career growth"
        elif score >= 30:
            return "Moderate professional potential requiring focused effort"
        else:
            return "Professional growth requires significant effort and skill development"