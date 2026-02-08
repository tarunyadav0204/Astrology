from .base_calculator import BaseCalculator
from .planet_analyzer import PlanetAnalyzer
from .house_analyzer import HouseAnalyzer
from .house_strength_calculator import HouseStrengthCalculator
from .aspect_calculator import AspectCalculator
from .planetary_dignities_calculator import PlanetaryDignitiesCalculator
from .classical_shadbala import calculate_classical_shadbala
from .yoga_calculator import YogaCalculator

class WealthCalculator(BaseCalculator):
    """Comprehensive wealth analysis using existing calculators"""
    
    def __init__(self, chart_data, birth_data):
        super().__init__(chart_data)
        self.birth_data = birth_data
        
        # Initialize existing calculators
        self.planet_analyzer = PlanetAnalyzer(chart_data, birth_data)
        self.house_analyzer = HouseAnalyzer(chart_data, birth_data)
        self.house_strength_calc = HouseStrengthCalculator(chart_data)
        self.aspect_calc = AspectCalculator(chart_data)
        self.dignities_calc = PlanetaryDignitiesCalculator(chart_data)
        self.shadbala_data = calculate_classical_shadbala(birth_data, chart_data)
        self.yoga_calc = YogaCalculator(chart_data=chart_data)
        
        # Wealth house mappings
        self.WEALTH_HOUSES = {
            2: "Accumulated wealth and family assets",
            5: "Speculation, investments and intelligence gains", 
            9: "Fortune, luck and dharmic wealth",
            11: "Income, gains and fulfillment of desires"
        }
        
        # Supporting wealth houses
        self.SUPPORTING_WEALTH_HOUSES = {
            1: "Self-effort and personal wealth capacity",
            4: "Property, real estate and fixed assets",
            7: "Business partnerships and trade",
            10: "Career income and professional wealth"
        }
        
        # Wealth house lords to analyze
        self.WEALTH_HOUSE_LORDS = [1, 2, 4, 5, 7, 9, 10, 11]
        
        # Planet-wealth system mapping
        self.PLANET_WEALTH_MAPPING = {
            'Sun': {'systems': ['Authority wealth', 'Government income', 'Leadership positions'], 'element': 'Fire'},
            'Moon': {'systems': ['Public wealth', 'Liquid assets', 'Real estate'], 'element': 'Water'},
            'Mars': {'systems': ['Property wealth', 'Sports income', 'Engineering business'], 'element': 'Fire'},
            'Mercury': {'systems': ['Business wealth', 'Communication income', 'Trade and commerce'], 'element': 'Air'},
            'Jupiter': {'systems': ['Wisdom wealth', 'Teaching income', 'Dharmic gains'], 'element': 'Air'},
            'Venus': {'systems': ['Luxury wealth', 'Arts income', 'Beauty business'], 'element': 'Water'},
            'Saturn': {'systems': ['Slow wealth', 'Hard work income', 'Mining and labor'], 'element': 'Earth'},
            'Rahu': {'systems': ['Foreign wealth', 'Technology income', 'Sudden gains'], 'element': 'Air'},
            'Ketu': {'systems': ['Spiritual wealth', 'Research income', 'Hidden assets'], 'element': 'Fire'}
        }
        
        # Natural wealth significators
        self.NATURAL_WEALTH_SIGNIFICATORS = {
            2: ['Jupiter'],  # Wealth accumulation
            5: ['Jupiter'],  # Investments, speculation
            9: ['Jupiter'],  # Fortune, luck
            11: ['Jupiter'],  # Gains, income
            4: ['Moon'],     # Property, real estate
            7: ['Venus'],    # Business partnerships
            10: ['Sun', 'Mercury']  # Career income
        }
    
    def calculate_overall_wealth(self):
        """Calculate overall wealth assessment"""
        planet_analysis = self._analyze_wealth_planets()
        house_analysis = self._analyze_wealth_houses()
        yoga_analysis = self._analyze_wealth_yogas()
        wealth_score = self._calculate_wealth_score(planet_analysis, house_analysis, yoga_analysis)
        
        return {
            'planet_analysis': planet_analysis,
            'house_analysis': house_analysis,
            'yoga_analysis': yoga_analysis,
            'wealth_score': wealth_score['score'],
            'wealth_score_breakdown': wealth_score['calculation_breakdown'],
            'wealth_constitution': self._determine_wealth_constitution(),
            'income_sources': self._analyze_income_sources(),
            'wealth_timeline': self._calculate_wealth_timeline(),
            'wealth_remedies': self._calculate_wealth_remedies()
        }
    
    def _analyze_wealth_planets(self):
        """Analyze all planets for wealth impact"""
        planet_wealth_analysis = {}
        
        for planet_name, planet_data in self.chart_data['planets'].items():
            if planet_name not in self.PLANET_WEALTH_MAPPING:
                continue
                
            analysis = self.planet_analyzer.analyze_planet(planet_name)
            wealth_impact = self._get_planet_wealth_impact(planet_name, analysis)
            
            planet_wealth_analysis[planet_name] = {
                'basic_analysis': analysis,
                'wealth_impact': wealth_impact,
                'wealth_systems': self.PLANET_WEALTH_MAPPING[planet_name]['systems'],
                'element': self.PLANET_WEALTH_MAPPING[planet_name]['element']
            }
        
        return planet_wealth_analysis
    
    def _analyze_wealth_houses(self):
        """Analyze wealth-related houses using HouseAnalyzer"""
        house_wealth_analysis = {}
        
        for house_num in self.WEALTH_HOUSE_LORDS:
            house_analysis = self.house_analyzer.analyze_house(house_num)
            wealth_interpretation = self._get_house_wealth_interpretation(house_num, house_analysis)
            
            house_wealth_analysis[house_num] = {
                'house_analysis': house_analysis,
                'wealth_significance': self.WEALTH_HOUSES.get(house_num) or self.SUPPORTING_WEALTH_HOUSES[house_num],
                'wealth_interpretation': wealth_interpretation
            }
        
        return house_wealth_analysis
    
    def _analyze_wealth_yogas(self):
        """Analyze wealth-related yogas"""
        all_yogas = self.yoga_calc.calculate_all_yogas()
        
        yoga_analysis = {
            'dhana_yogas': all_yogas.get('dhana_yogas', []),
            'lakshmi_yogas': [],  # Will be populated from other yogas
            'raja_yogas': all_yogas.get('raj_yogas', []),
            'viparita_yogas': all_yogas.get('viparita_raja_yogas', []),
            'total_beneficial': 0,
            'total_afflictions': 0
        }
        
        # Count beneficial yogas
        yoga_analysis['total_beneficial'] = (
            len(yoga_analysis['dhana_yogas']) +
            len(yoga_analysis['raja_yogas']) +
            len(yoga_analysis['viparita_yogas'])
        )
        
        # Add Gaja Kesari as Lakshmi yoga (wealth-related)
        gaja_kesari = all_yogas.get('gaja_kesari_yogas', [])
        if gaja_kesari:
            yoga_analysis['lakshmi_yogas'].extend(gaja_kesari)
            yoga_analysis['total_beneficial'] += len(gaja_kesari)
        
        return yoga_analysis
    
    def _calculate_wealth_score(self, planet_analysis, house_analysis, yoga_analysis):
        """Calculate overall wealth score with detailed breakdown"""
        base_score = 50
        calculation_breakdown = ["Base Score: 50"]
        
        # Planet contributions
        planet_score = 0
        for planet_name, analysis in planet_analysis.items():
            impact_type = analysis['wealth_impact']['impact_type']
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
        
        # House contributions
        house_score = 0
        for house_num, analysis in house_analysis.items():
            house_strength = analysis['house_analysis']['overall_house_assessment']['overall_strength_score']
            
            if house_num in [2, 5, 9, 11]:  # Primary wealth houses
                contribution = (house_strength - 50) * 0.4
                house_score += contribution
                calculation_breakdown.append(f"{house_num}th House: {contribution:+.1f} (Primary wealth)")
            else:  # Supporting wealth houses
                contribution = (house_strength - 50) * 0.2
                house_score += contribution
                calculation_breakdown.append(f"{house_num}th House: {contribution:+.1f} (Supporting)")
        
        base_score += house_score
        calculation_breakdown.append(f"House Total: {house_score:+.1f}")
        
        # Yoga contributions
        yoga_score = yoga_analysis['total_beneficial'] * 6 - yoga_analysis['total_afflictions'] * 8
        base_score += yoga_score
        calculation_breakdown.append(f"Beneficial Yogas: +{yoga_analysis['total_beneficial'] * 6}")
        calculation_breakdown.append(f"Affliction Yogas: -{yoga_analysis['total_afflictions'] * 8}")
        calculation_breakdown.append(f"Yoga Total: {yoga_score:+d}")
        
        final_score = min(100, max(0, int(base_score)))
        calculation_breakdown.append(f"Final Score: {final_score}")
        
        return {
            'score': final_score,
            'calculation_breakdown': calculation_breakdown
        }
    
    def _determine_wealth_constitution(self):
        """Determine wealth constitution type based on strongest wealth planets"""
        planet_strengths = {}
        
        for planet_name in ['Jupiter', 'Venus', 'Mercury', 'Sun']:
            if planet_name in self.chart_data['planets']:
                analysis = self.planet_analyzer.analyze_planet(planet_name)
                strength = analysis['strength_analysis']['shadbala_points']
                dignity = analysis['dignity_analysis']['dignity']
                
                # Boost strength for exalted/own sign
                if dignity in ['exalted', 'own_sign']:
                    strength *= 1.5
                
                planet_strengths[planet_name] = strength
        
        if not planet_strengths:
            return 'Mixed constitution'
        
        strongest_planet = max(planet_strengths, key=planet_strengths.get)
        
        constitutions = {
            'Jupiter': 'Wisdom-based wealth (teaching, consulting, dharmic business)',
            'Venus': 'Luxury-based wealth (arts, beauty, entertainment)',
            'Mercury': 'Business-based wealth (trade, communication, technology)',
            'Sun': 'Authority-based wealth (leadership, government, high positions)'
        }
        
        return constitutions[strongest_planet]
    
    def _analyze_income_sources(self):
        """Analyze primary income sources"""
        sources = []
        
        # Analyze 10th house for career income
        tenth_house = self.house_analyzer.analyze_house(10)
        tenth_lord = tenth_house['basic_info']['house_lord']
        tenth_lord_house = tenth_house['house_lord_analysis']['basic_info']['house']
        
        if tenth_lord_house in [2, 5, 9, 11]:
            sources.append(f"Career income through {tenth_lord} placement in {tenth_lord_house}th house")
        
        # Analyze 11th house for gains
        eleventh_house = self.house_analyzer.analyze_house(11)
        eleventh_lord = eleventh_house['basic_info']['house_lord']
        
        sources.append(f"Primary gains through {eleventh_lord} influence")
        
        return sources
    
    def _get_planet_wealth_impact(self, planet_name, analysis):
        """Get planet's wealth impact with reasoning"""
        dignity = analysis['dignity_analysis']['dignity']
        house = analysis['basic_info']['house']
        gandanta_analysis = analysis.get('gandanta_analysis', {})
        combustion = analysis['combustion_status']['is_combust']
        shadbala_rupas = analysis['strength_analysis']['shadbala_rupas']
        
        reasons = []
        
        # Check for Gandanta impact first
        if gandanta_analysis.get('is_gandanta', False):
            intensity = gandanta_analysis['intensity']
            gandanta_type = gandanta_analysis['gandanta_type']
            
            reasons.append(f"in Gandanta ({gandanta_type}, {intensity} intensity)")
            gandanta_implications = self._get_gandanta_wealth_implications(planet_name, gandanta_analysis)
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
        
        if house in [2, 11]:
            reasons.append(f"in {house}th house (primary wealth house)")
        elif house in [5, 9]:
            reasons.append(f"in {house}th house (fortune house)")
        elif house in [1, 4, 7, 10]:
            reasons.append(f"in {house}th house (supporting wealth)")
        elif house in [6, 8, 12]:
            reasons.append(f"in {house}th house (dusthana)")
        
        if combustion:
            reasons.append("combust")
        
        if shadbala_rupas < 3:
            reasons.append(f"weak strength ({shadbala_rupas:.1f} rupas)")
        elif shadbala_rupas >= 5:
            reasons.append(f"good strength ({shadbala_rupas:.1f} rupas)")
        
        reasoning = f"{planet_name} is {', '.join(reasons)}" if reasons else f"{planet_name} has moderate placement"
        
        # Determine impact
        if dignity in ['exalted', 'own_sign'] and house in [2, 11]:
            return {
                'impact_type': 'Very Positive',
                'severity': 'Beneficial',
                'implications': [f'Strong {planet_name} enhances {self.PLANET_WEALTH_MAPPING[planet_name]["systems"][0].lower()}'],
                'reasoning': reasoning
            }
        elif dignity in ['exalted', 'own_sign'] and house in [5, 9, 1, 4, 7, 10]:
            return {
                'impact_type': 'Positive',
                'severity': 'Beneficial',
                'implications': [f'Well-placed {planet_name} supports {self.PLANET_WEALTH_MAPPING[planet_name]["systems"][0].lower()}'],
                'reasoning': reasoning
            }
        elif dignity == 'debilitated' or house in [6, 8, 12]:
            return {
                'impact_type': 'Challenging',
                'severity': 'Medium',
                'implications': [f'Weak {planet_name} may limit {self.PLANET_WEALTH_MAPPING[planet_name]["systems"][0].lower()}'],
                'reasoning': reasoning
            }
        else:
            return {
                'impact_type': 'Neutral',
                'severity': 'Low',
                'implications': [f'Moderate influence on {self.PLANET_WEALTH_MAPPING[planet_name]["systems"][0].lower()}'],
                'reasoning': reasoning
            }
    
    def _get_house_wealth_interpretation(self, house_num, house_analysis):
        """Get house wealth interpretation with reasoning"""
        strength = house_analysis['overall_house_assessment']['overall_strength_score']
        lord_analysis = house_analysis['house_lord_analysis']
        lord_planet = lord_analysis['basic_info']['planet']
        lord_house = lord_analysis['basic_info']['house']
        lord_dignity = lord_analysis['dignity_analysis']['dignity']
        
        reasons = []
        
        # Lord placement reasoning
        if lord_house in [2, 11]:
            reasons.append(f"{lord_planet} (lord) in {lord_house}th house strongly enhances wealth")
        elif lord_house in [5, 9]:
            reasons.append(f"{lord_planet} (lord) in {lord_house}th house supports fortune")
        elif lord_house in [1, 4, 7, 10]:
            reasons.append(f"{lord_planet} (lord) in {lord_house}th house moderately supports wealth")
        elif lord_house in [6, 8, 12]:
            reasons.append(f"{lord_planet} (lord) in {lord_house}th house creates challenges")
        
        # Lord dignity reasoning
        if lord_dignity == 'debilitated':
            reasons.append(f"{lord_planet} is debilitated")
        elif lord_dignity in ['exalted', 'own_sign']:
            reasons.append(f"{lord_planet} is {lord_dignity}")
        
        reason_text = " because " + ", ".join(reasons) if reasons else ""
        strength_desc = 'strong' if strength > 70 else 'moderate' if strength > 40 else 'weak'
        
        interpretations = {
            1: f"Self-effort for wealth is {strength_desc}{reason_text}",
            2: f"Wealth accumulation capacity is {strength_desc}{reason_text}",
            4: f"Property and fixed assets are {strength_desc}{reason_text}",
            5: f"Investment and speculation ability is {strength_desc}{reason_text}",
            7: f"Business partnership potential is {strength_desc}{reason_text}",
            9: f"Fortune and luck factors are {strength_desc}{reason_text}",
            10: f"Career income potential is {strength_desc}{reason_text}",
            11: f"Gains and income flow is {strength_desc}{reason_text}"
        }
        
        return interpretations[house_num]
    
    def _get_gandanta_wealth_implications(self, planet_name, gandanta_info):
        """Get wealth-specific implications for planet in Gandanta"""
        if not gandanta_info['is_gandanta']:
            return []
        
        intensity = gandanta_info['intensity']
        
        planet_specific_impacts = {
            'Jupiter': [
                'Wisdom-based income severely restricted',
                'Teaching and consulting opportunities blocked',
                'Dharmic wealth creation challenges',
                'Financial guidance abilities compromised'
            ],
            'Venus': [
                'Luxury and arts income disrupted',
                'Beauty and entertainment business challenges',
                'Partnership wealth creation problems',
                'Aesthetic value monetization difficulties'
            ],
            'Mercury': [
                'Business and trade income instability',
                'Communication-based earnings disrupted',
                'Technology and commerce challenges',
                'Analytical wealth creation blocked'
            ],
            'Sun': [
                'Authority-based income challenges',
                'Government and leadership wealth blocked',
                'High-position earnings disrupted',
                'Recognition-based income problems'
            ]
        }
        
        impacts = planet_specific_impacts.get(planet_name, ['General wealth challenges'])
        
        if intensity in ['Extreme', 'High']:
            impacts.append(f'{intensity} intensity - severe wealth restrictions requiring immediate remedies')
        elif intensity == 'Medium':
            impacts.append('Medium intensity - moderate wealth challenges, remedies recommended')
        else:
            impacts.append('Low intensity - mild wealth effects, general precautions sufficient')
        
        return impacts
    
    def _calculate_wealth_timeline(self):
        """Calculate wealth timeline - simplified version"""
        return {
            'current_period': 'Building Phase',
            'wealth_focus': 'Establish income sources',
            'upcoming_opportunities': 'Jupiter transit benefits',
            'favorable_periods': ['Venus dasha', 'Jupiter antardasha'],
            'caution_periods': ['Saturn dasha', 'Rahu antardasha']
        }
    
    def _calculate_wealth_remedies(self):
        """Calculate wealth remedies - simplified version"""
        return {
            'gemstones': ['Yellow Sapphire for Jupiter', 'Diamond for Venus', 'Emerald for Mercury'],
            'mantras': ['Om Guruve Namaha', 'Om Shukraya Namaha'],
            'donations': ['Yellow items on Thursday', 'White items on Friday'],
            'colors': ['Yellow', 'White', 'Green'],
            'timing': ['Thursday for wealth decisions', 'Friday for luxury purchases']
        }