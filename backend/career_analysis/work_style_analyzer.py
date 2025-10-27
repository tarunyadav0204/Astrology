from calculators.planet_analyzer import PlanetAnalyzer
from calculators.yogi_calculator import YogiCalculator
from calculators.badhaka_calculator import BadhakaCalculator

class WorkStyleAnalyzer:
    def __init__(self, chart_data):
        self.chart_data = chart_data
        self.planets = chart_data['planets']
        self.ascendant = chart_data['ascendant']
        self.ascendant_sign = int(self.ascendant / 30)
        
        # Initialize existing calculators
        self.planet_analyzer = PlanetAnalyzer(chart_data)
        self.yogi_calc = YogiCalculator(chart_data)
        self.badhaka_calc = BadhakaCalculator(chart_data)
    
    def analyze_creative_vs_structured(self, birth_data):
        """Analyze creative vs structured work preference using comprehensive planetary analysis"""
        
        # Calculate Yogi points and Badhaka data once
        yogi_data = self.yogi_calc.calculate_yogi_points(birth_data)
        
        # Calculate scores using existing planetary analysis
        creative_scores = self._calculate_creative_scores(yogi_data)
        structured_scores = self._calculate_structured_scores(yogi_data)
        
        # Calculate final indices
        creative_index = sum(creative_scores.values())
        structured_index = sum(structured_scores.values())
        
        # Determine primary preference
        primary_preference, preference_strength = self._determine_preference(creative_index, structured_index)
        
        # Generate work style behaviors
        work_behaviors = self._generate_work_behaviors(creative_index, structured_index)
        
        return {
            'creative_index': round(creative_index, 1),
            'structured_index': round(structured_index, 1),
            'primary_preference': primary_preference,
            'preference_strength': preference_strength,
            'creative_breakdown': creative_scores,
            'structured_breakdown': structured_scores,
            'work_behaviors': work_behaviors,
            'calculation_details': self._get_calculation_breakdown(creative_scores, structured_scores)
        }
    
    def _calculate_creative_scores(self, yogi_data):
        """Calculate creative work scores using existing planetary analysis"""
        scores = {
            'venus_creativity': 0,
            'moon_imagination': 0,
            'mercury_flexibility': 0,
            'fifth_house_expression': 0,
            'twelfth_house_inspiration': 0,
            'water_mutable_signs': 0
        }
        
        # Venus creativity - use existing planet analyzer
        venus_analysis = self.planet_analyzer.analyze_planet('Venus')
        venus_base_score = self._get_creative_base_score('Venus')
        scores['venus_creativity'] = self._apply_planetary_conditions('Venus', venus_base_score, venus_analysis, yogi_data)
        
        # Moon imagination
        moon_analysis = self.planet_analyzer.analyze_planet('Moon')
        moon_base_score = self._get_creative_base_score('Moon')
        scores['moon_imagination'] = self._apply_planetary_conditions('Moon', moon_base_score, moon_analysis, yogi_data)
        
        # Mercury flexibility
        mercury_analysis = self.planet_analyzer.analyze_planet('Mercury')
        mercury_base_score = self._get_creative_base_score('Mercury')
        scores['mercury_flexibility'] = self._apply_planetary_conditions('Mercury', mercury_base_score, mercury_analysis, yogi_data)
        
        # 5th house expression
        scores['fifth_house_expression'] = self._calculate_house_creative_influence(5, yogi_data)
        
        # 12th house inspiration
        scores['twelfth_house_inspiration'] = self._calculate_house_creative_influence(12, yogi_data)
        
        # Water and mutable signs emphasis
        scores['water_mutable_signs'] = self._calculate_sign_emphasis(['water', 'mutable'])
        
        return scores
    
    def _calculate_structured_scores(self, yogi_data):
        """Calculate structured work scores using existing planetary analysis"""
        scores = {
            'saturn_discipline': 0,
            'mars_systematic': 0,
            'mercury_analytical': 0,
            'sixth_house_routine': 0,
            'tenth_house_hierarchy': 0,
            'earth_fixed_signs': 0
        }
        
        # Saturn discipline
        saturn_analysis = self.planet_analyzer.analyze_planet('Saturn')
        saturn_base_score = self._get_structured_base_score('Saturn')
        scores['saturn_discipline'] = self._apply_planetary_conditions('Saturn', saturn_base_score, saturn_analysis, yogi_data)
        
        # Mars systematic action
        mars_analysis = self.planet_analyzer.analyze_planet('Mars')
        mars_base_score = self._get_structured_base_score('Mars')
        scores['mars_systematic'] = self._apply_planetary_conditions('Mars', mars_base_score, mars_analysis, yogi_data)
        
        # Mercury analytical
        mercury_analysis = self.planet_analyzer.analyze_planet('Mercury')
        mercury_base_score = self._get_structured_base_score('Mercury')
        scores['mercury_analytical'] = self._apply_planetary_conditions('Mercury', mercury_base_score, mercury_analysis, yogi_data)
        
        # 6th house routine work
        scores['sixth_house_routine'] = self._calculate_house_structured_influence(6, yogi_data)
        
        # 10th house hierarchy
        scores['tenth_house_hierarchy'] = self._calculate_house_structured_influence(10, yogi_data)
        
        # Earth and fixed signs emphasis
        scores['earth_fixed_signs'] = self._calculate_sign_emphasis(['earth', 'fixed'])
        
        return scores
    
    def _get_creative_base_score(self, planet):
        """Get base creative score for planet based on house and sign placement"""
        planet_data = self.planets[planet]
        house = planet_data['house']
        sign = int(planet_data['longitude'] / 30)
        
        base_score = 0
        
        if planet == 'Venus':
            # Venus creativity factors
            if house in [1, 5, 10]:  # Self-expression, creativity, career creativity
                base_score += 15
            elif house in [3, 7, 11]:  # Communication, partnerships, networks
                base_score += 10
            
            # Venus in artistic signs
            if sign in [1, 6, 11]:  # Taurus, Libra, Pisces
                base_score += 12
            elif sign in [2, 3, 7]:  # Gemini, Cancer, Scorpio
                base_score += 8
                
        elif planet == 'Moon':
            # Moon imagination factors
            if house in [5, 12]:  # Creativity, subconscious
                base_score += 12
            elif house in [1, 4, 9]:  # Self, emotions, higher mind
                base_score += 8
            
            # Moon in intuitive signs
            if sign in [3, 7, 11]:  # Cancer, Scorpio, Pisces
                base_score += 10
            elif sign in [2, 5, 8]:  # Gemini, Virgo, Sagittarius
                base_score += 6
                
        elif planet == 'Mercury':
            # Mercury flexibility factors
            if house in [3, 5, 9]:  # Communication, creativity, higher learning
                base_score += 10
            elif house in [1, 7, 11]:  # Self-expression, partnerships, networks
                base_score += 8
            
            # Mercury in flexible signs
            if sign in [2, 5, 8, 11]:  # Gemini, Virgo, Sagittarius, Pisces
                base_score += 8
        
        return base_score
    
    def _get_structured_base_score(self, planet):
        """Get base structured score for planet based on house and sign placement"""
        planet_data = self.planets[planet]
        house = planet_data['house']
        sign = int(planet_data['longitude'] / 30)
        
        base_score = 0
        
        if planet == 'Saturn':
            # Saturn discipline factors
            if house in [1, 6, 10]:  # Self-discipline, routine work, career structure
                base_score += 15
            elif house in [2, 7, 11]:  # Resources, partnerships, achievements
                base_score += 10
            
            # Saturn in structured signs
            if sign in [9, 10]:  # Capricorn, Aquarius
                base_score += 12
            elif sign in [1, 5, 6]:  # Taurus, Virgo, Libra
                base_score += 8
                
        elif planet == 'Mars':
            # Mars systematic action
            if house in [6, 10]:  # Work, career
                base_score += 12
            elif house in [1, 3, 11]:  # Initiative, action, achievements
                base_score += 8
            
            # Mars in earth signs (systematic)
            if sign in [1, 5, 9]:  # Taurus, Virgo, Capricorn
                base_score += 10
            elif sign in [0, 7]:  # Aries, Scorpio (own signs but less systematic)
                base_score += 6
                
        elif planet == 'Mercury':
            # Mercury analytical factors
            if house in [6, 10]:  # Analysis, career
                base_score += 10
            elif house in [1, 3, 9]:  # Thinking, communication, higher analysis
                base_score += 8
            
            # Mercury in analytical signs
            if sign in [5, 9]:  # Virgo, Capricorn
                base_score += 10
            elif sign in [1, 2]:  # Taurus, Gemini
                base_score += 6
        
        return base_score
    
    def _apply_planetary_conditions(self, planet, base_score, planet_analysis, yogi_data):
        """Apply existing planetary conditions (dignity, yogi, badhaka, etc.) to base score"""
        if base_score == 0:
            return 0
        
        final_score = base_score
        
        # Apply dignity from planet analysis
        dignity = planet_analysis.get('dignity', {}).get('status', 'neutral')
        if dignity == 'exalted':
            final_score *= 1.25
        elif dignity == 'own':
            final_score *= 1.15
        elif dignity == 'debilitated':
            final_score *= 0.70
        elif dignity == 'moolatrikona':
            final_score *= 1.20
        
        # Apply Yogi significance
        yogi_significance = self._analyze_planet_yogi_significance(planet, yogi_data)
        if yogi_significance['is_yogi_lord']:
            final_score *= 1.40
        elif yogi_significance['is_avayogi_lord']:
            final_score *= 0.75
        elif yogi_significance['is_dagdha_lord']:
            final_score *= 0.65
        elif yogi_significance['is_tithi_shunya_lord']:
            final_score *= 0.80
        
        # Apply Badhaka impact
        badhaka_impact = self._analyze_planet_badhaka_impact(planet)
        if badhaka_impact['is_badhaka_lord']:
            final_score *= 0.70
        elif badhaka_impact['is_in_badhaka_house']:
            final_score *= 0.85
        
        # Apply combustion and retrograde from planet analysis
        if planet_analysis.get('combust', False):
            final_score *= 0.80
        
        if planet_analysis.get('retrograde', False):
            if planet in ['Mercury', 'Venus']:
                final_score *= 1.10  # Beneficial for creativity/analysis
            else:
                final_score *= 0.90
        
        return round(final_score, 1)
    
    def _calculate_house_creative_influence(self, house_num, yogi_data):
        """Calculate creative influence of a house using existing analysis"""
        planets_in_house = [p for p, data in self.planets.items() if data['house'] == house_num]
        
        influence_score = 0
        for planet in planets_in_house:
            if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
                planet_analysis = self.planet_analyzer.analyze_planet(planet)
                base_influence = {'Venus': 12, 'Moon': 10, 'Mercury': 8, 'Jupiter': 6, 'Sun': 5, 'Mars': 4, 'Saturn': 2, 'Ketu': 10, 'Rahu': 6}
                planet_score = base_influence[planet]
                influence_score += self._apply_planetary_conditions(planet, planet_score, planet_analysis, yogi_data)
        
        return influence_score
    
    def _calculate_house_structured_influence(self, house_num, yogi_data):
        """Calculate structured influence of a house using existing analysis"""
        planets_in_house = [p for p, data in self.planets.items() if data['house'] == house_num]
        
        influence_score = 0
        for planet in planets_in_house:
            if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
                planet_analysis = self.planet_analyzer.analyze_planet(planet)
                base_influence = {'Saturn': 12, 'Mars': 10, 'Mercury': 8, 'Sun': 6, 'Jupiter': 5, 'Venus': 3, 'Moon': 2, 'Ketu': 8, 'Rahu': 4}
                planet_score = base_influence[planet]
                influence_score += self._apply_planetary_conditions(planet, planet_score, planet_analysis, yogi_data)
        
        return influence_score
    
    def _calculate_sign_emphasis(self, sign_types):
        """Calculate emphasis of sign types (water, earth, mutable, fixed)"""
        emphasis_score = 0
        
        for planet, data in self.planets.items():
            if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
                sign = int(data['longitude'] / 30)
                
                for sign_type in sign_types:
                    if sign_type == 'water' and sign in [3, 7, 11]:  # Cancer, Scorpio, Pisces
                        emphasis_score += 3
                    elif sign_type == 'earth' and sign in [1, 5, 9]:  # Taurus, Virgo, Capricorn
                        emphasis_score += 3
                    elif sign_type == 'mutable' and sign in [2, 5, 8, 11]:  # Gemini, Virgo, Sagittarius, Pisces
                        emphasis_score += 2
                    elif sign_type == 'fixed' and sign in [1, 4, 7, 10]:  # Taurus, Leo, Scorpio, Aquarius
                        emphasis_score += 2
                    elif sign_type == 'cardinal' and sign in [0, 3, 6, 9]:  # Aries, Cancer, Libra, Capricorn
                        emphasis_score += 2
        
        return emphasis_score
    
    def _analyze_planet_yogi_significance(self, planet, yogi_data):
        """Analyze planet's Yogi significance using existing logic"""
        return {
            'is_yogi_lord': planet == yogi_data['yogi']['lord'],
            'is_avayogi_lord': planet == yogi_data['avayogi']['lord'],
            'is_dagdha_lord': planet == yogi_data['dagdha_rashi']['lord'],
            'is_tithi_shunya_lord': planet == yogi_data['tithi_shunya_rashi']['lord']
        }
    
    def _analyze_planet_badhaka_impact(self, planet):
        """Analyze planet's Badhaka impact using existing calculator"""
        is_badhaka_lord = self.badhaka_calc.is_badhaka_planet(planet, self.ascendant_sign)
        badhaka_house = self.badhaka_calc.get_badhaka_house(self.ascendant_sign)
        planet_house = self.planets[planet]['house']
        is_in_badhaka_house = planet_house == badhaka_house
        
        return {
            'is_badhaka_lord': is_badhaka_lord,
            'is_in_badhaka_house': is_in_badhaka_house
        }
    
    def _determine_preference(self, creative_index, structured_index):
        """Determine primary work style preference"""
        if creative_index > structured_index + 15:
            return "Creative", "Strong"
        elif creative_index > structured_index + 5:
            return "Creative", "Moderate"
        elif structured_index > creative_index + 15:
            return "Structured", "Strong"
        elif structured_index > creative_index + 5:
            return "Structured", "Moderate"
        else:
            return "Balanced", "Adaptive"
    
    def _generate_work_behaviors(self, creative_index, structured_index):
        """Generate work style behavior examples with astrological reasons"""
        behaviors = {
            'creative_behaviors': [],
            'structured_behaviors': [],
            'work_environment': [],
            'project_approach': []
        }
        
        # Generate creative behaviors with reasons
        behaviors['creative_behaviors'] = self._generate_creative_behaviors_with_reasons()
        
        # Generate structured behaviors with reasons
        behaviors['structured_behaviors'] = self._generate_structured_behaviors_with_reasons()
        
        # Set environment and approach based on dominant preference
        if creative_index > structured_index:
            behaviors['work_environment'] = self._generate_creative_environment_with_reasons()
            behaviors['project_approach'] = self._generate_creative_approach_with_reasons()
        else:
            behaviors['work_environment'] = self._generate_structured_environment_with_reasons()
            behaviors['project_approach'] = self._generate_structured_approach_with_reasons()
        
        return behaviors
    
    def _generate_creative_behaviors_with_reasons(self):
        """Generate creative behaviors with specific astrological reasons"""
        behaviors = []
        
        # Venus creativity influence
        venus_house = self.planets['Venus']['house']
        venus_sign = int(self.planets['Venus']['longitude'] / 30)
        if venus_house in [1, 5, 10] or venus_sign in [1, 6, 11]:
            behaviors.append({
                'behavior': 'Thrives in open-ended projects without rigid deadlines',
                'reason': f'Venus in H{venus_house} enhances creative expression and artistic freedom'
            })
        
        # Moon imagination influence
        moon_house = self.planets['Moon']['house']
        moon_sign = int(self.planets['Moon']['longitude'] / 30)
        if moon_house in [5, 12] or moon_sign in [3, 7, 11]:
            behaviors.append({
                'behavior': 'Prefers brainstorming sessions over detailed planning meetings',
                'reason': f'Moon in H{moon_house} strengthens intuitive and imaginative thinking'
            })
        
        # Mercury flexibility
        mercury_house = self.planets['Mercury']['house']
        mercury_sign = int(self.planets['Mercury']['longitude'] / 30)
        if mercury_house in [3, 5, 9] or mercury_sign in [2, 5, 8, 11]:
            behaviors.append({
                'behavior': 'Works best with flexible schedules and creative freedom',
                'reason': f'Mercury in H{mercury_house} supports adaptable communication and thinking'
            })
        
        # 5th house influence
        planets_in_5th = [p for p, data in self.planets.items() if data['house'] == 5]
        if planets_in_5th:
            behaviors.append({
                'behavior': 'Enjoys experimenting with new approaches and methods',
                'reason': f'5th house occupied by {planets_in_5th[0]} promotes creative experimentation'
            })
        
        # Fallback if no specific influences
        if not behaviors:
            behaviors.append({
                'behavior': 'Shows creative potential in work approach',
                'reason': 'Natural creative tendencies based on overall chart patterns'
            })
        
        return behaviors
    
    def _generate_structured_behaviors_with_reasons(self):
        """Generate structured behaviors with specific astrological reasons"""
        behaviors = []
        
        # Saturn discipline influence
        saturn_house = self.planets['Saturn']['house']
        saturn_sign = int(self.planets['Saturn']['longitude'] / 30)
        if saturn_house in [1, 6, 10] or saturn_sign in [9, 10]:
            behaviors.append({
                'behavior': 'Excels in rule-based environments with clear procedures',
                'reason': f'Saturn in H{saturn_house} creates natural affinity for structured systems'
            })
        
        # Mars systematic action
        mars_house = self.planets['Mars']['house']
        mars_sign = int(self.planets['Mars']['longitude'] / 30)
        if mars_house in [6, 10] or mars_sign in [1, 5, 9]:
            behaviors.append({
                'behavior': 'Prefers detailed project plans and systematic workflows',
                'reason': f'Mars in H{mars_house} drives systematic and organized action'
            })
        
        # 6th house routine work
        planets_in_6th = [p for p, data in self.planets.items() if data['house'] == 6]
        if planets_in_6th:
            behaviors.append({
                'behavior': 'Works best with defined schedules and measurable outcomes',
                'reason': f'6th house occupied by {planets_in_6th[0]} emphasizes routine and measurable work'
            })
        
        # 10th house hierarchy
        planets_in_10th = [p for p, data in self.planets.items() if data['house'] == 10]
        if planets_in_10th:
            behaviors.append({
                'behavior': 'Values consistency and proven methodologies',
                'reason': f'10th house occupied by {planets_in_10th[0]} supports traditional career approaches'
            })
        
        # Fallback if no specific influences
        if not behaviors:
            behaviors.append({
                'behavior': 'Shows structured approach in work methods',
                'reason': 'Natural systematic tendencies based on overall chart patterns'
            })
        
        return behaviors
    
    def _generate_creative_environment_with_reasons(self):
        """Generate creative work environment preferences with reasons"""
        environment = []
        
        venus_house = self.planets['Venus']['house']
        venus_sign = int(self.planets['Venus']['longitude'] / 30)
        venus_sign_name = self._get_sign_name(venus_sign)
        
        if venus_house == 1:
            environment.append(f'Prefers inspiring, aesthetically pleasing workspaces - Venus in 1st house makes beauty and harmony essential to your personal expression')
        elif venus_house == 5:
            environment.append(f'Prefers inspiring, aesthetically pleasing workspaces - Venus in 5th house of creativity demands artistic and beautiful work environments')
        elif venus_house == 10:
            environment.append(f'Prefers inspiring, aesthetically pleasing workspaces - Venus in 10th house brings artistic sensibility to your career environment')
        else:
            environment.append(f'Prefers aesthetically pleasing workspaces - Venus in H{venus_house} in {venus_sign_name} influences your environmental preferences')
        
        moon_house = self.planets['Moon']['house']
        moon_sign = int(self.planets['Moon']['longitude'] / 30)
        moon_sign_name = self._get_sign_name(moon_sign)
        
        if moon_house == 11:
            environment.append(f'Works well in collaborative, dynamic environments - Moon in 11th house of networks creates need for group emotional connection')
        elif moon_house == 3:
            environment.append(f'Works well in collaborative, dynamic environments - Moon in 3rd house of communication supports interactive work settings')
        else:
            environment.append(f'Works well in emotionally supportive environments - Moon in H{moon_house} in {moon_sign_name} shapes your emotional work needs')
        
        # Check for mutable signs emphasis
        mutable_planets = [p for p, data in self.planets.items() if int(data['longitude'] / 30) in [2, 5, 8, 11]]
        if len(mutable_planets) >= 3:
            environment.append(f'Needs variety and change in daily routines - {len(mutable_planets)} planets in mutable signs create need for flexibility')
        else:
            environment.append(f'Needs some variety in routines - Chart patterns support adaptive work environments')
        
        return environment
    
    def _generate_creative_approach_with_reasons(self):
        """Generate creative project approach with reasons"""
        approach = []
        
        jupiter_house = self.planets['Jupiter']['house']
        jupiter_sign = int(self.planets['Jupiter']['longitude'] / 30)
        jupiter_sign_name = self._get_sign_name(jupiter_sign)
        
        if jupiter_house == 5:
            approach.append(f'Starts with big picture vision, fills in details later - Jupiter in 5th house of creativity expands your visionary approach')
        elif jupiter_house == 9:
            approach.append(f'Starts with big picture vision, fills in details later - Jupiter in 9th house of higher wisdom emphasizes philosophical perspective')
        else:
            approach.append(f'Starts with broader perspective - Jupiter in H{jupiter_house} in {jupiter_sign_name} influences your planning scope')
        
        # Check Mercury for adaptability
        mercury_house = self.planets['Mercury']['house']
        mercury_sign = int(self.planets['Mercury']['longitude'] / 30)
        mercury_sign_name = self._get_sign_name(mercury_sign)
        if mercury_sign in [2, 5, 8, 11]:  # Mutable signs
            approach.append(f'Adapts plans based on inspiration and new ideas - Mercury in {mercury_sign_name} supports flexible thinking and adaptation')
        else:
            approach.append(f'Adapts plans when needed - Mercury in H{mercury_house} in {mercury_sign_name} shapes your adaptability style')
        
        # Check 5th house for innovation
        planets_in_5th = [p for p, data in self.planets.items() if data['house'] == 5]
        if planets_in_5th:
            approach.append(f'Values innovation over proven methods - {planets_in_5th[0]} in 5th house of creativity drives original approaches')
        else:
            approach.append(f'Values some innovation in methods - 5th house influences in your chart support creative approaches')
        
        return approach
    
    def _generate_structured_environment_with_reasons(self):
        """Generate structured work environment preferences with reasons"""
        environment = []
        
        saturn_house = self.planets['Saturn']['house']
        saturn_sign = int(self.planets['Saturn']['longitude'] / 30)
        saturn_sign_name = self._get_sign_name(saturn_sign)
        
        if saturn_house == 1:
            environment.append(f'Prefers organized, systematic workspaces - Saturn in 1st house makes personal discipline and order essential to your identity')
        elif saturn_house == 6:
            environment.append(f'Prefers organized, systematic workspaces - Saturn in 6th house of daily work creates need for structured routines')
        elif saturn_house == 10:
            environment.append(f'Prefers organized, systematic workspaces - Saturn in 10th house of career demands professional structure and hierarchy')
        else:
            environment.append(f'Prefers organized workspaces - Saturn in H{saturn_house} in {saturn_sign_name} influences your approach to structure')
        
        # Check for planets in 6th house (work environment)
        planets_in_6th = [p for p, data in self.planets.items() if data['house'] == 6]
        if planets_in_6th:
            environment.append(f'Works well in hierarchical, process-driven environments - {planets_in_6th[0]} in 6th house of daily work supports systematic approaches')
        else:
            environment.append(f'Works well in process-driven environments - 6th house lord influences your work style preferences')
        
        # Check 10th house for responsibility patterns
        planets_in_10th = [p for p, data in self.planets.items() if data['house'] == 10]
        if planets_in_10th:
            environment.append(f'Needs clear expectations and defined responsibilities - {planets_in_10th[0]} in 10th house creates need for clear professional boundaries')
        else:
            environment.append(f'Needs clear expectations - 10th house patterns in your chart emphasize defined professional roles')
        
        return environment
    
    def _generate_structured_approach_with_reasons(self):
        """Generate structured project approach with reasons"""
        approach = []
        
        saturn_house = self.planets['Saturn']['house']
        saturn_sign = int(self.planets['Saturn']['longitude'] / 30)
        saturn_sign_name = self._get_sign_name(saturn_sign)
        
        if saturn_house == 1:
            approach.append(f'Creates detailed plans before starting execution - Saturn in 1st house makes thorough preparation part of your core approach')
        elif saturn_house == 6:
            approach.append(f'Creates detailed plans before starting execution - Saturn in 6th house of work methodology demands systematic preparation')
        elif saturn_house == 10:
            approach.append(f'Creates detailed plans before starting execution - Saturn in 10th house of career requires professional thoroughness')
        else:
            approach.append(f'Creates detailed plans before execution - Saturn in H{saturn_house} in {saturn_sign_name} shapes your planning approach')
        
        # Check Mars for systematic action
        mars_house = self.planets['Mars']['house']
        mars_sign = int(self.planets['Mars']['longitude'] / 30)
        mars_sign_name = self._get_sign_name(mars_sign)
        if mars_house in [6, 10] or mars_sign in [1, 5, 9]:  # Earth signs
            approach.append(f'Follows systematic processes and checkpoints - Mars in H{mars_house} in {mars_sign_name} drives methodical action')
        else:
            approach.append(f'Follows systematic processes - Mars in H{mars_house} influences your action methodology')
        
        # Check Mercury for analytical approach
        mercury_house = self.planets['Mercury']['house']
        mercury_sign = int(self.planets['Mercury']['longitude'] / 30)
        mercury_sign_name = self._get_sign_name(mercury_sign)
        if mercury_house in [6, 10] or mercury_sign in [5, 9]:  # Virgo, Capricorn
            approach.append(f'Values efficiency and measurable results - Mercury in H{mercury_house} in {mercury_sign_name} emphasizes analytical outcomes')
        else:
            approach.append(f'Values measurable results - Mercury in H{mercury_house} shapes your approach to measuring success')
        
        return approach
    
    def _get_calculation_breakdown(self, creative_scores, structured_scores):
        """Provide transparent calculation breakdown"""
        breakdown = {
            'creative_factors': [],
            'structured_factors': [],
            'key_planetary_influences': {}
        }
        
        # Creative factors
        for factor, score in creative_scores.items():
            if score > 0:
                factor_name = factor.replace('_', ' ').title()
                breakdown['creative_factors'].append(f"{factor_name}: +{score} points")
        
        # Structured factors
        for factor, score in structured_scores.items():
            if score > 0:
                factor_name = factor.replace('_', ' ').title()
                breakdown['structured_factors'].append(f"{factor_name}: +{score} points")
        
        # Key planetary influences
        for planet in ['Venus', 'Moon', 'Mercury', 'Mars', 'Saturn']:
            planet_data = self.planets[planet]
            house = planet_data['house']
            sign = int(planet_data['longitude'] / 30)
            sign_name = self._get_sign_name(sign)
            breakdown['key_planetary_influences'][planet] = f"H{house} in {sign_name}"
        
        return breakdown
    
    def analyze_solo_vs_team(self, birth_data):
        """Analyze solo vs team work preference using comprehensive planetary analysis"""
        
        # Calculate Yogi points and Badhaka data once
        yogi_data = self.yogi_calc.calculate_yogi_points(birth_data)
        
        # Calculate scores using existing planetary analysis
        solo_scores = self._calculate_solo_scores(yogi_data)
        team_scores = self._calculate_team_scores(yogi_data)
        
        # Calculate final indices
        solo_index = sum(solo_scores.values())
        team_index = sum(team_scores.values())
        
        # Determine primary preference
        primary_preference, preference_strength = self._determine_solo_team_preference(solo_index, team_index)
        
        # Generate work style behaviors
        work_behaviors = self._generate_solo_team_behaviors(solo_index, team_index)
        
        return {
            'solo_index': round(solo_index, 1),
            'team_index': round(team_index, 1),
            'primary_preference': primary_preference,
            'preference_strength': preference_strength,
            'solo_breakdown': solo_scores,
            'team_breakdown': team_scores,
            'work_behaviors': work_behaviors,
            'calculation_details': self._get_solo_team_calculation_breakdown(solo_scores, team_scores)
        }
    
    def _calculate_solo_scores(self, yogi_data):
        """Calculate solo work scores using existing planetary analysis"""
        scores = {
            'sun_independence': 0,
            'saturn_self_sufficiency': 0,
            'mars_earth_methodical': 0,
            'mercury_independent_thinking': 0,
            'fixed_signs_emphasis': 0,
            'ketu_detachment': 0
        }
        
        # Sun independence - houses 1, 8, 12
        sun_analysis = self.planet_analyzer.analyze_planet('Sun')
        sun_base_score = self._get_solo_sun_score()
        scores['sun_independence'] = self._apply_planetary_conditions('Sun', sun_base_score, sun_analysis, yogi_data)
        
        # Saturn self-sufficiency
        saturn_analysis = self.planet_analyzer.analyze_planet('Saturn')
        saturn_base_score = self._get_solo_saturn_score()
        scores['saturn_self_sufficiency'] = self._apply_planetary_conditions('Saturn', saturn_base_score, saturn_analysis, yogi_data)
        
        # Mars in earth signs - methodical self-directed action
        mars_analysis = self.planet_analyzer.analyze_planet('Mars')
        mars_base_score = self._get_solo_mars_score()
        scores['mars_earth_methodical'] = self._apply_planetary_conditions('Mars', mars_base_score, mars_analysis, yogi_data)
        
        # Mercury independent thinking - houses 3, 6
        mercury_analysis = self.planet_analyzer.analyze_planet('Mercury')
        mercury_base_score = self._get_solo_mercury_score()
        scores['mercury_independent_thinking'] = self._apply_planetary_conditions('Mercury', mercury_base_score, mercury_analysis, yogi_data)
        
        # Fixed signs emphasis
        scores['fixed_signs_emphasis'] = self._calculate_sign_emphasis(['fixed'])
        
        # Ketu detachment
        scores['ketu_detachment'] = self._calculate_ketu_detachment_influence(yogi_data)
        
        return scores
    
    def _calculate_team_scores(self, yogi_data):
        """Calculate team work scores using existing planetary analysis"""
        scores = {
            'moon_communication_networks': 0,
            'venus_collaboration': 0,
            'jupiter_group_wisdom': 0,
            'mercury_air_communication': 0,
            'cardinal_signs_emphasis': 0,
            'seventh_house_partnerships': 0,
            'eleventh_house_networks': 0
        }
        
        # Moon in houses 3, 7, 11 - communication, partnerships, networks
        moon_analysis = self.planet_analyzer.analyze_planet('Moon')
        moon_base_score = self._get_team_moon_score()
        scores['moon_communication_networks'] = self._apply_planetary_conditions('Moon', moon_base_score, moon_analysis, yogi_data)
        
        # Venus collaboration and harmony
        venus_analysis = self.planet_analyzer.analyze_planet('Venus')
        venus_base_score = self._get_team_venus_score()
        scores['venus_collaboration'] = self._apply_planetary_conditions('Venus', venus_base_score, venus_analysis, yogi_data)
        
        # Jupiter in houses 7, 11 - partnerships, group wisdom
        jupiter_analysis = self.planet_analyzer.analyze_planet('Jupiter')
        jupiter_base_score = self._get_team_jupiter_score()
        scores['jupiter_group_wisdom'] = self._apply_planetary_conditions('Jupiter', jupiter_base_score, jupiter_analysis, yogi_data)
        
        # Mercury in air signs - communication-oriented thinking
        mercury_analysis = self.planet_analyzer.analyze_planet('Mercury')
        mercury_base_score = self._get_team_mercury_score()
        scores['mercury_air_communication'] = self._apply_planetary_conditions('Mercury', mercury_base_score, mercury_analysis, yogi_data)
        
        # Cardinal signs emphasis
        scores['cardinal_signs_emphasis'] = self._calculate_sign_emphasis(['cardinal'])
        
        # 7th house strength
        scores['seventh_house_partnerships'] = self._calculate_house_team_influence(7, yogi_data)
        
        # 11th house networks
        scores['eleventh_house_networks'] = self._calculate_house_team_influence(11, yogi_data)
        
        return scores
    
    def _get_sign_name(self, sign_num):
        """Get sign name from number"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_num]
    
    def _get_solo_sun_score(self):
        """Get solo score for Sun based on houses 1, 8, 12"""
        sun_house = self.planets['Sun']['house']
        sun_sign = int(self.planets['Sun']['longitude'] / 30)
        
        base_score = 0
        
        if sun_house == 1:  # Self-reliance, independence
            base_score += 15
        elif sun_house == 8:  # Introspection, self-transformation
            base_score += 12
        elif sun_house == 12:  # Solitude, behind-the-scenes work
            base_score += 10
        
        # Sun in fixed signs (self-contained)
        if sun_sign in [1, 4, 7, 10]:  # Taurus, Leo, Scorpio, Aquarius
            base_score += 8
        
        return base_score
    
    def _get_solo_saturn_score(self):
        """Get solo score for Saturn - discipline, self-sufficiency"""
        saturn_house = self.planets['Saturn']['house']
        saturn_sign = int(self.planets['Saturn']['longitude'] / 30)
        
        base_score = 0
        
        # Saturn strong positions for self-discipline
        if saturn_house in [1, 6, 10]:  # Self-discipline, work, career
            base_score += 12
        elif saturn_house in [2, 8]:  # Resources, transformation
            base_score += 8
        
        # Saturn in own signs or exaltation
        if saturn_sign in [9, 10]:  # Capricorn, Aquarius
            base_score += 10
        elif saturn_sign == 6:  # Libra (exaltation)
            base_score += 8
        
        return base_score
    
    def _get_solo_mars_score(self):
        """Get solo score for Mars in earth signs - methodical, self-directed"""
        mars_house = self.planets['Mars']['house']
        mars_sign = int(self.planets['Mars']['longitude'] / 30)
        
        base_score = 0
        
        # Mars in earth signs - methodical action
        if mars_sign in [1, 5, 9]:  # Taurus, Virgo, Capricorn
            base_score += 12
        
        # Mars in houses supporting independent action
        if mars_house in [1, 3, 6]:  # Self, initiative, work
            base_score += 8
        
        return base_score
    
    def _get_solo_mercury_score(self):
        """Get solo score for Mercury in houses 3, 6 - independent thinking"""
        mercury_house = self.planets['Mercury']['house']
        mercury_sign = int(self.planets['Mercury']['longitude'] / 30)
        
        base_score = 0
        
        # Mercury in houses supporting independent thinking
        if mercury_house == 3:  # Independent communication and analysis
            base_score += 10
        elif mercury_house == 6:  # Analytical work, problem-solving
            base_score += 12
        
        # Mercury in earth signs (analytical, methodical)
        if mercury_sign in [1, 5, 9]:  # Taurus, Virgo, Capricorn
            base_score += 8
        
        return base_score
    
    def _get_team_moon_score(self):
        """Get team score for Moon in houses 3, 7, 11"""
        moon_house = self.planets['Moon']['house']
        moon_sign = int(self.planets['Moon']['longitude'] / 30)
        
        base_score = 0
        
        if moon_house == 3:  # Communication, collaboration
            base_score += 10
        elif moon_house == 7:  # Partnerships, one-on-one collaboration
            base_score += 12
        elif moon_house == 11:  # Networks, group emotional connection
            base_score += 15
        
        # Moon in cardinal signs (initiative in groups)
        if moon_sign in [0, 3, 6, 9]:  # Aries, Cancer, Libra, Capricorn
            base_score += 6
        
        return base_score
    
    def _get_team_venus_score(self):
        """Get team score for Venus - harmony, collaboration"""
        venus_house = self.planets['Venus']['house']
        venus_sign = int(self.planets['Venus']['longitude'] / 30)
        
        base_score = 0
        
        # Venus in partnership and collaboration houses
        if venus_house == 7:  # Partnerships
            base_score += 15
        elif venus_house == 11:  # Networks, group harmony
            base_score += 12
        elif venus_house in [3, 5]:  # Communication, creative collaboration
            base_score += 10
        
        # Venus in air signs (relationship-oriented)
        if venus_sign in [2, 6, 10]:  # Gemini, Libra, Aquarius
            base_score += 8
        
        return base_score
    
    def _get_team_jupiter_score(self):
        """Get team score for Jupiter in houses 7, 11"""
        jupiter_house = self.planets['Jupiter']['house']
        jupiter_sign = int(self.planets['Jupiter']['longitude'] / 30)
        
        base_score = 0
        
        if jupiter_house == 7:  # Partnership guidance and wisdom
            base_score += 12
        elif jupiter_house == 11:  # Group wisdom, network guidance
            base_score += 15
        elif jupiter_house in [3, 5]:  # Communication, teaching
            base_score += 8
        
        # Jupiter in air signs (social wisdom)
        if jupiter_sign in [2, 6, 10]:  # Gemini, Libra, Aquarius
            base_score += 6
        
        return base_score
    
    def _get_team_mercury_score(self):
        """Get team score for Mercury in air signs"""
        mercury_house = self.planets['Mercury']['house']
        mercury_sign = int(self.planets['Mercury']['longitude'] / 30)
        
        base_score = 0
        
        # Mercury in air signs - communication-oriented thinking
        if mercury_sign in [2, 6, 10]:  # Gemini, Libra, Aquarius
            base_score += 12
        
        # Mercury in communication and partnership houses
        if mercury_house in [3, 7, 11]:  # Communication, partnerships, networks
            base_score += 10
        
        return base_score
    
    def _calculate_ketu_detachment_influence(self, yogi_data):
        """Calculate Ketu's influence on detachment from group dynamics"""
        ketu_house = self.planets['Ketu']['house']
        
        influence_score = 0
        
        # Ketu in houses affecting group dynamics
        if ketu_house == 7:  # Detachment from partnerships
            influence_score += 10
        elif ketu_house == 11:  # Detachment from networks and groups
            influence_score += 12
        elif ketu_house in [3, 5]:  # Detachment from communication/creative groups
            influence_score += 8
        
        return influence_score
    
    def _calculate_house_team_influence(self, house_num, yogi_data):
        """Calculate team influence of houses 7 and 11"""
        planets_in_house = [p for p, data in self.planets.items() if data['house'] == house_num]
        
        influence_score = 0
        for planet in planets_in_house:
            if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
                planet_analysis = self.planet_analyzer.analyze_planet(planet)
                if house_num == 7:  # Partnership house
                    base_influence = {'Venus': 15, 'Jupiter': 12, 'Moon': 10, 'Mercury': 8, 'Sun': 6, 'Mars': 5, 'Saturn': 3}
                else:  # 11th house - networks
                    base_influence = {'Jupiter': 15, 'Moon': 12, 'Venus': 10, 'Mercury': 8, 'Sun': 6, 'Mars': 5, 'Saturn': 4}
                
                planet_score = base_influence[planet]
                influence_score += self._apply_planetary_conditions(planet, planet_score, planet_analysis, yogi_data)
        
        return influence_score
    
    def _determine_solo_team_preference(self, solo_index, team_index):
        """Determine primary solo vs team preference"""
        if solo_index > team_index + 15:
            return "Solo", "Strong"
        elif solo_index > team_index + 5:
            return "Solo", "Moderate"
        elif team_index > solo_index + 15:
            return "Team", "Strong"
        elif team_index > solo_index + 5:
            return "Team", "Moderate"
        else:
            return "Balanced", "Adaptive"
    
    def _generate_solo_team_behaviors(self, solo_index, team_index):
        """Generate solo vs team behavior examples with astrological reasons"""
        behaviors = {
            'solo_behaviors': [],
            'team_behaviors': [],
            'collaboration_style': [],
            'communication_approach': []
        }
        
        # Generate solo behaviors with reasons
        behaviors['solo_behaviors'] = self._generate_solo_behaviors_with_reasons()
        
        # Generate team behaviors with reasons
        behaviors['team_behaviors'] = self._generate_team_behaviors_with_reasons()
        
        # Set collaboration style and communication based on dominant preference
        if solo_index > team_index:
            behaviors['collaboration_style'] = self._generate_solo_collaboration_style()
            behaviors['communication_approach'] = self._generate_solo_communication_approach()
        else:
            behaviors['collaboration_style'] = self._generate_team_collaboration_style()
            behaviors['communication_approach'] = self._generate_team_communication_approach()
        
        return behaviors
    
    def _get_solo_team_calculation_breakdown(self, solo_scores, team_scores):
        """Provide transparent calculation breakdown for solo vs team analysis"""
        breakdown = {
            'solo_factors': [],
            'team_factors': [],
            'key_planetary_influences': {}
        }
        
        # Solo factors
        for factor, score in solo_scores.items():
            if score > 0:
                factor_name = factor.replace('_', ' ').title()
                breakdown['solo_factors'].append(f"{factor_name}: +{score} points")
        
        # Team factors
        for factor, score in team_scores.items():
            if score > 0:
                factor_name = factor.replace('_', ' ').title()
                breakdown['team_factors'].append(f"{factor_name}: +{score} points")
        
        # Key planetary influences
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Ketu']:
            planet_data = self.planets[planet]
            house = planet_data['house']
            sign = int(planet_data['longitude'] / 30)
            sign_name = self._get_sign_name(sign)
            breakdown['key_planetary_influences'][planet] = f"H{house} in {sign_name}"
        
        return breakdown
    
    def _generate_solo_behaviors_with_reasons(self):
        """Generate solo work behaviors with specific astrological reasons"""
        behaviors = []
        
        # Sun independence
        sun_house = self.planets['Sun']['house']
        if sun_house in [1, 8, 12]:
            if sun_house == 1:
                behaviors.append({
                    'behavior': 'Prefers independent research and self-directed projects',
                    'reason': f'Sun in 1st house makes self-reliance essential to your identity'
                })
            elif sun_house == 8:
                behaviors.append({
                    'behavior': 'Excels in behind-the-scenes analytical work',
                    'reason': f'Sun in 8th house creates preference for introspective, transformative work'
                })
            elif sun_house == 12:
                behaviors.append({
                    'behavior': 'Works best in quiet, solitary environments',
                    'reason': f'Sun in 12th house emphasizes solitude and behind-the-scenes contribution'
                })
        
        # Saturn self-sufficiency
        saturn_house = self.planets['Saturn']['house']
        saturn_sign = int(self.planets['Saturn']['longitude'] / 30)
        saturn_sign_name = self._get_sign_name(saturn_sign)
        if saturn_house in [1, 6, 10]:
            behaviors.append({
                'behavior': 'Takes full responsibility for project outcomes',
                'reason': f'Saturn in H{saturn_house} in {saturn_sign_name} creates strong self-discipline and individual accountability'
            })
        
        # Mars earth signs methodical
        mars_sign = int(self.planets['Mars']['longitude'] / 30)
        mars_sign_name = self._get_sign_name(mars_sign)
        if mars_sign in [1, 5, 9]:  # Earth signs
            behaviors.append({
                'behavior': 'Prefers methodical, step-by-step execution',
                'reason': f'Mars in {mars_sign_name} drives systematic, self-directed action'
            })
        
        # Mercury independent thinking
        mercury_house = self.planets['Mercury']['house']
        if mercury_house in [3, 6]:
            behaviors.append({
                'behavior': 'Enjoys independent analysis and problem-solving',
                'reason': f'Mercury in H{mercury_house} supports autonomous thinking and analysis'
            })
        
        return behaviors
    
    def _generate_team_behaviors_with_reasons(self):
        """Generate team work behaviors with specific astrological reasons"""
        behaviors = []
        
        # Moon communication networks
        moon_house = self.planets['Moon']['house']
        if moon_house in [3, 7, 11]:
            if moon_house == 3:
                behaviors.append({
                    'behavior': 'Thrives in collaborative communication and brainstorming',
                    'reason': f'Moon in 3rd house creates need for interactive communication'
                })
            elif moon_house == 7:
                behaviors.append({
                    'behavior': 'Excels in partnership-based projects',
                    'reason': f'Moon in 7th house emphasizes emotional connection through partnerships'
                })
            elif moon_house == 11:
                behaviors.append({
                    'behavior': 'Energized by group dynamics and team achievements',
                    'reason': f'Moon in 11th house creates emotional fulfillment through network success'
                })
        
        # Venus collaboration
        venus_house = self.planets['Venus']['house']
        venus_sign = int(self.planets['Venus']['longitude'] / 30)
        venus_sign_name = self._get_sign_name(venus_sign)
        if venus_house in [7, 11, 3, 5]:
            behaviors.append({
                'behavior': 'Naturally builds harmony and consensus in teams',
                'reason': f'Venus in H{venus_house} in {venus_sign_name} promotes collaborative relationships'
            })
        
        # Jupiter group wisdom
        jupiter_house = self.planets['Jupiter']['house']
        if jupiter_house in [7, 11]:
            behaviors.append({
                'behavior': 'Seeks guidance and wisdom through team collaboration',
                'reason': f'Jupiter in H{jupiter_house} expands wisdom through group interactions'
            })
        
        # Mercury air signs communication
        mercury_sign = int(self.planets['Mercury']['longitude'] / 30)
        mercury_sign_name = self._get_sign_name(mercury_sign)
        if mercury_sign in [2, 6, 10]:  # Air signs
            behaviors.append({
                'behavior': 'Excels in team communication and idea exchange',
                'reason': f'Mercury in {mercury_sign_name} emphasizes communication-oriented thinking'
            })
        
        return behaviors
    
    def _generate_solo_collaboration_style(self):
        """Generate solo-oriented collaboration style with reasons"""
        style = []
        
        saturn_house = self.planets['Saturn']['house']
        if saturn_house in [1, 6, 10]:
            style.append(f'Prefers clearly defined individual responsibilities within teams - Saturn in H{saturn_house} needs structured boundaries')
        
        sun_house = self.planets['Sun']['house']
        if sun_house in [1, 8, 12]:
            style.append(f'Contributes best when given independent tasks within group projects - Sun in H{sun_house} requires autonomous contribution')
        
        style.append('Values team meetings that are focused and outcome-oriented')
        
        return style
    
    def _generate_solo_communication_approach(self):
        """Generate solo-oriented communication approach with reasons"""
        approach = []
        
        mercury_house = self.planets['Mercury']['house']
        mercury_sign = int(self.planets['Mercury']['longitude'] / 30)
        mercury_sign_name = self._get_sign_name(mercury_sign)
        
        if mercury_house in [3, 6]:
            approach.append(f'Prefers written communication and detailed documentation - Mercury in H{mercury_house} supports analytical communication')
        
        approach.append(f'Communicates most effectively in one-on-one or small group settings - Mercury in {mercury_sign_name} influences communication style')
        approach.append('Values direct, purposeful communication over casual interaction')
        
        return approach
    
    def _generate_team_collaboration_style(self):
        """Generate team-oriented collaboration style with reasons"""
        style = []
        
        moon_house = self.planets['Moon']['house']
        if moon_house in [3, 7, 11]:
            style.append(f'Thrives in open, collaborative team environments - Moon in H{moon_house} needs group emotional connection')
        
        venus_house = self.planets['Venus']['house']
        if venus_house in [7, 11]:
            style.append(f'Naturally facilitates team harmony and consensus-building - Venus in H{venus_house} promotes group relationships')
        
        jupiter_house = self.planets['Jupiter']['house']
        if jupiter_house in [7, 11]:
            style.append(f'Seeks to expand team wisdom and collective growth - Jupiter in H{jupiter_house} emphasizes group development')
        
        return style
    
    def _generate_team_communication_approach(self):
        """Generate team-oriented communication approach with reasons"""
        approach = []
        
        mercury_sign = int(self.planets['Mercury']['longitude'] / 30)
        mercury_sign_name = self._get_sign_name(mercury_sign)
        
        if mercury_sign in [2, 6, 10]:  # Air signs
            approach.append(f'Excels in group discussions and brainstorming sessions - Mercury in {mercury_sign_name} supports interactive communication')
        
        moon_house = self.planets['Moon']['house']
        if moon_house in [3, 7, 11]:
            approach.append(f'Values emotional connection and rapport in team communication - Moon in H{moon_house} emphasizes relational communication')
        
        approach.append('Prefers collaborative decision-making processes')
        
        return approach