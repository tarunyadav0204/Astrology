from calculators.planet_analyzer import PlanetAnalyzer
from ashtakavarga import AshtakavargaCalculator

class TenthHouseAnalyzer:
    def __init__(self, chart_data, birth_details):
        self.chart_data = chart_data
        self.birth_details = birth_details
        self.planet_analyzer = PlanetAnalyzer(chart_data)
        self.ashtakavarga = AshtakavargaCalculator(birth_details, chart_data)
        
    def analyze_tenth_house(self):
        """Comprehensive 10th house analysis"""
        tenth_house_number = 10
        
        return {
            "house_info": self._get_house_basic_info(tenth_house_number),
            "planets_in_house": self._analyze_planets_in_house(tenth_house_number),
            "aspects_on_house": self._analyze_aspects_on_house(tenth_house_number),
            "house_strength": self._calculate_house_strength(tenth_house_number),
            "sign_analysis": self._analyze_house_sign(tenth_house_number),
            "ashtakavarga_points": self._get_ashtakavarga_points(tenth_house_number),
            "overall_assessment": self._assess_house_overall(tenth_house_number)
        }
    
    def _get_house_basic_info(self, house_number):
        """Get basic information about the house"""
        # Calculate 10th house sign
        ascendant_longitude = self.chart_data.get('ascendant', 0)
        tenth_house_longitude = (ascendant_longitude + (house_number - 1) * 30) % 360
        tenth_house_sign = int(tenth_house_longitude / 30)
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Get sign lord
        sign_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        
        return {
            "house_number": house_number,
            "house_sign": sign_names[tenth_house_sign],
            "house_sign_number": tenth_house_sign,
            "house_lord": sign_lords[tenth_house_sign],
            "house_longitude": tenth_house_longitude,
            "house_types": ["Kendra", "Artha"]
        }
    
    def _analyze_planets_in_house(self, house_number):
        """Analyze all planets in the specified house"""
        planets_in_house = []
        planets_data = self.chart_data.get('planets', {})
        
        for planet, data in planets_data.items():
            if data.get('house') == house_number:
                planet_analysis = self.planet_analyzer.analyze_planet(planet)
                planets_in_house.append({
                    "planet": planet,
                    "longitude": data.get('longitude', 0),
                    "dignity": planet_analysis.get('dignity_analysis', {}).get('dignity', 'neutral'),
                    "shadbala_rupas": planet_analysis.get('strength_analysis', {}).get('shadbala_rupas', 0),
                    "functional_nature": planet_analysis.get('dignity_analysis', {}).get('functional_nature', 'neutral'),
                    "career_significance": self._get_planet_career_significance(planet),
                    "overall_effect": self._assess_planet_effect_on_house(planet, planet_analysis)
                })
        
        # Calculate conjunctions within the house
        conjunctions = self._find_house_conjunctions(planets_in_house)
        
        return {
            "planets": planets_in_house,
            "planet_count": len(planets_in_house),
            "conjunctions": conjunctions,
            "overall_planetary_influence": self._assess_overall_planetary_influence(planets_in_house),
            "strongest_planet": self._find_strongest_planet_in_house(planets_in_house),
            "career_impact": self._assess_career_impact_of_planets(planets_in_house)
        }
    
    def _analyze_aspects_on_house(self, house_number):
        """Analyze all aspects received by the house"""
        aspects_on_house = []
        planets_data = self.chart_data.get('planets', {})
        
        for planet, data in planets_data.items():
            planet_house = data.get('house', 1)
            if planet_house != house_number:  # Don't aspect self
                aspected_houses = self.planet_analyzer._get_aspect_houses(planet, planet_house)
                
                if house_number in aspected_houses:
                    aspect_type = self._get_aspect_type_for_house(planet_house, house_number)
                    planet_analysis = self.planet_analyzer.analyze_planet(planet)
                    
                    # Calculate aspect effect on house
                    aspect_effect = self._calculate_aspect_effect_on_house(planet, planet_analysis)
                    
                    aspects_on_house.append({
                        "aspecting_planet": planet,
                        "from_house": planet_house,
                        "aspect_type": aspect_type,
                        "effect": aspect_effect['effect'],
                        "effect_score": aspect_effect['score'],
                        "calculation_details": aspect_effect['details']
                    })
        
        # Categorize aspects
        benefic_aspects = [a for a in aspects_on_house if a['effect_score'] > 0]
        malefic_aspects = [a for a in aspects_on_house if a['effect_score'] < 0]
        
        return {
            "aspects": aspects_on_house,
            "aspect_count": len(aspects_on_house),
            "benefic_aspects": benefic_aspects,
            "malefic_aspects": malefic_aspects,
            "net_aspect_score": sum(a['effect_score'] for a in aspects_on_house),
            "overall_aspect_effect": self._assess_overall_aspect_effect(aspects_on_house)
        }
    
    def _calculate_house_strength(self, house_number):
        """Calculate comprehensive house strength"""
        house_info = self._get_house_basic_info(house_number)
        planets_analysis = self._analyze_planets_in_house(house_number)
        aspects_analysis = self._analyze_aspects_on_house(house_number)
        
        # 1. Sign lord strength (30% weight)
        sign_lord = house_info['house_lord']
        lord_analysis = self.planet_analyzer.analyze_planet(sign_lord)
        lord_strength = lord_analysis.get('overall_assessment', {}).get('overall_strength_score', 50)
        
        # 2. Planets in house strength (25% weight)
        planets_strength = 50  # Base
        if planets_analysis['planets']:
            planets_strength = sum(p['shadbala_rupas'] * 10 for p in planets_analysis['planets']) / len(planets_analysis['planets'])
            planets_strength = min(100, max(0, planets_strength))
        
        # 3. Aspects received strength (25% weight)
        aspects_strength = 50 + (aspects_analysis['net_aspect_score'] * 5)
        aspects_strength = min(100, max(0, aspects_strength))
        
        # 4. Ashtakavarga points (20% weight)
        ashtakavarga_points = self._get_ashtakavarga_points(house_number)
        ashtakavarga_strength = (ashtakavarga_points['total_points'] / 8) * 100
        
        # Calculate weighted total
        total_strength = (
            lord_strength * 0.30 +
            planets_strength * 0.25 +
            aspects_strength * 0.25 +
            ashtakavarga_strength * 0.20
        )
        
        return {
            "total_score": round(total_strength, 1),
            "grade": self._get_strength_grade(total_strength),
            "components": {
                "sign_lord_strength": round(lord_strength, 1),
                "planets_strength": round(planets_strength, 1),
                "aspects_strength": round(aspects_strength, 1),
                "ashtakavarga_strength": round(ashtakavarga_strength, 1)
            },
            "interpretation": self._interpret_house_strength(total_strength)
        }
    
    def _analyze_house_sign(self, house_number):
        """Analyze the sign occupying the house"""
        house_info = self._get_house_basic_info(house_number)
        sign_number = house_info['house_sign_number']
        sign_name = house_info['house_sign']
        
        # Career characteristics by sign
        career_characteristics = {
            0: "Leadership, pioneering, military, sports, engineering",  # Aries
            1: "Finance, luxury goods, agriculture, arts, beauty",      # Taurus
            2: "Communication, writing, teaching, trade, media",       # Gemini
            3: "Hospitality, real estate, psychology, caregiving",     # Cancer
            4: "Government, administration, entertainment, politics",   # Leo
            5: "Service, health, analysis, accounting, research",      # Virgo
            6: "Law, diplomacy, partnerships, arts, fashion",         # Libra
            7: "Investigation, occult, surgery, transformation",       # Scorpio
            8: "Teaching, philosophy, law, publishing, travel",       # Sagittarius
            9: "Business, organization, structure, traditional fields", # Capricorn
            10: "Innovation, technology, humanitarian work, groups",   # Aquarius
            11: "Spirituality, healing, arts, charity, service"       # Pisces
        }
        
        return {
            "sign": sign_name,
            "sign_number": sign_number,
            "sign_lord": house_info['house_lord'],
            "career_nature": career_characteristics.get(sign_number, "General career fields"),
            "sign_element": self._get_sign_element(sign_number),
            "sign_quality": self._get_sign_quality(sign_number),
            "career_approach": self._get_career_approach_by_sign(sign_number)
        }
    
    def _get_ashtakavarga_points(self, house_number):
        """Get Ashtakavarga points for the house"""
        try:
            # Calculate Sarvashtakavarga and get house points
            sarva_data = self.ashtakavarga.calculate_sarvashtakavarga()
            
            # Get ascendant sign to calculate house position
            ascendant_sign = int(self.chart_data.get('ascendant', 0) / 30)
            house_sign = (ascendant_sign + house_number - 1) % 12
            house_points = sarva_data['sarvashtakavarga'][house_sign]
            
            return {
                "total_points": house_points,
                "strength_level": "Strong" if house_points >= 30 else "Moderate" if house_points >= 25 else "Weak",
                "interpretation": f"House has {house_points} Ashtakavarga points indicating {'strong' if house_points >= 30 else 'moderate' if house_points >= 25 else 'weak'} support"
            }
        except Exception as e:
            print(f"Ashtakavarga calculation error: {e}")
            return {
                "total_points": 28,  # Average
                "strength_level": "Moderate",
                "interpretation": "Moderate Ashtakavarga support"
            }
    
    def _assess_house_overall(self, house_number):
        """Overall assessment of the house"""
        house_strength = self._calculate_house_strength(house_number)
        planets_analysis = self._analyze_planets_in_house(house_number)
        aspects_analysis = self._analyze_aspects_on_house(house_number)
        sign_analysis = self._analyze_house_sign(house_number)
        
        overall_score = house_strength['total_score']
        
        # Key strengths
        strengths = []
        if house_strength['components']['sign_lord_strength'] >= 70:
            strengths.append("Strong house lord")
        if planets_analysis['planet_count'] > 0:
            strengths.append(f"{planets_analysis['planet_count']} planet(s) in house")
        if aspects_analysis['net_aspect_score'] > 2:
            strengths.append("Beneficial aspects received")
        if house_strength['components']['ashtakavarga_strength'] >= 70:
            strengths.append("Strong Ashtakavarga support")
        
        # Key challenges
        challenges = []
        if house_strength['components']['sign_lord_strength'] <= 40:
            challenges.append("Weak house lord")
        if aspects_analysis['net_aspect_score'] < -2:
            challenges.append("Malefic aspects affecting house")
        if house_strength['components']['ashtakavarga_strength'] <= 40:
            challenges.append("Low Ashtakavarga support")
        
        # Recommendations
        recommendations = []
        if house_strength['components']['sign_lord_strength'] <= 50:
            recommendations.append(f"Strengthen {sign_analysis['sign_lord']} through remedies")
        if aspects_analysis['net_aspect_score'] < 0:
            recommendations.append("Perform remedies for malefic planetary influences")
        recommendations.append("Focus on career fields aligned with house sign characteristics")
        
        return {
            "overall_strength_score": round(overall_score, 1),
            "overall_grade": house_strength['grade'],
            "key_strengths": strengths,
            "key_challenges": challenges,
            "recommendations": recommendations,
            "career_potential": "High" if overall_score >= 70 else "Moderate" if overall_score >= 50 else "Needs attention"
        }
    
    # Helper methods
    def _get_planet_career_significance(self, planet):
        """Get career significance of planet"""
        significance = {
            'Sun': 'Government, authority, leadership positions',
            'Moon': 'Public relations, hospitality, caregiving',
            'Mars': 'Military, sports, engineering, surgery',
            'Mercury': 'Communication, business, writing, teaching',
            'Jupiter': 'Education, law, spirituality, counseling',
            'Venus': 'Arts, entertainment, luxury, beauty',
            'Saturn': 'Service, hard work, traditional professions',
            'Rahu': 'Foreign connections, technology, unconventional',
            'Ketu': 'Spirituality, research, behind-the-scenes work'
        }
        return significance.get(planet, 'General career influence')
    
    def _assess_planet_effect_on_house(self, planet, planet_analysis):
        """Assess planet's effect on the house"""
        strength_score = planet_analysis.get('overall_assessment', {}).get('overall_strength_score', 50)
        if strength_score >= 70:
            return 'Highly beneficial'
        elif strength_score >= 50:
            return 'Beneficial'
        elif strength_score >= 30:
            return 'Mixed results'
        else:
            return 'Challenging'
    
    def _find_house_conjunctions(self, planets_in_house):
        """Find conjunctions within the house"""
        conjunctions = []
        for i, planet1 in enumerate(planets_in_house):
            for planet2 in planets_in_house[i+1:]:
                longitude_diff = abs(planet1['longitude'] - planet2['longitude'])
                if longitude_diff <= 10:  # Within 10 degrees
                    conjunctions.append({
                        'planet1': planet1['planet'],
                        'planet2': planet2['planet'],
                        'orb': round(longitude_diff, 2),
                        'effect': 'Beneficial' if self._is_beneficial_conjunction(planet1['planet'], planet2['planet']) else 'Challenging'
                    })
        return conjunctions
    
    def _assess_overall_planetary_influence(self, planets_in_house):
        """Assess overall planetary influence"""
        if not planets_in_house:
            return 'No direct planetary influence'
        
        total_strength = sum(p['shadbala_rupas'] for p in planets_in_house)
        avg_strength = total_strength / len(planets_in_house)
        
        if avg_strength >= 6:
            return 'Strong planetary support'
        elif avg_strength >= 4:
            return 'Moderate planetary support'
        else:
            return 'Weak planetary support'
    
    def _find_strongest_planet_in_house(self, planets_in_house):
        """Find strongest planet in house"""
        if not planets_in_house:
            return None
        
        strongest = max(planets_in_house, key=lambda p: p['shadbala_rupas'])
        return {
            'planet': strongest['planet'],
            'strength': strongest['shadbala_rupas'],
            'significance': strongest['career_significance']
        }
    
    def _assess_career_impact_of_planets(self, planets_in_house):
        """Assess career impact of planets in house"""
        if not planets_in_house:
            return 'Career depends on house lord and aspects'
        
        impacts = []
        for planet in planets_in_house:
            if planet['shadbala_rupas'] >= 5:
                impacts.append(f"{planet['planet']}: {planet['career_significance']}")
        
        return impacts if impacts else ['Moderate planetary career influence']
    
    def _get_aspect_type_for_house(self, from_house, to_house):
        """Get aspect type between houses"""
        if to_house >= from_house:
            aspect_number = to_house - from_house + 1
        else:
            aspect_number = (12 - from_house) + to_house + 1
        
        if aspect_number > 12:
            aspect_number = aspect_number - 12
        
        aspect_names = {
            3: '3rd aspect', 4: '4th aspect', 5: '5th aspect', 7: '7th aspect',
            8: '8th aspect', 9: '9th aspect', 10: '10th aspect', 11: '11th aspect'
        }
        
        return aspect_names.get(aspect_number, f'{aspect_number}th aspect')
    
    def _calculate_aspect_effect_on_house(self, planet, planet_analysis):
        """Calculate aspect effect on house"""
        base_score = 0
        details = []
        
        # Natural benefic/malefic
        natural_benefics = ['Jupiter', 'Venus']
        natural_malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']
        
        if planet in natural_benefics:
            base_score += 2
            details.append(f"Natural benefic ({planet}): +2 points")
        elif planet in natural_malefics:
            base_score -= 2
            details.append(f"Natural malefic ({planet}): -2 points")
        else:
            base_score += 1
            details.append(f"Conditional benefic ({planet}): +1 point")
        
        # Planet strength
        strength_score = planet_analysis.get('overall_assessment', {}).get('overall_strength_score', 50)
        if strength_score >= 70:
            base_score += 2
            details.append("Strong planet: +2 points")
        elif strength_score <= 30:
            base_score -= 2
            details.append("Weak planet: -2 points")
        else:
            details.append("Moderate planet strength: 0 points")
        
        # Determine effect
        if base_score >= 3:
            effect = 'Highly beneficial'
        elif base_score >= 1:
            effect = 'Beneficial'
        elif base_score >= -1:
            effect = 'Neutral'
        elif base_score >= -3:
            effect = 'Malefic'
        else:
            effect = 'Highly malefic'
        
        details.append(f"Final aspect effect: {effect} (Score: {base_score})")
        
        return {
            'effect': effect,
            'score': base_score,
            'details': details
        }
    
    def _assess_overall_aspect_effect(self, aspects):
        """Assess overall aspect effect"""
        if not aspects:
            return 'No aspects received'
        
        total_score = sum(a['effect_score'] for a in aspects)
        if total_score >= 5:
            return 'Highly beneficial aspects'
        elif total_score >= 2:
            return 'Beneficial aspects'
        elif total_score >= -2:
            return 'Mixed aspects'
        elif total_score >= -5:
            return 'Malefic aspects'
        else:
            return 'Highly malefic aspects'
    
    def _get_strength_grade(self, score):
        """Get strength grade"""
        if score >= 80:
            return 'Excellent'
        elif score >= 70:
            return 'Very Good'
        elif score >= 60:
            return 'Good'
        elif score >= 50:
            return 'Average'
        elif score >= 40:
            return 'Below Average'
        else:
            return 'Weak'
    
    def _interpret_house_strength(self, score):
        """Interpret house strength"""
        if score >= 70:
            return 'Strong house supporting career success and recognition'
        elif score >= 50:
            return 'Moderate house strength with good career potential'
        else:
            return 'House needs strengthening for better career outcomes'
    
    def _get_sign_element(self, sign_number):
        """Get sign element"""
        elements = ['Fire', 'Earth', 'Air', 'Water'] * 3
        return elements[sign_number]
    
    def _get_sign_quality(self, sign_number):
        """Get sign quality"""
        qualities = ['Cardinal', 'Fixed', 'Mutable'] * 4
        return qualities[sign_number]
    
    def _get_career_approach_by_sign(self, sign_number):
        """Get career approach by sign"""
        approaches = {
            0: "Direct, pioneering, leadership-oriented",
            1: "Steady, practical, value-focused",
            2: "Versatile, communicative, adaptable",
            3: "Nurturing, intuitive, security-focused",
            4: "Authoritative, creative, recognition-seeking",
            5: "Service-oriented, analytical, perfectionist",
            6: "Diplomatic, balanced, partnership-focused",
            7: "Intense, transformative, research-oriented",
            8: "Philosophical, expansive, knowledge-seeking",
            9: "Structured, ambitious, goal-oriented",
            10: "Innovative, humanitarian, group-focused",
            11: "Intuitive, compassionate, service-oriented"
        }
        return approaches.get(sign_number, "Balanced approach")
    
    def _is_beneficial_conjunction(self, planet1, planet2):
        """Check if conjunction is beneficial"""
        benefics = ['Jupiter', 'Venus', 'Mercury', 'Moon']
        malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']
        
        if planet1 in benefics and planet2 in benefics:
            return True
        elif planet1 in malefics and planet2 in malefics:
            return False
        else:
            return True  # Mixed conjunction - generally manageable