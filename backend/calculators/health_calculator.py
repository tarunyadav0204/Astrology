from .base_calculator import BaseCalculator
from .planet_analyzer import PlanetAnalyzer
from .house_analyzer import HouseAnalyzer
from .house_strength_calculator import HouseStrengthCalculator
from .aspect_calculator import AspectCalculator
from .planetary_dignities_calculator import PlanetaryDignitiesCalculator
from .shadbala_calculator import ShadbalaCalculator
from .yoga_calculator import YogaCalculator

class HealthCalculator(BaseCalculator):
    """Comprehensive health analysis using existing calculators"""
    
    def __init__(self, chart_data=None, birth_data=None):
        super().__init__(chart_data or {})
        self.birth_data = birth_data
        
        # Initialize existing calculators
        self.planet_analyzer = PlanetAnalyzer(chart_data, birth_data)
        self.house_analyzer = HouseAnalyzer(chart_data, birth_data)
        self.house_strength_calc = HouseStrengthCalculator(chart_data)
        self.aspect_calc = AspectCalculator(chart_data)
        self.dignities_calc = PlanetaryDignitiesCalculator(chart_data)
        self.shadbala_calc = ShadbalaCalculator(chart_data)
        self.yoga_calc = YogaCalculator(chart_data=chart_data)
        
        # Health house mappings
        self.HEALTH_HOUSES = {
            1: "Physical body and vitality",
            2: "Face, speech, family health patterns",
            6: "Diseases and immunity", 
            7: "Partnerships affecting health",
            8: "Chronic illness and longevity",
            12: "Hospitalization and mental health"
        }
        
        # Health house lords to analyze
        self.HEALTH_HOUSE_LORDS = [1, 2, 6, 7, 8, 12]
        
        # Planet-body system mapping
        self.PLANET_BODY_MAPPING = {
            'Sun': {'systems': ['Heart', 'Spine', 'Vitality'], 'element': 'Fire'},
            'Moon': {'systems': ['Mind', 'Fluids', 'Digestive'], 'element': 'Water'},
            'Mars': {'systems': ['Blood', 'Muscles', 'Energy'], 'element': 'Fire'},
            'Mercury': {'systems': ['Nervous', 'Respiratory', 'Communication'], 'element': 'Air'},
            'Jupiter': {'systems': ['Liver', 'Immunity', 'Growth'], 'element': 'Air'},
            'Venus': {'systems': ['Reproductive', 'Hormones', 'Beauty'], 'element': 'Water'},
            'Saturn': {'systems': ['Bones', 'Teeth', 'Chronic'], 'element': 'Earth'},
            'Rahu': {'systems': ['Toxins', 'Stress', 'Nervous'], 'element': 'Air'},
            'Ketu': {'systems': ['Hidden ailments', 'Detachment', 'Spiritual'], 'element': 'Fire'}
        }
        
        # Natural significators for houses
        self.NATURAL_SIGNIFICATORS = {
            1: ['Sun'],  # Self, vitality
            2: ['Jupiter'],  # Wealth, speech
            3: ['Mars'],  # Courage, siblings
            4: ['Moon'],  # Mother, home
            5: ['Jupiter'],  # Children, intelligence
            6: ['Mars', 'Saturn'],  # Enemies, diseases
            7: ['Venus'],  # Spouse, partnerships
            8: ['Saturn', 'Ketu'],  # Longevity, transformation
            9: ['Jupiter'],  # Father, dharma
            10: ['Sun', 'Mercury'],  # Career, reputation
            11: ['Jupiter'],  # Gains, friends
            12: ['Saturn', 'Ketu']  # Loss, moksha
        }
    
    def calculate_overall_health(self):
        """Calculate overall health assessment"""
        planet_analysis = self._analyze_health_planets()
        house_analysis = self._analyze_health_houses()
        yoga_analysis = self._analyze_health_yogas()
        health_score = self._calculate_health_score(planet_analysis, house_analysis, yoga_analysis)
        
        return {
            'planet_analysis': planet_analysis,
            'house_analysis': house_analysis,
            'yoga_analysis': yoga_analysis,
            'health_score': health_score['score'],
            'health_score_breakdown': health_score['calculation_breakdown'],
            'constitution_type': self._determine_constitution(),
            'element_balance': self._calculate_element_balance(),
            'health_timeline': self._calculate_health_timeline(),
            'health_remedies': self._calculate_health_remedies()
        }
    
    def _analyze_health_planets(self):
        """Analyze all planets for health impact"""
        planet_health_analysis = {}
        
        for planet_name, planet_data in self.chart_data['planets'].items():
            # Skip planets that don't have health mappings (like Gulika)
            if planet_name not in self.PLANET_BODY_MAPPING:
                continue
                
            analysis = self.planet_analyzer.analyze_planet(planet_name)
            health_impact = self._get_planet_health_impact(planet_name, analysis)
            
            planet_health_analysis[planet_name] = {
                'basic_analysis': analysis,
                'health_impact': health_impact,
                'body_systems': self.PLANET_BODY_MAPPING[planet_name]['systems'],
                'element': self.PLANET_BODY_MAPPING[planet_name]['element']
            }
        
        return planet_health_analysis
    
    def _analyze_health_houses(self):
        """Analyze health-related houses using HouseAnalyzer"""
        house_health_analysis = {}
        
        for house_num in self.HEALTH_HOUSE_LORDS:
            house_analysis = self.house_analyzer.analyze_house(house_num)
            health_interpretation = self._get_house_health_interpretation(house_num, house_analysis)
            
            house_health_analysis[house_num] = {
                'house_analysis': house_analysis,
                'health_significance': self.HEALTH_HOUSES[house_num],
                'health_interpretation': health_interpretation
            }
        
        return house_health_analysis
    
    def _analyze_health_yogas(self):
        """Analyze health-related yogas"""
        health_yogas = self.yoga_calc.calculate_health_yogas()
        
        yoga_analysis = {
            'beneficial_yogas': [],
            'affliction_yogas': [],
            'total_beneficial': 0,
            'total_afflictions': 0
        }
        
        for yoga in health_yogas:
            if yoga.get('type') == 'beneficial':
                yoga_analysis['beneficial_yogas'].append(yoga)
                yoga_analysis['total_beneficial'] += 1
            elif yoga.get('type') == 'affliction':
                yoga_analysis['affliction_yogas'].append(yoga)
                yoga_analysis['total_afflictions'] += 1
        
        return yoga_analysis
    
    def _calculate_health_score(self, planet_analysis, house_analysis, yoga_analysis):
        """Calculate overall health score with detailed breakdown"""
        base_score = 50
        calculation_breakdown = ["Base Score: 50"]
        
        # Planet contributions
        planet_score = 0
        for planet_name, analysis in planet_analysis.items():
            impact_type = analysis['health_impact']['impact_type']
            if impact_type == 'Very Positive':
                planet_score += 8
                calculation_breakdown.append(f"{planet_name}: +8 (Very Positive)")
            elif impact_type == 'Challenging':
                planet_score -= 6
                calculation_breakdown.append(f"{planet_name}: -6 (Challenging)")
            elif impact_type == 'Gandanta Afflicted':
                planet_score -= 12
                calculation_breakdown.append(f"{planet_name}: -12 (Gandanta Afflicted)")
        
        base_score += planet_score
        calculation_breakdown.append(f"Planet Total: {planet_score:+d}")
        
        # House contributions (adjusted for health interpretation)
        house_score = 0
        for house_num, analysis in house_analysis.items():
            house_strength = analysis['house_analysis']['overall_house_assessment']['overall_strength_score']
            
            # For 6th, 8th, 12th houses, weakness can be good (fewer diseases, less suffering)
            if house_num == 6:  # 6th house - diseases
                # Weak 6th house = fewer diseases = good for health
                contribution = (50 - house_strength) * 0.3  # Inverted
                house_score += contribution
                calculation_breakdown.append(f"{house_num}th House: {contribution:+.1f} (Diseases - weak is good)")
            elif house_num == 8:  # 8th house - chronic illness
                # Weak 8th house = less chronic illness = good for health
                contribution = (50 - house_strength) * 0.2  # Inverted, less weight
                house_score += contribution
                calculation_breakdown.append(f"{house_num}th House: {contribution:+.1f} (Chronic illness - weak is good)")
            elif house_num == 12:  # 12th house - hospitalization
                # Weak 12th house = less hospitalization = good for health
                contribution = (50 - house_strength) * 0.2  # Inverted, less weight
                house_score += contribution
                calculation_breakdown.append(f"{house_num}th House: {contribution:+.1f} (Hospitalization - weak is good)")
            elif house_num == 1:  # 1st house - vitality
                # Strong 1st house = good vitality = good for health
                contribution = (house_strength - 50) * 0.4
                house_score += contribution
                calculation_breakdown.append(f"{house_num}th House: {contribution:+.1f} (Vitality - strong is good)")
            else:  # 2nd, 7th houses - secondary health houses
                contribution = (house_strength - 50) * 0.15
                house_score += contribution
                calculation_breakdown.append(f"{house_num}th House: {contribution:+.1f} (Secondary)")
        
        base_score += house_score
        calculation_breakdown.append(f"House Total: {house_score:+.1f}")
        
        # Yoga contributions
        yoga_score = yoga_analysis['total_beneficial'] * 5 - yoga_analysis['total_afflictions'] * 8
        base_score += yoga_score
        calculation_breakdown.append(f"Beneficial Yogas: +{yoga_analysis['total_beneficial'] * 5}")
        calculation_breakdown.append(f"Affliction Yogas: -{yoga_analysis['total_afflictions'] * 8}")
        calculation_breakdown.append(f"Yoga Total: {yoga_score:+d}")
        
        final_score = min(100, max(0, int(base_score)))
        calculation_breakdown.append(f"Final Score: {final_score}")
        
        return {
            'score': final_score,
            'calculation_breakdown': calculation_breakdown
        }
    
    def _determine_constitution(self):
        """Determine Ayurvedic constitution type"""
        element_balance = self._calculate_element_balance()
        
        if element_balance['Fire'] > 40:
            return 'Pitta (Fire dominant)'
        elif element_balance['Water'] > 40:
            return 'Kapha (Water dominant)'
        elif element_balance['Air'] > 40:
            return 'Vata (Air dominant)'
        else:
            return 'Mixed constitution'
    
    def _calculate_element_balance(self):
        """Calculate elemental balance"""
        elements = {'Fire': 0, 'Water': 0, 'Air': 0, 'Earth': 0}
        planets = self.chart_data.get('planets', {})
        
        for planet_name, planet_data in planets.items():
            if planet_name in self.PLANET_BODY_MAPPING:
                element = self.PLANET_BODY_MAPPING[planet_name]['element']
                # Weight by planet strength
                analysis = self.planet_analyzer.analyze_planet(planet_name)
                strength = analysis['strength_analysis']['shadbala_points']
                elements[element] += strength
        
        # Normalize to percentages
        total = sum(elements.values())
        if total > 0:
            for element in elements:
                elements[element] = round((elements[element] / total) * 100, 1)
        
        return elements
    
    def _get_health_benefit(self, planet_name, planet_data):
        """Get health benefit description"""
        house = planet_data.get('house', 1)
        
        benefits = {
            ('Sun', 10): 'excellent vitality and leadership in health matters',
            ('Jupiter', 1): 'natural healing ability and strong immunity',
            ('Moon', 4): 'emotional stability and good digestive health',
            ('Venus', 7): 'hormonal balance and reproductive health',
            ('Mercury', 3): 'strong nervous system and respiratory health'
        }
        
        return benefits.get((planet_name, house), f'positive influence on {self.PLANET_BODY_MAPPING[planet_name]["systems"][0].lower()}')
    
    def _get_health_concern(self, planet_name, planet_data, analysis):
        """Get health concern description"""
        house = planet_data.get('house', 1)
        
        concerns = {
            ('Saturn', 6): 'chronic digestive issues',
            ('Mars', 1): 'inflammation and blood pressure issues',
            ('Rahu', 12): 'mental stress and sleep disorders',
            ('Ketu', 8): 'hidden health problems'
        }
        
        return concerns.get((planet_name, house), f'issues with {self.PLANET_BODY_MAPPING[planet_name]["systems"][0].lower()}')
    
    def _get_health_reason(self, planet_name, planet_data, effect_type):
        """Get astrological reasoning"""
        house = planet_data.get('house', 1)
        house_name = self.get_house_name(house)
        
        if effect_type == 'positive':
            return f"{planet_name} represents {self.PLANET_BODY_MAPPING[planet_name]['systems'][0].lower()} and {house_name} shows {self.HEALTH_HOUSES.get(house, 'life area')}"
        else:
            return f"{planet_name} creates {self.PLANET_BODY_MAPPING[planet_name]['systems'][0].lower()} issues and {house_name} governs {self.HEALTH_HOUSES.get(house, 'life challenges')}"
    
    def _calculate_strength_factor(self, analysis):
        """Calculate strength factor (0-100)"""
        shadbala_points = analysis['strength_analysis']['shadbala_points']
        dignity_multiplier = analysis['dignity_analysis']['strength_multiplier']
        
        return min(100, int(shadbala_points * dignity_multiplier * 10))
    
    def _calculate_concern_severity(self, analysis):
        """Calculate concern severity"""
        dignity = analysis['dignity_analysis']['dignity']
        combustion = analysis['combustion_status']['is_combust']
        
        if dignity == 'debilitated' or combustion:
            return 'High'
        elif dignity in ['enemy_sign', 'neutral']:
            return 'Medium'
        else:
            return 'Low'
    
    def _severity_to_number(self, severity):
        """Convert severity to number for sorting"""
        return {'High': 3, 'Medium': 2, 'Low': 1}.get(severity, 1)
    
    def _get_affliction_type(self, analysis):
        """Get type of affliction"""
        if analysis['combustion_status']['is_combust']:
            return 'combust'
        elif analysis['dignity_analysis']['dignity'] == 'debilitated':
            return 'debilitated'
        else:
            return 'afflicted'
    
    def get_house_name(self, house_num):
        """Get house name"""
        house_names = {
            1: '1st house', 2: '2nd house', 3: '3rd house', 4: '4th house',
            5: '5th house', 6: '6th house', 7: '7th house', 8: '8th house',
            9: '9th house', 10: '10th house', 11: '11th house', 12: '12th house'
        }
        return house_names.get(house_num, f'{house_num}th house')
    
    def _is_natural_significator(self, planet_name, house_num):
        """Check if planet is natural significator for house"""
        return planet_name in self.NATURAL_SIGNIFICATORS.get(house_num, [])
    
    def _get_viparita_yoga_type(self, planet_lordships, planet_house):
        """Determine Viparita Raja Yoga type"""
        if 6 in planet_lordships and planet_house in [8, 12]:
            return 'Sarala Yoga'  # 6th lord in 8th/12th
        elif 8 in planet_lordships and planet_house in [6, 12]:
            return 'Vimala Yoga'  # 8th lord in 6th/12th
        elif 12 in planet_lordships and planet_house in [6, 8]:
            return 'Vimala Yoga'  # 12th lord in 6th/8th
        return None
    
    def _is_dusthana_lord(self, planet_lordships):
        """Check if planet is dusthana lord"""
        return any(h in [6, 8, 12] for h in planet_lordships)
    
    def _classify_planet_nature(self, planet_name, planet_analysis, current_house):
        """Classify planet nature considering all factors"""
        planet_lordships = planet_analysis.get('lordship_analysis', {}).get('houses_ruled', [])
        planet_house = planet_analysis.get('basic_info', {}).get('house', current_house)
        
        # Check for Viparita Raja Yoga
        viparita_type = self._get_viparita_yoga_type(planet_lordships, planet_house)
        if viparita_type:
            return 'viparita', viparita_type
        
        # Check if natural significator
        if self._is_natural_significator(planet_name, current_house):
            return 'natural_significator', f'natural {current_house}th house significator'
        
        # Check if dusthana lord
        if self._is_dusthana_lord(planet_lordships):
            return 'dusthana_lord', 'dusthana lord'
        
        # Regular classification
        if planet_name in ['Mars', 'Saturn', 'Rahu', 'Ketu']:
            return 'malefic', 'malefic'
        elif planet_name in ['Jupiter', 'Venus']:
            return 'benefic', 'benefic'
        elif planet_name == 'Mercury':
            return 'neutral', 'neutral'
        else:
            return 'luminaries', 'luminary'
    
    def _get_planet_health_impact(self, planet_name, analysis):
        """Get planet's health impact with inline reasoning"""
        dignity = analysis['dignity_analysis']['dignity']
        house = analysis['basic_info']['house']
        gandanta_analysis = analysis.get('gandanta_analysis', {})
        combustion = analysis['combustion_status']['is_combust']
        shadbala_rupas = analysis['strength_analysis']['shadbala_rupas']
        
        # Build inline reasoning
        reasons = []
        
        # Check for Gandanta impact first
        if gandanta_analysis.get('is_gandanta', False):
            intensity = gandanta_analysis.get('intensity', 'Medium')
            gandanta_type = gandanta_analysis.get('gandanta_type', '')
            longitude = analysis['basic_info']['longitude']

            reasons.append(f"in Gandanta ({gandanta_type}, {intensity} intensity)")
            gandanta_implications = self._get_gandanta_health_implications(planet_name, gandanta_analysis)
            return {
                'impact_type': 'Gandanta Afflicted',
                'severity': 'High',
                'implications': gandanta_implications,
                'reasoning': f"{planet_name} is {', '.join(reasons)}"
            }
        
        # Build reasoning for regular analysis
        if dignity == 'debilitated':
            reasons.append("debilitated")
        elif dignity in ['exalted', 'own_sign']:
            reasons.append(f"{dignity}")
        
        if house in [6, 8, 12]:
            reasons.append(f"in {house}th house (dusthana)")
        elif house in [1, 5, 9]:
            reasons.append(f"in {house}th house (favorable)")
        
        if combustion:
            reasons.append("combust")
        
        if shadbala_rupas < 3:
            reasons.append(f"weak strength ({shadbala_rupas:.1f} rupas)")
        elif shadbala_rupas >= 5:
            reasons.append(f"good strength ({shadbala_rupas:.1f} rupas)")
        
        reasoning = f"{planet_name} is {', '.join(reasons)}" if reasons else f"{planet_name} has moderate placement"
        
        # Regular analysis
        if dignity in ['exalted', 'own_sign'] and house in [1, 5, 9]:
            return {
                'impact_type': 'Very Positive',
                'severity': 'Beneficial',
                'implications': [f'Strong {planet_name} enhances {self.PLANET_BODY_MAPPING.get(planet_name, {"systems": ["general health"]})["systems"][0].lower()}'],
                'reasoning': reasoning
            }
        elif dignity == 'debilitated' or house in [6, 8, 12]:
            return {
                'impact_type': 'Challenging',
                'severity': 'Medium',
                'implications': [f'Weak {planet_name} may affect {self.PLANET_BODY_MAPPING.get(planet_name, {"systems": ["general health"]})["systems"][0].lower()}'],
                'reasoning': reasoning
            }
        else:

            return {
                'impact_type': 'Neutral',
                'severity': 'Low',
                'implications': [f'Moderate influence on {self.PLANET_BODY_MAPPING.get(planet_name, {"systems": ["general health"]})["systems"][0].lower()}'],
                'reasoning': reasoning
            }
    
    def _get_house_health_interpretation(self, house_num, house_analysis):
        """Get house health interpretation with inline reasoning including aspects"""
        strength = house_analysis['overall_house_assessment']['overall_strength_score']
        lord_analysis = house_analysis['house_lord_analysis']
        lord_planet = lord_analysis['basic_info']['planet']
        lord_house = lord_analysis['basic_info']['house']
        lord_dignity = lord_analysis['dignity_analysis']['dignity']
        
        # Build inline reasoning
        reasons = []
        
        # Lord placement reasoning
        if lord_house in [6, 8, 12]:
            reasons.append(f"{lord_planet} (lord) in {lord_house}th house creates challenges")
        elif lord_house in [1, 4, 5, 7, 9, 10]:
            reasons.append(f"{lord_planet} (lord) in {lord_house}th house is favorable")
        
        # Lord dignity reasoning
        if lord_dignity == 'debilitated':
            reasons.append(f"{lord_planet} is debilitated")
        elif lord_dignity in ['exalted', 'own_sign']:
            reasons.append(f"{lord_planet} is {lord_dignity}")
        
        # Lord aspects reasoning - check if lord is receiving aspects
        lord_aspects = lord_analysis.get('aspects_received', {})
        if lord_aspects.get('has_aspects', False):
            aspects_list = lord_aspects.get('aspects', [])
            malefic_aspects = []
            benefic_aspects = []
            
            for aspect in aspects_list:
                aspecting_planet = aspect['aspecting_planet']
                # Check if aspecting planet is dusthana lord
                if aspecting_planet in ['Mars', 'Saturn', 'Rahu', 'Ketu']:
                    malefic_aspects.append(aspect)
                elif aspecting_planet == 'Mercury':
                    # Check Mercury's lordship from chart data
                    mercury_data = self.chart_data.get('planets', {}).get('Mercury', {})
                    mercury_houses = mercury_data.get('houses_ruled', [])
                    if any(h in [6, 8, 12] for h in mercury_houses):
                        malefic_aspects.append(aspect)  # Mercury as dusthana lord
                    else:
                        benefic_aspects.append(aspect)  # Mercury as benefic
                elif aspecting_planet in ['Jupiter', 'Venus']:
                    benefic_aspects.append(aspect)
            
            if malefic_aspects:
                aspecters = [f"{a['aspecting_planet']}'s {a['aspect_type']}" for a in malefic_aspects]
                reasons.append(f"{lord_planet} (lord) afflicted by {', '.join(aspecters)}")
            elif benefic_aspects:
                aspecters = [f"{a['aspecting_planet']}'s {a['aspect_type']}" for a in benefic_aspects]
                reasons.append(f"{lord_planet} (lord) blessed by {', '.join(aspecters)}")
        
        # Resident planets reasoning with conjunction analysis
        residents = house_analysis.get('resident_planets', [])
        if len(residents) > 1:
            # Multiple planets - analyze conjunctions with comprehensive classification
            malefics = []
            benefics = []
            viparita_planets = []
            natural_significators = []
            
            for resident in residents:
                planet_name = resident['planet']
                planet_analysis = resident['analysis']
                
                # Use comprehensive planet classification
                nature, description = self._classify_planet_nature(planet_name, planet_analysis, house_num)
                
                if nature == 'viparita':
                    viparita_planets.append(f"{planet_name} ({description})")
                elif nature == 'natural_significator':
                    natural_significators.append(f"{planet_name} ({description})")
                elif nature in ['dusthana_lord', 'malefic']:
                    malefics.append(f"{planet_name} ({description})")
                else:
                    benefics.append(planet_name)
            
            # Combine positive factors
            all_positive = benefics + viparita_planets + natural_significators
            
            if viparita_planets and natural_significators:
                reasons.append(f"Beneficial conjunction of {', '.join(viparita_planets)} with {', '.join(natural_significators)}")
            elif viparita_planets and malefics:
                reasons.append(f"Conjunction includes Viparita planets {', '.join(viparita_planets)} with malefics {', '.join(malefics)}")
            elif malefics and all_positive:
                reasons.append(f"Mixed conjunction of {', '.join(malefics)} (challenging) with {', '.join(all_positive)} (beneficial)")
            elif len(malefics) > 1:
                reasons.append(f"Multiple challenging planets conjunct: {', '.join(malefics)}")
            elif malefics:
                reasons.append(f"{', '.join(malefics)} conjunct with other planets")
        
        # Individual resident planet analysis with comprehensive classification
        for resident in residents:
            planet_name = resident['planet']
            planet_analysis = resident['analysis']
            
            if planet_analysis['dignity_analysis']['dignity'] == 'debilitated':
                reasons.append(f"{planet_name} (resident) is debilitated")
            else:
                # Use comprehensive planet classification
                nature, description = self._classify_planet_nature(planet_name, planet_analysis, house_num)
                
                if nature == 'viparita':
                    reasons.append(f"{planet_name} ({description}) creates beneficial effects")
                elif nature == 'natural_significator':
                    reasons.append(f"{planet_name} ({description}) comfortable in natural domain")
                elif nature == 'dusthana_lord':
                    reasons.append(f"{planet_name} ({description}) afflicts the house")
                elif nature == 'malefic':
                    reasons.append(f"{planet_name} (malefic resident) afflicts the house")
                elif nature == 'benefic' and planet_analysis['dignity_analysis']['dignity'] in ['exalted', 'own_sign']:
                    reasons.append(f"{planet_name} (benefic resident) strengthens the house")
        
        # House aspects reasoning
        house_aspects = house_analysis.get('aspects_received', [])
        malefic_house_aspects = [a for a in house_aspects if a['aspecting_planet'] in ['Mars', 'Saturn', 'Rahu', 'Ketu']]
        benefic_house_aspects = [a for a in house_aspects if a['aspecting_planet'] in ['Jupiter', 'Venus']]
        
        if malefic_house_aspects:
            aspecters = [a['aspecting_planet'] for a in malefic_house_aspects]
            reasons.append(f"House afflicted by {', '.join(aspecters)} aspects")
        
        if benefic_house_aspects:
            aspecters = [a['aspecting_planet'] for a in benefic_house_aspects]
            reasons.append(f"House blessed by {', '.join(aspecters)} aspects")
        
        reason_text = " because " + ", ".join(reasons) if reasons else ""
        
        # Separate positive and negative factors for balanced reasoning
        positive_factors = []
        negative_factors = []
        
        # Categorize reasons
        for reason in reasons:
            if any(word in reason.lower() for word in ['favorable', 'exalted', 'own_sign', 'blessed', 'strengthens']):
                positive_factors.append(reason)
            elif any(word in reason.lower() for word in ['debilitated', 'challenges', 'afflicts', 'afflicted', 'malefic', 'conjunction', 'dusthana lord']):
                negative_factors.append(reason)
            elif any(word in reason.lower() for word in ['viparita', 'beneficial effects', 'comfortable', 'natural domain', 'beneficial conjunction', 'vimala yoga', 'sarala yoga']):
                # Viparita yoga, natural significators, beneficial conjunctions - positive
                positive_factors.append(reason)
            else:
                # Neutral factors - add to context but don't categorize as positive/negative
                pass
        
        # Build balanced interpretation
        strength_desc = 'strong' if strength > 70 else 'moderate' if strength > 40 else 'weak'
        
        # Check for additional factors not captured in reasons
        additional_factors = []
        if lord_dignity == 'enemy_sign':
            additional_factors.append(f"{lord_planet} (lord) in enemy sign")
        if lord_analysis.get('combustion_status', {}).get('is_combust', False):
            additional_factors.append(f"{lord_planet} (lord) is combust")
        shadbala_rupas = lord_analysis.get('strength_analysis', {}).get('shadbala_rupas', 0)
        if shadbala_rupas > 0 and shadbala_rupas < 2:
            additional_factors.append(f"{lord_planet} (lord) has weak Shadbala strength ({shadbala_rupas:.1f} rupas)")
        elif shadbala_rupas == 0:
            # If shadbala is 0, there might be a calculation issue - don't add this factor
            pass
        
        # Check if lord is dusthana lord
        lord_lordships = lord_analysis.get('lordship_analysis', {}).get('houses_ruled', [])
        if any(h in [6, 8, 12] for h in lord_lordships) and lord_house not in [6, 8, 12]:
            additional_factors.append(f"{lord_planet} (dusthana lord) creates challenges")
        
        # Add additional factors to negative factors if they exist
        all_negative_factors = negative_factors + additional_factors
        
        if positive_factors and all_negative_factors:
            reason_text = f" - has positive factors ({', '.join(positive_factors)}) but weakened by {', '.join(all_negative_factors)}"
        elif positive_factors and strength <= 40 and additional_factors:
            reason_text = f" - despite positive factors ({', '.join(positive_factors)}), weakened by {', '.join(additional_factors)} (score: {strength:.0f}/100)"
        elif positive_factors and strength <= 40:
            reason_text = f" - positive factors ({', '.join(positive_factors)}) but low overall house strength (score: {strength:.0f}/100)"
        elif positive_factors:
            reason_text = f" due to {', '.join(positive_factors)}"
        elif all_negative_factors:
            reason_text = f" due to {', '.join(all_negative_factors)}"
        else:
            reason_text = f" (overall strength: {strength:.0f}/100)"
        
        # Clean up any HTML entities that might have been introduced
        reason_text = reason_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        
        interpretations = {
            1: f"Physical vitality is {strength_desc}{reason_text}",
            2: f"Face and speech health is {strength_desc.replace('weak', 'concerning').replace('strong', 'good')}{reason_text}",
            6: f"Disease resistance is {strength_desc.replace('weak', 'low').replace('strong', 'good')}{reason_text}",
            7: f"Partnership health influence is {strength_desc.replace('weak', 'challenging').replace('strong', 'positive')}{reason_text}",
            8: f"Longevity factors are {strength_desc.replace('weak', 'concerning').replace('strong', 'favorable')}{reason_text}",
            12: f"Mental health is {strength_desc.replace('weak', 'needs attention').replace('strong', 'stable')}{reason_text}"
        }
        
        final_interpretation = interpretations.get(house_num, 'General health influence')
        # Clean up any HTML entities in the final interpretation
        final_interpretation = final_interpretation.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        
        return final_interpretation
    
    def _get_yoga_health_impact(self, yoga):
        """Get health impact of specific yoga"""
        yoga_impacts = {
            'Guru Lagna Yoga': 'Excellent natural healing ability and immunity',
            'Sarala Yoga (Health)': 'Victory over diseases and health challenges',
            'Vimala Yoga (Health)': 'Reduced chronic health issues',
            'Lagna Lord Aristha Yoga': 'Increased health challenges and vulnerability',
            'Surya Karma Yoga': 'Strong vitality and health leadership'
        }
        
        return yoga_impacts.get(yoga.get('name'), 'General health influence')
    
    def _calculate_health_timeline(self):
        """Calculate health timeline - simplified version"""
        return {
            'current_period': 'Building Phase (25-35)',
            'health_focus': 'Establish good habits',
            'upcoming_challenges': 'Watch for stress after 35',
            'favorable_periods': ['Jupiter dasha', 'Venus antardasha'],
            'caution_periods': ['Saturn dasha', 'Mars antardasha']
        }
    
    def _calculate_health_remedies(self):
        """Calculate health remedies - simplified version"""
        return {
            'gemstones': ['Ruby for Sun', 'Pearl for Moon', 'Red Coral for Mars'],
            'mantras': ['Om Suryaya Namaha', 'Om Chandraya Namaha'],
            'lifestyle': ['Regular exercise', 'Balanced diet', 'Adequate sleep'],
            'colors': ['Orange', 'White', 'Green'],
            'donations': ['Wheat on Sunday', 'Rice on Monday', 'Red lentils on Tuesday']
        }
    
    def _get_gandanta_health_implications(self, planet_name, gandanta_info):
        """Get health-specific implications for planet in Gandanta"""
        if not gandanta_info['is_gandanta']:
            return []
        
        intensity = gandanta_info['intensity']
        gandanta_type = gandanta_info['gandanta_type']
        
        # Base health impacts by Gandanta type
        gandanta_health_impacts = {
            'pisces_aries': 'Head injuries, mental health, nervous system disorders',
            'cancer_leo': 'Heart problems, digestive issues, emotional disorders',
            'scorpio_sagittarius': 'Reproductive system, liver issues, accidents, chronic diseases'
        }
        
        base_impact = gandanta_health_impacts[gandanta_type]
        
        # Planet-specific health impacts
        planet_specific_impacts = {
            'Sun': [
                'Weak vitality and life force',
                'Heart problems and circulation issues',
                'Low immunity and frequent illnesses',
                'Difficulty recovering from diseases'
            ],
            'Moon': [
                'Mental health instability',
                'Digestive disorders from emotional stress',
                'Sleep disorders and insomnia',
                'Psychosomatic health issues'
            ],
            'Mars': [
                'Blood disorders and circulation problems',
                'Prone to accidents and injuries',
                'Inflammatory conditions',
                'Energy depletion and fatigue'
            ],
            'Mercury': [
                'Nervous system disorders',
                'Communication and speech problems',
                'Respiratory issues',
                'Anxiety and mental restlessness'
            ],
            'Jupiter': [
                'Liver and digestive problems',
                'Weak immunity system',
                'Weight and metabolic issues',
                'Difficulty in healing and recovery'
            ],
            'Venus': [
                'Reproductive system disorders',
                'Hormonal imbalances',
                'Kidney and urinary problems',
                'Skin and beauty related issues'
            ],
            'Saturn': [
                'Chronic and long-lasting health issues',
                'Bone and joint problems',
                'Dental issues',
                'Slow healing and recovery'
            ],
            'Rahu': [
                'Mysterious and hard-to-diagnose illnesses',
                'Toxic conditions and poisoning',
                'Sudden health crises',
                'Addiction and substance abuse issues'
            ],
            'Ketu': [
                'Hidden health problems',
                'Spiritual and psychological disorders',
                'Detachment from body care',
                'Sudden health transformations'
            ]
        }
        
        impacts = planet_specific_impacts.get(planet_name, ['General health challenges'])
        impacts.append(base_impact)
        
        # Adjust severity based on intensity
        if intensity in ['Extreme', 'High']:
            impacts.append(f'{intensity} intensity - requires immediate attention and remedies')
        elif intensity == 'Medium':
            impacts.append('Medium intensity - preventive measures recommended')
        else:
            impacts.append('Low intensity - mild effects, general precautions sufficient')
        
        return impacts