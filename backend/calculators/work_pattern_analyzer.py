from .base_calculator import BaseCalculator

class WorkPatternAnalyzer(BaseCalculator):
    """Analyze work pattern: Employed/Self-employed/Government/Entrepreneur"""
    
    def __init__(self, chart_data, birth_data):
        super().__init__(chart_data)
        if not birth_data:
            raise ValueError("Birth data required for work pattern analysis")
        
        # Initialize calculators
        from .shadbala_calculator import ShadbalaCalculator
        from .planetary_dignities_calculator import PlanetaryDignitiesCalculator
        
        self.shadbala_calc = ShadbalaCalculator(chart_data)
        self.dignities_calc = PlanetaryDignitiesCalculator(chart_data)
        
        # Get real data
        self.shadbala_data = self.shadbala_calc.calculate_shadbala()
        self.dignities_data = self.dignities_calc.calculate_planetary_dignities()
    
    def analyze_work_pattern(self):
        """Comprehensive work pattern analysis"""
        # Get key factors
        tenth_lord_analysis = self._analyze_tenth_lord_pattern()
        lagna_lord_analysis = self._analyze_lagna_lord_strength()
        second_lord_analysis = self._analyze_wealth_source()
        tenth_house_analysis = self._analyze_tenth_house_occupants()
        
        # Calculate pattern scores
        pattern_scores = self._calculate_pattern_scores(
            tenth_lord_analysis, lagna_lord_analysis, 
            second_lord_analysis, tenth_house_analysis
        )
        
        # Determine primary pattern
        primary_pattern = max(pattern_scores, key=pattern_scores.get)
        
        return {
            'primary_pattern': primary_pattern,
            'pattern_scores': pattern_scores,
            'pattern_analysis': self._generate_pattern_analysis(
                primary_pattern, tenth_lord_analysis, 
                lagna_lord_analysis, second_lord_analysis
            ),
            'astrological_reasoning': self._generate_pattern_reasoning(
                tenth_lord_analysis, lagna_lord_analysis, 
                second_lord_analysis, tenth_house_analysis
            )
        }
    
    def _analyze_tenth_lord_pattern(self):
        """Analyze 10th lord for work pattern indicators"""
        ascendant_sign = int(self.chart_data['ascendant'] / 30)
        tenth_house_sign = (ascendant_sign + 9) % 12
        tenth_lord = self.get_sign_lord(tenth_house_sign)
        
        tenth_lord_data = self.chart_data['planets'][tenth_lord]
        tenth_lord_house = tenth_lord_data['house']
        
        return {
            'tenth_lord': tenth_lord,
            'house_placement': tenth_lord_house,
            'strength': self.shadbala_data[tenth_lord]['total_rupas'],
            'dignity': self.dignities_data[tenth_lord]['dignity']
        }
    
    def _analyze_lagna_lord_strength(self):
        """Analyze lagna lord for entrepreneurial potential"""
        ascendant_sign = int(self.chart_data['ascendant'] / 30)
        lagna_lord = self.get_sign_lord(ascendant_sign)
        
        lagna_lord_data = self.chart_data['planets'][lagna_lord]
        lagna_lord_house = lagna_lord_data['house']
        
        return {
            'lagna_lord': lagna_lord,
            'house_placement': lagna_lord_house,
            'strength': self.shadbala_data[lagna_lord]['total_rupas'],
            'dignity': self.dignities_data[lagna_lord]['dignity']
        }
    
    def _analyze_wealth_source(self):
        """Analyze 2nd lord for income source pattern"""
        ascendant_sign = int(self.chart_data['ascendant'] / 30)
        second_house_sign = (ascendant_sign + 1) % 12
        second_lord = self.get_sign_lord(second_house_sign)
        
        second_lord_data = self.chart_data['planets'][second_lord]
        second_lord_house = second_lord_data['house']
        
        return {
            'second_lord': second_lord,
            'house_placement': second_lord_house,
            'strength': self.shadbala_data[second_lord]['total_rupas']
        }
    
    def _analyze_tenth_house_occupants(self):
        """Analyze planets in 10th house"""
        tenth_house_planets = []
        for planet, data in self.chart_data['planets'].items():
            if data['house'] == 10:
                tenth_house_planets.append(planet)
        
        return {
            'occupants': tenth_house_planets,
            'count': len(tenth_house_planets)
        }
    
    def _calculate_pattern_scores(self, tenth_lord, lagna_lord, second_lord, tenth_house):
        """Calculate scores for each work pattern"""
        scores = {
            'Government': 0,
            'Employed': 0,
            'Self-employed': 0,
            'Entrepreneur': 0
        }
        
        # 10th lord house placement scoring
        house_scores = {
            1: {'Self-employed': 3, 'Entrepreneur': 2},
            2: {'Self-employed': 2, 'Entrepreneur': 1},
            3: {'Self-employed': 2, 'Employed': 1},
            4: {'Self-employed': 1, 'Employed': 1},
            5: {'Entrepreneur': 2, 'Self-employed': 1},
            6: {'Employed': 3, 'Government': 1},
            7: {'Employed': 2, 'Entrepreneur': 1},
            8: {'Employed': 1, 'Self-employed': 1},
            9: {'Government': 2, 'Employed': 1},
            10: {'Government': 3, 'Employed': 2},
            11: {'Employed': 2, 'Entrepreneur': 2},
            12: {'Employed': 1, 'Self-employed': 1}
        }
        
        # Add 10th lord house scores
        if tenth_lord['house_placement'] in house_scores:
            for pattern, score in house_scores[tenth_lord['house_placement']].items():
                scores[pattern] += score
        
        # 10th lord planet scoring
        planet_scores = {
            'Sun': {'Government': 3, 'Employed': 1},
            'Moon': {'Employed': 2, 'Government': 1},
            'Mercury': {'Employed': 2, 'Self-employed': 1},
            'Venus': {'Self-employed': 2, 'Employed': 1},
            'Mars': {'Self-employed': 3, 'Entrepreneur': 2},
            'Jupiter': {'Government': 2, 'Employed': 2},
            'Saturn': {'Employed': 3, 'Government': 2},
            'Rahu': {'Entrepreneur': 2, 'Self-employed': 1},
            'Ketu': {'Self-employed': 1, 'Employed': 1}
        }
        
        # Add 10th lord planet scores
        if tenth_lord['tenth_lord'] in planet_scores:
            for pattern, score in planet_scores[tenth_lord['tenth_lord']].items():
                scores[pattern] += score
        
        # Lagna lord strength bonus for entrepreneurship
        if lagna_lord['strength'] > 1.0 and lagna_lord['house_placement'] in [1, 5, 9, 10, 11]:
            scores['Entrepreneur'] += 2
            scores['Self-employed'] += 1
        
        # 2nd lord house placement for income source
        income_scores = {
            1: {'Self-employed': 2, 'Entrepreneur': 1},
            6: {'Employed': 2},
            8: {'Employed': 1},
            10: {'Government': 2, 'Employed': 1},
            11: {'Entrepreneur': 2, 'Employed': 1}
        }
        
        if second_lord['house_placement'] in income_scores:
            for pattern, score in income_scores[second_lord['house_placement']].items():
                scores[pattern] += score
        
        # 10th house occupants
        for planet in tenth_house['occupants']:
            if planet == 'Sun':
                scores['Government'] += 2
            elif planet == 'Saturn':
                scores['Employed'] += 2
            elif planet == 'Mars':
                scores['Self-employed'] += 2
        
        return scores
    
    def _generate_pattern_analysis(self, primary_pattern, tenth_lord, lagna_lord, second_lord):
        """Generate detailed pattern analysis"""
        pattern_descriptions = {
            'Government': {
                'summary': 'You are naturally suited for government service and public sector roles',
                'characteristics': ['Structured career progression', 'Job security and stability', 'Public service orientation', 'Authority and responsibility'],
                'ideal_roles': ['Government Officer', 'Public Administrator', 'Policy Maker', 'Civil Servant'],
                'work_style': 'Systematic, rule-based, and service-oriented approach'
            },
            'Employed': {
                'summary': 'You thrive in structured employment with established organizations',
                'characteristics': ['Team collaboration', 'Steady income and benefits', 'Clear role definitions', 'Professional growth paths'],
                'ideal_roles': ['Corporate Manager', 'Department Head', 'Specialist', 'Team Leader'],
                'work_style': 'Collaborative, process-oriented, and growth-focused approach'
            },
            'Self-employed': {
                'summary': 'You are suited for independent work and professional practice',
                'characteristics': ['Professional autonomy', 'Skill-based income', 'Client relationships', 'Flexible schedule'],
                'ideal_roles': ['Consultant', 'Freelancer', 'Professional Practitioner', 'Service Provider'],
                'work_style': 'Independent, client-focused, and expertise-driven approach'
            },
            'Entrepreneur': {
                'summary': 'You have natural entrepreneurial abilities and business acumen',
                'characteristics': ['Business ownership', 'Risk-taking ability', 'Innovation and creativity', 'Wealth creation potential'],
                'ideal_roles': ['Business Owner', 'Startup Founder', 'Investor', 'Business Developer'],
                'work_style': 'Innovative, risk-taking, and opportunity-focused approach'
            }
        }
        
        return pattern_descriptions[primary_pattern]
    
    def _generate_pattern_reasoning(self, tenth_lord, lagna_lord, second_lord, tenth_house):
        """Generate astrological reasoning for work pattern"""
        reasoning = []
        
        # 10th lord reasoning
        reasoning.append(f"Your 10th lord {tenth_lord['tenth_lord']} in {tenth_lord['house_placement']}th house indicates {self._get_house_work_pattern(tenth_lord['house_placement'])}")
        
        # Planet-specific reasoning
        planet_patterns = {
            'Sun': 'government service and authoritative positions',
            'Moon': 'public-facing roles and service positions',
            'Mercury': 'communication-based employment',
            'Venus': 'creative and independent work',
            'Mars': 'self-employment and entrepreneurial ventures',
            'Jupiter': 'advisory roles and institutional positions',
            'Saturn': 'structured employment and systematic work',
            'Rahu': 'unconventional and entrepreneurial paths'
        }
        
        if tenth_lord['tenth_lord'] in planet_patterns:
            reasoning.append(f"{tenth_lord['tenth_lord']} as 10th lord favors {planet_patterns[tenth_lord['tenth_lord']]}")
        
        # Lagna lord strength
        if lagna_lord['strength'] > 1.0:
            reasoning.append(f"Strong lagna lord {lagna_lord['lagna_lord']} supports independent and entrepreneurial ventures")
        else:
            reasoning.append(f"Moderate lagna lord {lagna_lord['lagna_lord']} suggests structured employment benefits")
        
        # 2nd lord income source
        income_patterns = {
            1: 'self-generated income through personal efforts',
            6: 'salary-based income through service',
            8: 'variable income through employment',
            10: 'authoritative position income',
            11: 'network-based and business income'
        }
        
        if second_lord['house_placement'] in income_patterns:
            reasoning.append(f"2nd lord {second_lord['second_lord']} in {second_lord['house_placement']}th house indicates {income_patterns[second_lord['house_placement']]}")
        
        # 10th house occupants
        if tenth_house['occupants']:
            planet_influences = []
            for planet in tenth_house['occupants']:
                if planet == 'Sun':
                    planet_influences.append('government service orientation')
                elif planet == 'Saturn':
                    planet_influences.append('structured employment preference')
                elif planet == 'Mars':
                    planet_influences.append('self-employment tendencies')
            
            if planet_influences:
                reasoning.append(f"Planets in 10th house ({', '.join(tenth_house['occupants'])}) add {', '.join(planet_influences)}")
        
        return reasoning
    
    def _get_house_work_pattern(self, house):
        """Get work pattern indication from house placement"""
        house_patterns = {
            1: 'self-employment and personal ventures',
            2: 'family business and wealth-focused work',
            3: 'communication-based self-employment',
            4: 'property-based or homeland work',
            5: 'creative and speculative ventures',
            6: 'service employment and daily work',
            7: 'partnership-based business',
            8: 'research and transformation work',
            9: 'advisory and educational roles',
            10: 'government and authoritative positions',
            11: 'large organization employment',
            12: 'foreign or behind-the-scenes work'
        }
        
        return house_patterns.get(house, 'professional work')