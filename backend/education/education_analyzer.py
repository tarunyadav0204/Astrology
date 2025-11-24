"""
Education Analysis Engine
Classical Vedic Astrology Education Analysis
"""

from calculators.house_strength_calculator import HouseStrengthCalculator
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from calculators.yoga_calculator import YogaCalculator
from calculators.ashtakavarga import AshtakavargaCalculator
from calculators.timing_calculator import TimingCalculator
from calculators.remedy_calculator import RemedyCalculator
from calculators.strength_calculator import StrengthCalculator
from calculators.shadbala_calculator import ShadbalaCalculator
from .constants import *

class EducationAnalyzer:
    """Comprehensive education analysis using classical Vedic astrology"""
    
    def __init__(self, birth_data, chart_data):
        self.birth_data = birth_data
        self.chart_data = chart_data
        
        # Initialize calculators
        self.house_calc = HouseStrengthCalculator(chart_data)
        self.dignity_calc = PlanetaryDignitiesCalculator(chart_data)
        self.yoga_calc = YogaCalculator(birth_data, chart_data)
        self.ashtaka_calc = AshtakavargaCalculator(birth_data, chart_data)
        self.timing_calc = TimingCalculator(chart_data)
        self.remedy_calc = RemedyCalculator(chart_data)
        self.strength_calc = StrengthCalculator(chart_data)
        self.shadbala_calc = ShadbalaCalculator(chart_data)
    
    def analyze_education(self):
        """Complete education analysis"""
        return {
            'overall_score': self._calculate_overall_score(),
            'house_analysis': self._analyze_houses(),
            'planetary_analysis': self._analyze_planets(),
            'yoga_analysis': self._analyze_yogas(),
            'ashtakavarga_analysis': self._analyze_ashtakavarga(),
            'shadbala_analysis': self._analyze_shadbala(),
            'timing_analysis': self._analyze_timing(),
            'subject_recommendations': self._get_subject_recommendations(),
            'remedies': self._get_remedies()
        }
    
    def _calculate_overall_score(self):
        """Calculate overall education strength score"""
        house_score = self._get_house_score()
        planet_score = self._get_planetary_score()
        yoga_score = self._get_yoga_score()
        ashtaka_score = self._get_ashtakavarga_score()
        
        total_score = (
            house_score * STRENGTH_WEIGHTS['house_strength'] +
            planet_score * STRENGTH_WEIGHTS['planetary_dignities'] +
            yoga_score * STRENGTH_WEIGHTS['yogas'] +
            ashtaka_score * STRENGTH_WEIGHTS['ashtakavarga']
        )
        
        return {
            'total_score': round(total_score, 1),
            'grade': self._get_grade(total_score),
            'breakdown': {
                'house_strength': round(house_score, 1),
                'planetary_strength': round(planet_score, 1),
                'yoga_strength': round(yoga_score, 1),
                'ashtakavarga_strength': round(ashtaka_score, 1)
            }
        }
    
    def _analyze_houses(self):
        """Analyze education houses (4th, 5th, 9th)"""
        house_analysis = {}
        
        for house_num in [4, 5, 9]:
            strength = self.house_calc.calculate_house_strength(house_num)
            house_info = EDUCATION_HOUSES[house_num]
            
            house_analysis[house_num] = {
                'name': house_info['name'],
                'description': house_info['description'],
                'strength': strength['total_strength'],
                'grade': strength['grade'],
                'interpretation': strength['interpretation'],
                'factors': strength['factors']
            }
        
        return house_analysis
    
    def _analyze_planets(self):
        """Analyze education-related planets using multiple calculators"""
        dignities = self.dignity_calc.calculate_planetary_dignities()
        shadbala_results = self.shadbala_calc.calculate_shadbala()
        planet_analysis = {}
        
        for planet, info in EDUCATION_PLANETS.items():
            if planet in dignities:
                dignity_data = dignities[planet]
                shadbala_data = shadbala_results.get(planet, {})
                score = self._calculate_planet_score(dignity_data, shadbala_data)
                
                planet_analysis[planet] = {
                    'significance': info['significance'],
                    'dignity': dignity_data['dignity'],
                    'strength_multiplier': dignity_data['strength_multiplier'],
                    'shadbala_grade': shadbala_data.get('grade', 'Unknown'),
                    'shadbala_rupas': shadbala_data.get('total_rupas', 0),
                    'score': score,
                    'states': dignity_data['states'],
                    'house': dignity_data.get('house', 1),
                    'sign': dignity_data['sign']
                }
        
        return planet_analysis
    
    def _analyze_yogas(self):
        """Analyze education-related yogas using yoga calculator"""
        education_yogas = self.yoga_calc.get_education_yogas_only()
        
        return {
            'yogas_found': education_yogas,
            'total_count': len(education_yogas),
            'strength_contribution': self._calculate_yoga_strength(education_yogas)
        }
    
    def _analyze_ashtakavarga(self):
        """Analyze Ashtakavarga for education houses"""
        sarva = self.ashtaka_calc.calculate_sarvashtakavarga()
        bindus = sarva['sarvashtakavarga']
        
        education_bindus = {}
        for house_num in [4, 5, 9]:
            # Convert house to sign (assuming Aries ascendant for simplicity)
            asc_sign = int(self.chart_data.get('ascendant', 0) / 30)
            house_sign = (asc_sign + house_num - 1) % 12
            
            education_bindus[house_num] = {
                'bindus': bindus[house_sign],
                'strength': self._interpret_bindus(bindus[house_sign]),
                'house_name': EDUCATION_HOUSES[house_num]['name']
            }
        
        return education_bindus
    
    def _analyze_shadbala(self):
        """Analyze Shadbala for education planets"""
        shadbala_results = self.shadbala_calc.calculate_shadbala()
        education_shadbala = {}
        
        for planet in EDUCATION_PLANETS.keys():
            if planet in shadbala_results:
                shadbala_data = shadbala_results[planet]
                education_shadbala[planet] = {
                    'total_rupas': shadbala_data['total_rupas'],
                    'grade': shadbala_data['grade'],
                    'components': shadbala_data['components'],
                    'interpretation': self._interpret_shadbala_grade(shadbala_data['grade'])
                }
        
        return education_shadbala
    
    def _interpret_shadbala_grade(self, grade):
        """Interpret shadbala grade for education"""
        interpretations = {
            'Excellent': 'Very strong planetary influence on education',
            'Good': 'Favorable planetary support for learning',
            'Average': 'Moderate planetary influence on education',
            'Weak': 'Planetary strength needs improvement for better educational outcomes'
        }
        return interpretations.get(grade, 'Unknown planetary strength')
    
    def _analyze_timing(self):
        """Analyze timing for educational events"""
        timing_analysis = {}
        
        for house_num in [4, 5, 9]:
            timing_analysis[house_num] = {
                'house_name': EDUCATION_HOUSES[house_num]['name'],
                'timing_indicators': self.timing_calc.get_timing_indicators(house_num),
                'favorable_periods': self.timing_calc.get_favorable_periods(house_num)
            }
        
        return timing_analysis
    
    def _get_subject_recommendations(self):
        """Get subject recommendations based on planetary strengths"""
        dignities = self.dignity_calc.calculate_planetary_dignities()
        recommendations = {}
        
        for planet, subjects in SUBJECT_RECOMMENDATIONS.items():
            if planet in dignities:
                dignity_data = dignities[planet]
                score = self._calculate_planet_score(dignity_data)
                
                if score >= 60:  # Only recommend if planet is reasonably strong
                    recommendations[planet] = {
                        'subjects': subjects,
                        'strength': score,
                        'reason': f"{planet} is {dignity_data['dignity']} with strength {score}"
                    }
        
        return recommendations
    
    def _get_remedies(self):
        """Get remedies using remedy calculator"""
        remedies = []
        
        # Analyze weak areas and suggest remedies
        house_analysis = self._analyze_houses()
        
        for house_num, data in house_analysis.items():
            if data['strength'] < 50:
                house_remedies = self.remedy_calc.suggest_remedies(house_num, data['strength'])
                remedies.extend([f"{EDUCATION_HOUSES[house_num]['name']}: {remedy}" for remedy in house_remedies[:2]])
        
        return remedies[:6]  # Limit to 6 remedies
    
    def _get_house_score(self):
        """Calculate weighted house score"""
        total_score = 0
        
        for house_num, weight in HOUSE_STRENGTH_WEIGHTS.items():
            strength = self.house_calc.calculate_house_strength(house_num)
            total_score += strength['total_strength'] * weight
        
        return total_score
    
    def _get_planetary_score(self):
        """Calculate weighted planetary score using multiple calculators"""
        dignities = self.dignity_calc.calculate_planetary_dignities()
        shadbala_results = self.shadbala_calc.calculate_shadbala()
        total_score = 0
        total_weight = 0
        
        for planet, info in EDUCATION_PLANETS.items():
            if planet in dignities:
                shadbala_data = shadbala_results.get(planet, {})
                score = self._calculate_planet_score(dignities[planet], shadbala_data)
                total_score += score * info['weight']
                total_weight += info['weight']
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def _calculate_planet_score(self, dignity_data, shadbala_data=None):
        """Calculate individual planet score using dignity and shadbala"""
        base_score = DIGNITY_SCORES.get(dignity_data['dignity'], 50)
        
        # Apply functional nature multiplier
        functional_mult = FUNCTIONAL_MULTIPLIERS.get(dignity_data.get('functional_nature', 'neutral'), 1.0)
        
        # Apply combustion effects
        combustion_mult = COMBUSTION_EFFECTS.get(dignity_data.get('combustion_status', 'normal'), 1.0)
        
        # Apply shadbala strength if available
        shadbala_mult = 1.0
        if shadbala_data:
            rupas = shadbala_data.get('total_rupas', 3)
            if rupas >= 6:
                shadbala_mult = 1.3
            elif rupas >= 4.5:
                shadbala_mult = 1.15
            elif rupas >= 3:
                shadbala_mult = 1.0
            else:
                shadbala_mult = 0.85
        
        final_score = base_score * functional_mult * combustion_mult * shadbala_mult
        return min(100, max(0, final_score))
    
    def _get_yoga_score(self):
        """Calculate yoga contribution score using yoga calculator"""
        education_yogas = self.yoga_calc.get_education_yogas_only()
        return self._calculate_yoga_strength(education_yogas)
    
    def _get_ashtakavarga_score(self):
        """Calculate Ashtakavarga score"""
        sarva = self.ashtaka_calc.calculate_sarvashtakavarga()
        bindus = sarva['sarvashtakavarga']
        
        asc_sign = int(self.chart_data.get('ascendant', 0) / 30)
        total_score = 0
        
        for house_num, weight in HOUSE_STRENGTH_WEIGHTS.items():
            house_sign = (asc_sign + house_num - 1) % 12
            bindu_count = bindus[house_sign]
            
            # Convert bindus to score (30+ = 100, 25-29 = 75, etc.)
            if bindu_count >= 30:
                score = 100
            elif bindu_count >= 28:
                score = 85
            elif bindu_count >= 25:
                score = 70
            elif bindu_count >= 22:
                score = 55
            else:
                score = 30
            
            total_score += score * weight
        
        return total_score
    
    def _calculate_yoga_strength(self, yogas):
        """Calculate total yoga strength using predefined strengths"""
        if not yogas:
            return 0
        
        total_strength = 0
        for yoga in yogas:
            yoga_name = yoga.get('name', '').lower()
            
            # Use predefined strengths or fallback to strength level
            if yoga_name in EDUCATION_YOGA_STRENGTHS:
                total_strength += EDUCATION_YOGA_STRENGTHS[yoga_name] / 4  # Scale down
            else:
                strength = yoga.get('strength', 'Medium')
                if strength == 'High':
                    total_strength += 25
                elif strength == 'Medium':
                    total_strength += 15
                else:
                    total_strength += 10
        
        return min(100, total_strength)
    
    def _interpret_bindus(self, bindu_count):
        """Interpret Ashtakavarga bindu count"""
        if bindu_count >= ASHTAKAVARGA_THRESHOLDS['excellent']:
            return 'Excellent'
        elif bindu_count >= ASHTAKAVARGA_THRESHOLDS['good']:
            return 'Good'
        elif bindu_count >= ASHTAKAVARGA_THRESHOLDS['average']:
            return 'Average'
        else:
            return 'Weak'
    
    def _get_grade(self, score):
        """Get grade based on score"""
        for threshold, grade in sorted(GRADE_MAPPING.items(), reverse=True):
            if score >= threshold:
                return grade
        return 'F'
    
