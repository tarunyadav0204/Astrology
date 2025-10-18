"""
Main Marriage Analyzer
Reuses existing house analysis logic
"""
from typing import Dict, List, Any, Optional
from event_prediction.house7_analyzer import House7Analyzer
from .guna_milan import GunaMilanCalculator

class MarriageAnalyzer:
    def __init__(self):
        self.guna_calculator = GunaMilanCalculator()
    
    def analyze_single_chart(self, chart_data: Dict, birth_details: Dict) -> Dict[str, Any]:
        """Analyze single chart for marriage prospects"""
        # Create a simple object from birth_details dict
        class BirthData:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
        
        birth_obj = BirthData(birth_details)
        
        # Use existing House7Analyzer
        house7_analyzer = House7Analyzer(birth_obj, chart_data)
        
        # Get 7th house analysis
        house_strength = house7_analyzer.analyze_house_strength()
        
        # Get marriage timing predictions (simplified to avoid dasha errors)
        try:
            marriage_timing = house7_analyzer.predict_marriage_timing()
        except:
            marriage_timing = []  # Fallback if timing fails
        
        # Analyze marriage karakas
        karakas = self._analyze_karakas(chart_data)
        
        # Check Manglik dosha
        manglik = self._check_manglik_dosha(chart_data)
        
        # Get D9 analysis
        d9_analysis = self._analyze_d9_chart(birth_details)
        
        # Calculate overall score (now includes D9)
        overall_score = self._calculate_overall_score(house_strength, karakas, manglik, d9_analysis)
        
        return {
            'overall_score': overall_score,
            'seventh_house_analysis': {
                'house_sign': self._get_sign_name(house7_analyzer.house_7_sign),
                'house_lord': house7_analyzer.house_7_lord,
                'strength_score': house_strength['total_strength'],
                'planets_in_house': house7_analyzer._get_planets_in_house(7),
                'interpretation': house_strength['interpretation']
            },
            'karaka_analysis': karakas,
            'manglik_analysis': manglik,
            'd9_analysis': d9_analysis,
            'marriage_timing': marriage_timing[:5],  # Top 5 predictions
            'recommendations': self._generate_recommendations(house_strength, karakas, manglik, d9_analysis),
            'chart_type': 'single'
        }
    
    def analyze_compatibility(self, boy_chart: Dict, girl_chart: Dict, 
                           boy_details: Dict, girl_details: Dict) -> Dict[str, Any]:
        """Analyze compatibility between two charts"""
        
        # Individual analyses
        boy_analysis = self.analyze_single_chart(boy_chart, boy_details)
        girl_analysis = self.analyze_single_chart(girl_chart, girl_details)
        
        # Guna Milan calculation
        boy_moon_nak = boy_chart.get('planets', {}).get('Moon', {}).get('nakshatra', 'Ashwini')
        girl_moon_nak = girl_chart.get('planets', {}).get('Moon', {}).get('nakshatra', 'Ashwini')
        
        guna_milan = self.guna_calculator.calculate_ashtakoot(boy_moon_nak, girl_moon_nak)
        
        # Combined compatibility score
        compatibility_score = self._calculate_compatibility_score(
            boy_analysis, girl_analysis, guna_milan
        )
        
        return {
            'compatibility_score': compatibility_score,
            'guna_milan': guna_milan,
            'boy_analysis': boy_analysis,
            'girl_analysis': girl_analysis,
            'combined_recommendations': self._generate_compatibility_recommendations(
                boy_analysis, girl_analysis, guna_milan
            ),
            'chart_type': 'compatibility'
        }
    
    def _analyze_karakas(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze Venus and Jupiter as marriage significators"""
        venus_data = chart_data['planets'].get('Venus', {})
        jupiter_data = chart_data['planets'].get('Jupiter', {})
        
        return {
            'venus': {
                'sign': self._get_sign_name(venus_data.get('sign', 0)),
                'house': self._get_planet_house(venus_data, chart_data),
                'dignity': self._get_planet_dignity('Venus', venus_data.get('sign', 0)),
                'strength': self._calculate_planet_strength('Venus', venus_data, chart_data)
            },
            'jupiter': {
                'sign': self._get_sign_name(jupiter_data.get('sign', 0)),
                'house': self._get_planet_house(jupiter_data, chart_data),
                'dignity': self._get_planet_dignity('Jupiter', jupiter_data.get('sign', 0)),
                'strength': self._calculate_planet_strength('Jupiter', jupiter_data, chart_data)
            }
        }
    
    def _check_manglik_dosha(self, chart_data: Dict) -> Dict[str, Any]:
        """Check for Mangal/Kuja Dosha (Mars in 7th, 8th houses only)"""
        mars_data = chart_data['planets'].get('Mars', {})
        mars_house = self._get_planet_house(mars_data, chart_data)
        
        is_manglik = mars_house in [7, 8]
        
        return {
            'is_manglik': is_manglik,
            'mars_house': mars_house,
            'mars_sign': self._get_sign_name(mars_data.get('sign', 0)),
            'severity': 'High' if mars_house == 7 else 'Medium' if mars_house == 8 else None,
            'cancellation': {'has_cancellation': False}
        }
    
    def _calculate_overall_score(self, house_strength: Dict, karakas: Dict, manglik: Dict, d9_analysis: Dict = None) -> Dict[str, Any]:
        """Calculate overall marriage score with D9 integration and yoga scoring"""
        seventh_score = house_strength['total_strength'] / 10
        venus_score = karakas['venus']['strength']
        jupiter_score = karakas['jupiter']['strength']
        
        # D9 contribution (30% weight as per Parasara tradition)
        d9_score = 0
        if d9_analysis:
            d9_score = d9_analysis.get('overall_strength', 0) / 10
        
        # Calculate yoga score
        yoga_score = self._calculate_yoga_score(karakas, manglik)
        
        manglik_penalty = 0
        if manglik['is_manglik']:
            severity = manglik.get('severity', 'Low')
            if severity == 'High':
                manglik_penalty = 1.5
            elif severity == 'Medium':
                manglik_penalty = 0.8
        
        # Updated weightage: D1 (70%) + D9 (30%) with yoga integration
        d1_component = (seventh_score * 0.3 + venus_score * 0.15 + jupiter_score * 0.1 + yoga_score * 0.15) * 0.7
        d9_component = d9_score * 0.25
        special_factors = 0.05  # Reserved for special factors
        
        raw_score = d1_component + d9_component + special_factors - manglik_penalty
        final_score = max(0, min(10, raw_score))
        
        return {
            'score': round(final_score, 1),
            'max_score': 10,
            'percentage': round((final_score / 10) * 100, 1),
            'grade': self._get_score_grade(final_score),
            'components': {
                'seventh_house_d1': round(seventh_score * 0.3, 1),
                'venus_d1': round(venus_score * 0.15, 1),
                'jupiter_d1': round(jupiter_score * 0.1, 1),
                'yoga_score': round(yoga_score, 1),
                'd9_strength': round(d9_score * 0.25, 1),
                'manglik_penalty': manglik_penalty,
                'd1_total': round(d1_component, 1),
                'd9_total': round(d9_component, 1)
            }
        }
    
    def _calculate_compatibility_score(self, boy_analysis: Dict, girl_analysis: Dict, 
                                     guna_milan: Dict) -> Dict[str, Any]:
        """Calculate combined compatibility score"""
        
        # Individual marriage scores
        boy_score = boy_analysis.get('overall_score', {}).get('score', 5)
        girl_score = girl_analysis.get('overall_score', {}).get('score', 5)
        
        # Guna Milan score (convert to 10 scale)
        guna_score = (guna_milan.get('total_score', 18) / 36) * 10
        
        # Weighted combination: Individual 40%, Guna Milan 60%
        individual_avg = (boy_score + girl_score) / 2
        final_score = (individual_avg * 0.4) + (guna_score * 0.6)
        
        return {
            'score': round(final_score, 1),
            'max_score': 10,
            'percentage': round((final_score / 10) * 100, 1),
            'grade': self._get_score_grade(final_score),
            'components': {
                'boy_individual': boy_score,
                'girl_individual': girl_score,
                'guna_milan': round(guna_score, 1),
                'individual_average': round(individual_avg, 1)
            }
        }
    

    
    def _get_sign_name(self, sign_num: int) -> str:
        """Convert sign number to name"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_num % 12]
    
    def _get_planet_house(self, planet_data: Dict, chart_data: Dict) -> int:
        """Get house number where planet is positioned"""
        if not planet_data:
            return 1
        planet_sign = planet_data.get('sign', 0)
        for i, house in enumerate(chart_data['houses']):
            if house['sign'] == planet_sign:
                return i + 1
        return 1
    
    def _get_planet_dignity(self, planet: str, sign: int) -> str:
        """Get planet dignity in sign"""
        exaltation = {'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6}
        debilitation = {'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0}
        own_signs = {
            'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
            'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
        }
        
        if sign == exaltation.get(planet):
            return 'Exalted'
        elif sign == debilitation.get(planet):
            return 'Debilitated'
        elif sign in own_signs.get(planet, []):
            return 'Own'
        else:
            return 'Neutral'
    
    def _calculate_planet_strength(self, planet: str, planet_data: Dict, chart_data: Dict) -> int:
        """Calculate planet strength (0-10 scale)"""
        if not planet_data:
            return 5
        
        strength = 5
        sign = planet_data.get('sign', 0)
        house = self._get_planet_house(planet_data, chart_data)
        
        # Dignity bonus
        dignity = self._get_planet_dignity(planet, sign)
        if dignity == 'Exalted':
            strength += 3
        elif dignity == 'Own':
            strength += 2
        elif dignity == 'Debilitated':
            strength -= 3
        
        # House placement
        if house in [1, 4, 7, 10]:  # Kendra
            strength += 1
        elif house in [5, 9]:  # Trikona
            strength += 2
        
        return max(0, min(10, strength))
    
    def _generate_recommendations(self, house_strength: Dict, karakas: Dict, manglik: Dict, d9_analysis: Dict = None) -> List[str]:
        """Generate marriage recommendations including D9 insights"""
        recommendations = []
        
        if house_strength['total_strength'] < 50:
            recommendations.append("Strengthen 7th house through remedies for its lord")
        
        if karakas['venus']['strength'] < 5:
            recommendations.append("Perform Venus remedies for better relationship harmony")
        
        if karakas['jupiter']['strength'] < 5:
            recommendations.append("Strengthen Jupiter for wisdom in marriage decisions")
        
        if manglik['is_manglik']:
            recommendations.append("Consider Manglik remedies or match with another Manglik")
        
        # D9 specific recommendations
        if d9_analysis:
            if d9_analysis.get('seventh_house_d9', {}).get('strength', 0) < 5:
                recommendations.append("D9 7th house is weak - focus on spiritual growth for marriage")
            
            if d9_analysis.get('venus_d9', {}).get('strength', 0) < 5:
                recommendations.append("Venus weak in D9 - perform Venus mantras and charity")
            
            if d9_analysis.get('jupiter_d9', {}).get('strength', 0) < 5:
                recommendations.append("Jupiter weak in D9 - seek blessings from guru/teacher")
        
        return recommendations
    
    def _generate_compatibility_recommendations(self, boy_analysis: Dict, 
                                              girl_analysis: Dict, 
                                              guna_milan: Dict) -> List[str]:
        """Generate compatibility recommendations"""
        recommendations = []
        
        # Guna Milan recommendations
        total_score = guna_milan.get('total_score', 18)
        if total_score < 18:
            recommendations.append("Low Guna Milan score - consider detailed consultation")
        elif total_score < 25:
            recommendations.append("Average compatibility - focus on mutual understanding")
        else:
            recommendations.append("Good compatibility indicated by Guna Milan")
        
        # Critical issues
        critical_issues = guna_milan.get('critical_issues', [])
        for issue in critical_issues:
            if 'Nadi Dosha' in issue:
                recommendations.append("Nadi Dosha present - requires special remedies")
            elif 'Bhakoot Dosha' in issue:
                recommendations.append("Bhakoot Dosha - may affect health and prosperity")
            elif 'Gana Dosha' in issue:
                recommendations.append("Gana mismatch - may cause temperament conflicts")
        
        # Individual chart recommendations
        boy_manglik = boy_analysis.get('manglik_analysis', {}).get('is_manglik', False)
        girl_manglik = girl_analysis.get('manglik_analysis', {}).get('is_manglik', False)
        
        if boy_manglik and girl_manglik:
            recommendations.append("Both are Manglik - mutual cancellation of dosha")
        elif boy_manglik or girl_manglik:
            recommendations.append("One partner is Manglik - requires remedial measures")
        
        return recommendations
    
    def _analyze_d9_chart(self, birth_details: Dict) -> Dict[str, Any]:
        """Analyze D9 Navamsa chart for marriage with comprehensive details"""
        try:
            # Calculate D9 using Swiss Ephemeris directly
            import swisseph as swe
            from datetime import datetime
            
            # Parse birth data
            date_parts = birth_details['date'].split('-')
            time_parts = birth_details['time'].split(':')
            hour = float(time_parts[0]) + float(time_parts[1])/60
            
            # Handle timezone
            tz_offset = 5.5  # Default IST
            if 'timezone' in birth_details and birth_details['timezone'].startswith('UTC'):
                tz_str = birth_details['timezone'][3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
            
            utc_hour = hour - tz_offset
            jd = swe.julday(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]), utc_hour)
            
            # Set Lahiri Ayanamsa
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            # Calculate D9 chart using corrected method
            d9_chart = self._calculate_d9_positions_corrected(jd, birth_details['latitude'], birth_details['longitude'])
            
            # Analyze D9 7th house
            d9_seventh_house = self._analyze_d9_seventh_house(d9_chart)
            
            # Analyze all major planets in D9
            venus_d9 = self._analyze_planet_in_d9('Venus', d9_chart)
            jupiter_d9 = self._analyze_planet_in_d9('Jupiter', d9_chart)
            mars_d9 = self._analyze_planet_in_d9('Mars', d9_chart)
            moon_d9 = self._analyze_planet_in_d9('Moon', d9_chart)
            
            # Detect D9 yogas
            d9_yogas = self._detect_d9_yogas(d9_chart)
            
            # Calculate D9 overall strength
            overall_strength = self._calculate_d9_strength(d9_seventh_house, venus_d9, jupiter_d9)
            
            return {
                'seventh_house_d9': d9_seventh_house,
                'venus_d9': venus_d9,
                'jupiter_d9': jupiter_d9,
                'mars_d9': mars_d9,
                'moon_d9': moon_d9,
                'd9_yogas': d9_yogas,
                'overall_strength': overall_strength,
                'interpretation': self._interpret_d9_results(d9_seventh_house, venus_d9, jupiter_d9)
            }
            
        except Exception as e:
            return {'error': f'D9 analysis failed: {str(e)}'}
    
    def _analyze_d9_seventh_house(self, d9_chart: Dict) -> Dict[str, Any]:
        """Analyze 7th house in D9"""
        d9_houses = d9_chart.get('houses', [])
        if len(d9_houses) < 7:
            return {'error': 'Invalid D9 chart data'}
        
        seventh_house_d9 = d9_houses[6]  # 7th house (0-indexed)
        seventh_sign_d9 = seventh_house_d9.get('sign', 0)
        seventh_lord_d9 = self._get_house_lord(seventh_sign_d9)
        
        # Find planets in 7th house D9
        planets_in_7th_d9 = []
        d9_planets = d9_chart.get('planets', {})
        for planet, data in d9_planets.items():
            if data.get('sign') == seventh_sign_d9:
                planets_in_7th_d9.append(planet)
        
        # Calculate strength
        strength = self._calculate_house_strength_d9(seventh_lord_d9, d9_planets, planets_in_7th_d9)
        
        # Calculate 7th house parameter scores
        house_scores = self._calculate_house_parameter_scores(seventh_lord_d9, strength, planets_in_7th_d9)
        
        return {
            'sign': seventh_sign_d9,
            'sign_name': self._get_sign_name(seventh_sign_d9),
            'lord': seventh_lord_d9,
            'planets': planets_in_7th_d9,
            'strength': strength,
            'parameter_scores': house_scores
        }
    
    def _analyze_planet_in_d9(self, planet_name: str, d9_chart: Dict) -> Dict[str, Any]:
        """Analyze specific planet in D9 with comprehensive details"""
        d9_planets = d9_chart.get('planets', {})
        planet_data = d9_planets.get(planet_name, {})
        
        if not planet_data:
            return {'error': f'{planet_name} not found in D9'}
        
        sign = planet_data.get('sign', 0)
        longitude = planet_data.get('longitude', 0)
        dignity = self._get_planet_dignity(planet_name, sign)
        strength = self._calculate_planet_strength_d9(planet_name, sign)
        
        # Calculate house position in D9 using Whole Sign system
        d9_houses = d9_chart.get('houses', [])
        d9_ascendant_sign = d9_houses[0].get('sign', 0) if d9_houses else 0
        
        # Calculate house number using Whole Sign system
        house = ((sign - d9_ascendant_sign) % 12) + 1
        
        # Find conjunctions in D9
        conjunctions = []
        for other_planet, other_data in d9_planets.items():
            if other_planet != planet_name and other_data.get('sign') == sign:
                conjunctions.append(other_planet)
        
        # Calculate aspects in D9
        aspects = self._get_d9_aspects(planet_name, sign, d9_planets)
        
        # Get nakshatra lord
        nakshatra_lord = self._get_nakshatra_lord(longitude)
        
        # Check special conditions
        special_conditions = self._check_d9_special_conditions(planet_name, sign, longitude)
        
        # Calculate positive/negative marking
        positive_negative = self._get_positive_negative_marking(strength, dignity, house)
        
        # Calculate detailed parameter scores
        parameter_scores = self._calculate_parameter_scores(planet_name, sign, house, dignity, strength, conjunctions, aspects)
        
        return {
            'sign': sign,
            'sign_name': self._get_sign_name(sign),
            'house': house,
            'dignity': dignity,
            'strength': strength,
            'longitude': longitude,
            'conjunctions': conjunctions,
            'aspects': aspects,
            'nakshatra_lord': nakshatra_lord,
            'special_conditions': special_conditions,
            'positive_negative': positive_negative,
            'parameter_scores': parameter_scores
        }
    
    def _calculate_d9_strength(self, seventh_house: Dict, venus: Dict, jupiter: Dict) -> int:
        """Calculate overall D9 strength for marriage"""
        seventh_strength = seventh_house.get('strength', 0)
        venus_strength = venus.get('strength', 0)
        jupiter_strength = jupiter.get('strength', 0)
        
        # Weighted average: 7th house (50%), Venus (30%), Jupiter (20%)
        overall = (seventh_strength * 0.5 + venus_strength * 0.3 + jupiter_strength * 0.2)
        return int(min(10, max(0, overall)))
    
    def _interpret_d9_results(self, seventh_house: Dict, venus: Dict, jupiter: Dict) -> str:
        """Interpret D9 analysis results"""
        interpretations = []
        
        # 7th house interpretation
        if seventh_house.get('strength', 0) >= 7:
            interpretations.append("Strong 7th house in D9 indicates harmonious marriage")
        elif seventh_house.get('strength', 0) >= 5:
            interpretations.append("Moderate 7th house strength in D9 suggests average marital harmony")
        else:
            interpretations.append("Weak 7th house in D9 may indicate marital challenges")
        
        # Venus interpretation
        venus_dignity = venus.get('dignity', 'Neutral')
        if venus_dignity == 'Exalted':
            interpretations.append("Exalted Venus in D9 blesses with loving spouse")
        elif venus_dignity == 'Own':
            interpretations.append("Venus in own sign in D9 ensures romantic fulfillment")
        elif venus_dignity == 'Debilitated':
            interpretations.append("Debilitated Venus in D9 may cause relationship issues")
        
        # Jupiter interpretation
        jupiter_dignity = jupiter.get('dignity', 'Neutral')
        if jupiter_dignity == 'Exalted':
            interpretations.append("Exalted Jupiter in D9 brings wise and spiritual spouse")
        elif jupiter_dignity == 'Own':
            interpretations.append("Jupiter in own sign in D9 ensures dharmic marriage")
        
        return " • ".join(interpretations) if interpretations else "D9 analysis shows mixed results"
    
    def _get_house_lord(self, sign: int) -> str:
        """Get house lord for a sign"""
        lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 
                'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter']
        return lords[sign % 12]
    
    def _calculate_house_strength_d9(self, lord: str, planets: Dict, occupants: List) -> int:
        """Calculate house strength in D9"""
        strength = 5  # Base strength
        
        # Lord's dignity
        lord_data = planets.get(lord, {})
        if lord_data:
            lord_sign = lord_data.get('sign', 0)
            dignity = self._get_planet_dignity(lord, lord_sign)
            if dignity == 'Exalted':
                strength += 3
            elif dignity == 'Own':
                strength += 2
            elif dignity == 'Debilitated':
                strength -= 3
        
        # Benefic planets in house
        benefics = ['Jupiter', 'Venus', 'Moon']
        malefics = ['Mars', 'Saturn', 'Rahu', 'Ketu']
        
        for planet in occupants:
            if planet in benefics:
                strength += 1
            elif planet in malefics:
                strength -= 1
        
        return max(0, min(10, strength))
    
    def _calculate_planet_strength_d9(self, planet: str, sign: int) -> int:
        """Calculate planet strength in D9"""
        strength = 5  # Base strength
        
        dignity = self._get_planet_dignity(planet, sign)
        if dignity == 'Exalted':
            strength += 4
        elif dignity == 'Own':
            strength += 3
        elif dignity == 'Debilitated':
            strength -= 4
        
        return max(0, min(10, strength))
    
    def _calculate_parameter_scores(self, planet_name: str, sign: int, house: int, dignity: str, strength: int, conjunctions: List, aspects: List) -> Dict[str, Any]:
        """Calculate detailed parameter scores with color coding"""
        scores = {}
        
        # Dignity Score
        if dignity == 'Exalted':
            scores['dignity'] = {'score': 10, 'status': 'Positive', 'color': 'green', 'text': f'{planet_name} Exalted'}
        elif dignity == 'Own':
            scores['dignity'] = {'score': 8, 'status': 'Positive', 'color': 'green', 'text': f'{planet_name} in Own Sign'}
        elif dignity == 'Debilitated':
            scores['dignity'] = {'score': 2, 'status': 'Negative', 'color': 'red', 'text': f'{planet_name} Debilitated'}
        else:
            scores['dignity'] = {'score': 5, 'status': 'Neutral', 'color': 'gray', 'text': f'{planet_name} Neutral'}
        
        # House Score
        if house in [1, 4, 7, 10]:  # Kendra
            scores['house'] = {'score': 8, 'status': 'Positive', 'color': 'green', 'text': f'{house}th House (Kendra)'}
        elif house in [5, 9]:  # Trikona
            scores['house'] = {'score': 9, 'status': 'Positive', 'color': 'green', 'text': f'{house}th House (Trikona)'}
        elif house in [2, 11]:  # Wealth houses
            scores['house'] = {'score': 7, 'status': 'Positive', 'color': 'green', 'text': f'{house}th House (Wealth)'}
        elif house in [6, 8, 12]:  # Dusthana
            scores['house'] = {'score': 3, 'status': 'Negative', 'color': 'red', 'text': f'{house}th House (Dusthana)'}
        else:
            scores['house'] = {'score': 5, 'status': 'Neutral', 'color': 'gray', 'text': f'{house}th House'}
        
        # Conjunction Score
        benefics = ['Jupiter', 'Venus', 'Moon']
        malefics = ['Mars', 'Saturn', 'Rahu', 'Ketu']
        conj_score = 5
        conj_status = 'Neutral'
        conj_color = 'gray'
        conj_text = 'No Conjunctions'
        
        if conjunctions:
            benefic_conj = [p for p in conjunctions if p in benefics]
            malefic_conj = [p for p in conjunctions if p in malefics]
            
            if benefic_conj and not malefic_conj:
                conj_score = 8
                conj_status = 'Positive'
                conj_color = 'green'
                conj_text = f'With {", ".join(benefic_conj)}'
            elif malefic_conj and not benefic_conj:
                conj_score = 3
                conj_status = 'Negative'
                conj_color = 'red'
                conj_text = f'With {", ".join(malefic_conj)}'
            else:
                conj_score = 5
                conj_status = 'Mixed'
                conj_color = 'orange'
                conj_text = f'Mixed Conjunctions'
        
        scores['conjunctions'] = {'score': conj_score, 'status': conj_status, 'color': conj_color, 'text': conj_text}
        
        # Aspects Score
        aspect_score = 5
        aspect_status = 'Neutral'
        aspect_color = 'gray'
        aspect_text = 'No Major Aspects'
        
        if aspects:
            benefic_aspects = [a for a in aspects if a['planet'] in benefics]
            malefic_aspects = [a for a in aspects if a['planet'] in malefics]
            
            if benefic_aspects and not malefic_aspects:
                aspect_score = 7
                aspect_status = 'Positive'
                aspect_color = 'green'
                aspect_text = f'Benefic Aspects ({len(benefic_aspects)})'
            elif malefic_aspects and not benefic_aspects:
                aspect_score = 4
                aspect_status = 'Negative'
                aspect_color = 'red'
                aspect_text = f'Malefic Aspects ({len(malefic_aspects)})'
            else:
                aspect_score = 5
                aspect_status = 'Mixed'
                aspect_color = 'orange'
                aspect_text = f'Mixed Aspects'
        
        scores['aspects'] = {'score': aspect_score, 'status': aspect_status, 'color': aspect_color, 'text': aspect_text}
        
        # Overall Strength Score
        if strength >= 8:
            scores['strength'] = {'score': strength, 'status': 'Positive', 'color': 'green', 'text': f'Very Strong ({strength}/10)'}
        elif strength >= 6:
            scores['strength'] = {'score': strength, 'status': 'Positive', 'color': 'green', 'text': f'Strong ({strength}/10)'}
        elif strength <= 3:
            scores['strength'] = {'score': strength, 'status': 'Negative', 'color': 'red', 'text': f'Weak ({strength}/10)'}
        elif strength <= 5:
            scores['strength'] = {'score': strength, 'status': 'Negative', 'color': 'red', 'text': f'Below Average ({strength}/10)'}
        else:
            scores['strength'] = {'score': strength, 'status': 'Neutral', 'color': 'gray', 'text': f'Average ({strength}/10)'}
        
        return scores
    
    def _calculate_house_parameter_scores(self, lord: str, strength: int, occupants: List) -> Dict[str, Any]:
        """Calculate 7th house parameter scores"""
        scores = {}
        
        # House Strength Score
        if strength >= 8:
            scores['strength'] = {'score': strength, 'status': 'Positive', 'color': 'green', 'text': f'Very Strong 7th House ({strength}/10)'}
        elif strength >= 6:
            scores['strength'] = {'score': strength, 'status': 'Positive', 'color': 'green', 'text': f'Strong 7th House ({strength}/10)'}
        elif strength <= 3:
            scores['strength'] = {'score': strength, 'status': 'Negative', 'color': 'red', 'text': f'Weak 7th House ({strength}/10)'}
        else:
            scores['strength'] = {'score': strength, 'status': 'Neutral', 'color': 'gray', 'text': f'Average 7th House ({strength}/10)'}
        
        # Occupants Score
        benefics = ['Jupiter', 'Venus', 'Moon']
        malefics = ['Mars', 'Saturn', 'Rahu', 'Ketu']
        
        if not occupants:
            scores['occupants'] = {'score': 5, 'status': 'Neutral', 'color': 'gray', 'text': 'No Planets in 7th House'}
        else:
            benefic_count = len([p for p in occupants if p in benefics])
            malefic_count = len([p for p in occupants if p in malefics])
            
            if benefic_count > malefic_count:
                scores['occupants'] = {'score': 8, 'status': 'Positive', 'color': 'green', 'text': f'Benefic Planets: {", ".join([p for p in occupants if p in benefics])}'}
            elif malefic_count > benefic_count:
                scores['occupants'] = {'score': 3, 'status': 'Negative', 'color': 'red', 'text': f'Malefic Planets: {", ".join([p for p in occupants if p in malefics])}'}
            else:
                scores['occupants'] = {'score': 5, 'status': 'Mixed', 'color': 'orange', 'text': f'Mixed Planets: {", ".join(occupants)}'}
        
        return scores
    
    def _calculate_d9_positions_corrected(self, jd: float, latitude: float, longitude: float) -> Dict[str, Any]:
        """Calculate D9 positions using corrected method from main.py"""
        import swisseph as swe
        
        # Calculate planetary positions
        planets = {}
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6]):
            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0]
            longitude_deg = pos[0]
            
            # Calculate D9 position using proper Vedic formula
            sign = int(longitude_deg / 30)
            degree_in_sign = longitude_deg % 30
            navamsa_part = int(degree_in_sign / (30/9))
            
            # D9 calculation based on sign type (corrected)
            if sign in [0, 3, 6, 9]:  # Movable signs
                d9_sign = (sign + navamsa_part) % 12
            elif sign in [1, 4, 7, 10]:  # Fixed signs
                d9_sign = ((sign + 8) + navamsa_part) % 12
            else:  # Dual signs [2, 5, 8, 11]
                d9_sign = ((sign + 4) + navamsa_part) % 12
            
            # Calculate actual degree within divisional sign
            part_size = 30.0 / 9
            part_index = int(degree_in_sign / part_size)
            degree_within_part = degree_in_sign % part_size
            actual_degree = (degree_within_part / part_size) * 30.0
            
            divisional_longitude = d9_sign * 30 + actual_degree
            
            planets[planet_names[i]] = {
                'sign': d9_sign,
                'longitude': divisional_longitude
            }
        
        # Calculate D9 ascendant using same method
        houses_data = swe.houses(jd, latitude, longitude, b'P')
        ayanamsa = swe.get_ayanamsa_ut(jd)
        ascendant_tropical = houses_data[1][0]
        ascendant_sidereal = (ascendant_tropical - ayanamsa) % 360
        
        asc_sign = int(ascendant_sidereal / 30)
        asc_degree = ascendant_sidereal % 30
        asc_navamsa_part = int(asc_degree / (30/9))
        
        if asc_sign in [0, 3, 6, 9]:
            d9_asc_sign = (asc_sign + asc_navamsa_part) % 12
        elif asc_sign in [1, 4, 7, 10]:
            d9_asc_sign = ((asc_sign + 8) + asc_navamsa_part) % 12
        else:
            d9_asc_sign = ((asc_sign + 4) + asc_navamsa_part) % 12
        
        # Calculate D9 houses
        houses = []
        for i in range(12):
            house_sign = (d9_asc_sign + i) % 12
            houses.append({
                'sign': house_sign,
                'longitude': house_sign * 30
            })
        
        return {
            'planets': planets,
            'houses': houses,
            'ascendant': d9_asc_sign * 30 + 15
        }
    

    
    def _calculate_yoga_score(self, karakas: Dict, manglik: Dict) -> float:
        """Calculate yoga score for marriage (-1.5 to +1.5)"""
        yoga_score = 0.0
        
        # Benefic yogas
        venus_strength = karakas['venus']['strength']
        jupiter_strength = karakas['jupiter']['strength']
        
        # Malavya Yoga (Venus strong)
        if venus_strength >= 8:
            yoga_score += 0.3
        elif venus_strength >= 6:
            yoga_score += 0.2
        
        # Hamsa Yoga (Jupiter strong)
        if jupiter_strength >= 8:
            yoga_score += 0.3
        elif jupiter_strength >= 6:
            yoga_score += 0.2
        
        # General benefic combination
        if venus_strength >= 6 and jupiter_strength >= 6:
            yoga_score += 0.2
        
        # Malefic yogas
        if manglik['is_manglik']:
            severity = manglik.get('severity', 'Low')
            if severity == 'High':
                yoga_score -= 0.4
            elif severity == 'Medium':
                yoga_score -= 0.2
        
        # Cap between -1.5 and +1.5
        return max(-1.5, min(1.5, yoga_score))
    
    def _get_score_grade(self, score: float) -> str:
        """Convert numeric score to grade"""
        if score >= 8.5:
            return 'Excellent'
        elif score >= 7.0:
            return 'Very Good'
        elif score >= 5.5:
            return 'Good'
        elif score >= 4.0:
            return 'Average'
        else:
            return 'Below Average'
    
    def _get_d9_aspects(self, planet_name: str, planet_sign: int, d9_planets: Dict) -> List[Dict[str, str]]:
        """Calculate aspects to a planet in D9"""
        aspects = []
        
        for other_planet, other_data in d9_planets.items():
            if other_planet == planet_name:
                continue
            
            other_sign = other_data.get('sign', 0)
            
            # 7th aspect (opposition)
            if (other_sign + 6) % 12 == planet_sign:
                aspects.append({'planet': other_planet, 'aspect': '7th'})
            
            # Special aspects
            if other_planet == 'Mars':
                if (other_sign + 3) % 12 == planet_sign:
                    aspects.append({'planet': other_planet, 'aspect': '4th'})
                if (other_sign + 7) % 12 == planet_sign:
                    aspects.append({'planet': other_planet, 'aspect': '8th'})
            elif other_planet == 'Jupiter':
                if (other_sign + 4) % 12 == planet_sign:
                    aspects.append({'planet': other_planet, 'aspect': '5th'})
                if (other_sign + 8) % 12 == planet_sign:
                    aspects.append({'planet': other_planet, 'aspect': '9th'})
            elif other_planet == 'Saturn':
                if (other_sign + 2) % 12 == planet_sign:
                    aspects.append({'planet': other_planet, 'aspect': '3rd'})
                if (other_sign + 9) % 12 == planet_sign:
                    aspects.append({'planet': other_planet, 'aspect': '10th'})
        
        return aspects
    
    def _get_nakshatra_lord(self, longitude: float) -> str:
        """Get nakshatra lord for given longitude"""
        # Nakshatra lords in order
        nakshatra_lords = [
            'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
            'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
            'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
        ]
        
        # Each nakshatra is 13°20' (800 minutes)
        nakshatra_index = int(longitude / (13 + 20/60))
        return nakshatra_lords[nakshatra_index % 27]
    
    def _check_d9_special_conditions(self, planet_name: str, sign: int, longitude: float) -> List[str]:
        """Check for special conditions in D9"""
        conditions = []
        
        # Check for Vargottama (same sign in D1 and D9)
        d1_sign = int(longitude / 30)  # Approximate D1 sign
        if d1_sign == sign:
            conditions.append('Vargottama')
        
        # Check for Pushkara Navamsa (specific degrees)
        degree_in_sign = longitude % 30
        if 10 <= degree_in_sign <= 13.33 or 23.33 <= degree_in_sign <= 26.66:
            conditions.append('Pushkara Navamsa')
        
        return conditions
    
    def _get_positive_negative_marking(self, strength: int, dignity: str, house: int) -> Dict[str, Any]:
        """Calculate positive/negative marking for D9 planet"""
        score = 0
        factors = []
        
        # Strength contribution
        if strength >= 8:
            score += 2
            factors.append("Very Strong")
        elif strength >= 6:
            score += 1
            factors.append("Strong")
        elif strength <= 3:
            score -= 2
            factors.append("Weak")
        elif strength <= 5:
            score -= 1
            factors.append("Below Average")
        
        # Dignity contribution
        if dignity == 'Exalted':
            score += 3
            factors.append("Exalted")
        elif dignity == 'Own':
            score += 2
            factors.append("Own Sign")
        elif dignity == 'Debilitated':
            score -= 3
            factors.append("Debilitated")
        
        # House contribution (beneficial houses)
        if house in [1, 4, 7, 10]:  # Kendra
            score += 1
            factors.append("Kendra House")
        elif house in [5, 9]:  # Trikona
            score += 2
            factors.append("Trikona House")
        elif house in [6, 8, 12]:  # Dusthana
            score -= 1
            factors.append("Dusthana House")
        
        # Determine overall marking
        if score >= 3:
            marking = "Very Positive"
            symbol = "++"
        elif score >= 1:
            marking = "Positive"
            symbol = "+"
        elif score <= -3:
            marking = "Very Negative"
            symbol = "--"
        elif score <= -1:
            marking = "Negative"
            symbol = "-"
        else:
            marking = "Neutral"
            symbol = "="
        
        return {
            'marking': marking,
            'symbol': symbol,
            'score': score,
            'factors': factors
        }
    
    def _detect_d9_yogas(self, d9_chart: Dict) -> List[Dict[str, str]]:
        """Detect yogas in D9 chart"""
        yogas = []
        d9_planets = d9_chart.get('planets', {})
        
        # Check for Raj Yoga in D9 (Kendra-Trikona lords together)
        venus_data = d9_planets.get('Venus', {})
        jupiter_data = d9_planets.get('Jupiter', {})
        
        if venus_data and jupiter_data:
            if venus_data.get('sign') == jupiter_data.get('sign'):
                yogas.append({
                    'name': 'Venus-Jupiter Conjunction in D9',
                    'type': 'benefic',
                    'strength': 'Strong',
                    'description': 'Venus and Jupiter together in D9 creates auspicious marriage yoga',
                    'effect': 'Harmonious marriage with spiritual and material fulfillment'
                })
        
        # Check for Neecha Bhanga in D9
        for planet_name, planet_data in d9_planets.items():
            if planet_name in ['Venus', 'Jupiter', 'Mars', 'Moon']:
                sign = planet_data.get('sign', 0)
                dignity = self._get_planet_dignity(planet_name, sign)
                
                if dignity == 'Exalted':
                    yogas.append({
                        'name': f'{planet_name} Exalted in D9',
                        'type': 'benefic',
                        'strength': 'Very Strong',
                        'description': f'{planet_name} is exalted in D9 Navamsa',
                        'effect': f'Excellent results for {planet_name} significations in marriage'
                    })
        
        return yogas
    
    def _analyze_d9_seventh_house(self, d9_chart: Dict) -> Dict[str, Any]:
        """Analyze 7th house in D9 with enhanced details"""
        d9_houses = d9_chart.get('houses', [])
        if len(d9_houses) < 7:
            return {'error': 'Invalid D9 chart data'}
        
        seventh_house_d9 = d9_houses[6]  # 7th house (0-indexed)
        seventh_sign_d9 = seventh_house_d9.get('sign', 0)
        seventh_lord_d9 = self._get_house_lord(seventh_sign_d9)
        
        # Find planets in 7th house D9
        planets_in_7th_d9 = []
        d9_planets = d9_chart.get('planets', {})
        for planet, data in d9_planets.items():
            if data.get('sign') == seventh_sign_d9:
                planets_in_7th_d9.append(planet)
        
        # Find 7th lord position in D9
        lord_position = None
        if seventh_lord_d9 in d9_planets:
            lord_data = d9_planets[seventh_lord_d9]
            lord_sign = lord_data.get('sign', 0)
            lord_house = 1
            for i, house_data in enumerate(d9_houses):
                if house_data.get('sign') == lord_sign:
                    lord_house = i + 1
                    break
            lord_position = {
                'sign': lord_sign,
                'house': lord_house
            }
        
        # Calculate strength
        strength = self._calculate_house_strength_d9(seventh_lord_d9, d9_planets, planets_in_7th_d9)
        
        # Add positive/negative marking for 7th house
        house_marking = self._get_positive_negative_marking(strength, 'Neutral', 7)
        
        return {
            'sign': seventh_sign_d9,
            'sign_name': self._get_sign_name(seventh_sign_d9),
            'lord': seventh_lord_d9,
            'lord_position': lord_position,
            'planets': planets_in_7th_d9,
            'strength': strength,
            'positive_negative': house_marking
        }