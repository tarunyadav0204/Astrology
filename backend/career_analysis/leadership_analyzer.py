from calculators.amatyakaraka_analyzer import AmatyakarakaAnalyzer
from calculators.yogi_calculator import YogiCalculator
from calculators.badhaka_calculator import BadhakaCalculator
from calculators.planet_analyzer import PlanetAnalyzer

class LeadershipAnalyzer:
    def __init__(self, chart_data):
        self.chart_data = chart_data
        self.planets = chart_data['planets']
        self.ascendant = chart_data['ascendant']
        self.ascendant_sign = int(self.ascendant / 30)
        self.yogi_calc = YogiCalculator(chart_data)
        self.badhaka_calc = BadhakaCalculator(chart_data)
        self.planet_analyzer = PlanetAnalyzer(chart_data)
    
    def analyze_leadership_tendencies(self, birth_data):
        """Main leadership analysis method"""
        # Calculate Amatyakaraka
        amk_analyzer = AmatyakarakaAnalyzer(self.chart_data)
        amk_analysis = amk_analyzer.analyze_amatyakaraka()
        amk_planet = amk_analysis['amatyakaraka_planet']
        amatyakaraka = {
            'planet': amk_planet,
            'house': self.chart_data['planets'][amk_planet]['house']
        }
        
        # Calculate scores
        leadership_scores = self._calculate_leadership_scores()
        team_scores = self._calculate_team_scores()
        
        # Add Amatyakaraka influence
        amk_leadership_bonus, amk_team_bonus = self._calculate_amk_influence(amatyakaraka)
        leadership_scores['amatyakaraka_influence'] = amk_leadership_bonus
        team_scores['amatyakaraka_influence'] = amk_team_bonus
        
        # Calculate final indices
        leadership_index = sum(leadership_scores.values())
        team_index = sum(team_scores.values())
        
        # Determine primary tendency
        primary_tendency, tendency_strength = self._determine_tendency(leadership_index, team_index)
        
        # Calculate Yogi, Avayogi, Badhaka impact on leadership
        yogi_data = self.yogi_calc.calculate_yogi_points(birth_data)
        leadership_yogi_impact = self._analyze_leadership_yogi_impact(yogi_data, amatyakaraka)
        leadership_badhaka_impact = self._analyze_leadership_badhaka_impact(amatyakaraka)
        
        # Generate hierarchy behaviors with Yogi/Badhaka integration
        hierarchy_behaviors = self._generate_hierarchy_behaviors(leadership_index, team_index, amatyakaraka, yogi_data)
        
        return {
            'leadership_index': round(leadership_index, 1),
            'team_index': round(team_index, 1),
            'primary_tendency': primary_tendency,
            'tendency_strength': tendency_strength,
            'amatyakaraka': amatyakaraka,
            'leadership_breakdown': leadership_scores,
            'team_breakdown': team_scores,
            'hierarchy_behaviors': hierarchy_behaviors,
            'yogi_analysis': {
                'yogi_points': yogi_data,
                'leadership_impact': leadership_yogi_impact,
                'interpretation': self._get_leadership_yogi_interpretation(leadership_yogi_impact)
            },
            'badhaka_analysis': {
                'leadership_impact': leadership_badhaka_impact,
                'interpretation': self._get_leadership_badhaka_interpretation(leadership_badhaka_impact)
            },
            'calculation_details': self._get_calculation_breakdown(leadership_scores, team_scores)
        }
    
    def _calculate_leadership_scores(self):
        """Calculate leadership scores based on traditional Vedic authority indicators"""
        scores = {
            'sun_authority': 0,
            'mars_drive': 0,
            'jupiter_guidance': 0,
            'tenth_house_career': 0,
            'fire_signs': 0,
            'angular_houses': 0
        }
        
        # Sun authority
        sun_data = self.planets['Sun']
        sun_house = sun_data['house']
        sun_sign = int(sun_data['longitude'] / 30)
        
        if sun_house in [1, 4, 7, 10]:
            scores['sun_authority'] += 15
        elif sun_house in [5, 9]:
            scores['sun_authority'] += 10
        
        if sun_sign == 4:  # Leo
            scores['sun_authority'] += 12
        elif sun_sign == 0:  # Aries
            scores['sun_authority'] += 10
        
        # Mars drive
        mars_data = self.planets['Mars']
        mars_house = mars_data['house']
        mars_sign = int(mars_data['longitude'] / 30)
        
        if mars_house in [1, 4, 7, 10]:
            scores['mars_drive'] += 12
        
        if mars_sign in [0, 7]:  # Aries, Scorpio
            scores['mars_drive'] += 10
        elif mars_sign == 9:  # Capricorn
            scores['mars_drive'] += 12
        
        # Jupiter guidance
        jupiter_data = self.planets['Jupiter']
        jupiter_house = jupiter_data['house']
        jupiter_sign = int(jupiter_data['longitude'] / 30)
        
        if jupiter_house in [1, 4, 7, 10]:
            scores['jupiter_guidance'] += 10
        elif jupiter_house in [5, 9]:
            scores['jupiter_guidance'] += 12
        
        if jupiter_sign in [8, 11]:  # Sagittarius, Pisces
            scores['jupiter_guidance'] += 8
        elif jupiter_sign == 3:  # Cancer
            scores['jupiter_guidance'] += 10
        
        # 10th house strength
        tenth_house_sign = (self.ascendant_sign + 9) % 12
        tenth_lord = self._get_house_lord(tenth_house_sign)
        tenth_lord_data = self.planets[tenth_lord]
        tenth_lord_house = tenth_lord_data['house']
        
        if tenth_lord_house in [1, 4, 7, 10]:
            scores['tenth_house_career'] += 12
        
        # Planets in 10th house
        planets_in_tenth = [p for p, data in self.planets.items() if data['house'] == 10]
        if 'Sun' in planets_in_tenth:
            scores['tenth_house_career'] += 8
        if 'Mars' in planets_in_tenth:
            scores['tenth_house_career'] += 6
        if 'Jupiter' in planets_in_tenth:
            scores['tenth_house_career'] += 5
        
        # Fire signs emphasis
        fire_sign_planets = 0
        for planet, data in self.planets.items():
            if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
                planet_sign = int(data['longitude'] / 30)
                if planet_sign in [0, 4, 8]:  # Aries, Leo, Sagittarius
                    fire_sign_planets += 1
        
        scores['fire_signs'] = fire_sign_planets * 3
        
        # Angular houses emphasis
        angular_planets = 0
        for planet, data in self.planets.items():
            if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
                if data['house'] in [1, 4, 7, 10]:
                    angular_planets += 1
        
        scores['angular_houses'] = angular_planets * 2
        
        return scores
    
    def _calculate_team_scores(self):
        """Calculate team orientation scores based on collaborative indicators"""
        scores = {
            'moon_empathy': 0,
            'venus_harmony': 0,
            'mercury_communication': 0,
            'seventh_house_partnerships': 0,
            'eleventh_house_groups': 0,
            'water_air_signs': 0
        }
        
        # Moon empathy
        moon_data = self.planets['Moon']
        moon_house = moon_data['house']
        moon_sign = int(moon_data['longitude'] / 30)
        
        if moon_house in [4, 7, 11]:
            scores['moon_empathy'] += 12
        elif moon_house in [5, 9]:
            scores['moon_empathy'] += 8
        
        if moon_sign == 3:  # Cancer
            scores['moon_empathy'] += 10
        elif moon_sign == 1:  # Taurus
            scores['moon_empathy'] += 8
        
        # Venus harmony
        venus_data = self.planets['Venus']
        venus_house = venus_data['house']
        venus_sign = int(venus_data['longitude'] / 30)
        
        if venus_house in [7, 11]:
            scores['venus_harmony'] += 12
        elif venus_house == 4:
            scores['venus_harmony'] += 8
        
        if venus_sign in [1, 6]:  # Taurus, Libra
            scores['venus_harmony'] += 10
        elif venus_sign == 11:  # Pisces
            scores['venus_harmony'] += 8
        
        # Mercury communication
        mercury_data = self.planets['Mercury']
        mercury_house = mercury_data['house']
        mercury_sign = int(mercury_data['longitude'] / 30)
        
        if mercury_house in [3, 7, 11]:
            scores['mercury_communication'] += 10
        
        if mercury_sign in [2, 5]:  # Gemini, Virgo
            scores['mercury_communication'] += 8
        
        # 7th house partnerships
        seventh_house_sign = (self.ascendant_sign + 6) % 12
        seventh_lord = self._get_house_lord(seventh_house_sign)
        seventh_lord_data = self.planets[seventh_lord]
        seventh_lord_house = seventh_lord_data['house']
        
        if seventh_lord_house in [1, 4, 7, 10]:
            scores['seventh_house_partnerships'] += 10
        
        planets_in_seventh = [p for p, data in self.planets.items() if data['house'] == 7]
        if 'Venus' in planets_in_seventh:
            scores['seventh_house_partnerships'] += 8
        if 'Moon' in planets_in_seventh:
            scores['seventh_house_partnerships'] += 6
        if 'Mercury' in planets_in_seventh:
            scores['seventh_house_partnerships'] += 5
        
        # 11th house groups
        eleventh_house_sign = (self.ascendant_sign + 10) % 12
        eleventh_lord = self._get_house_lord(eleventh_house_sign)
        eleventh_lord_data = self.planets[eleventh_lord]
        eleventh_lord_house = eleventh_lord_data['house']
        
        if eleventh_lord_house in [1, 4, 7, 10]:
            scores['eleventh_house_groups'] += 8
        
        planets_in_eleventh = [p for p, data in self.planets.items() if data['house'] == 11]
        scores['eleventh_house_groups'] += len(planets_in_eleventh) * 3
        
        # Water and Air signs emphasis
        collaborative_planets = 0
        for planet, data in self.planets.items():
            if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
                planet_sign = int(data['longitude'] / 30)
                if planet_sign in [2, 3, 6, 7, 10, 11]:  # Water and Air signs
                    collaborative_planets += 1
        
        scores['water_air_signs'] = collaborative_planets * 2
        
        return scores
    
    def _calculate_amk_influence(self, amatyakaraka):
        """Calculate Amatyakaraka influence on leadership vs team orientation"""
        amk_planet = amatyakaraka['planet']
        amk_house = amatyakaraka['house']
        
        leadership_bonus = 0
        team_bonus = 0
        
        # Planet-based influence
        if amk_planet == 'Sun':
            leadership_bonus += 15
        elif amk_planet == 'Mars':
            leadership_bonus += 12
        elif amk_planet == 'Jupiter':
            leadership_bonus += 10
        elif amk_planet == 'Saturn':
            leadership_bonus += 8
        elif amk_planet == 'Moon':
            team_bonus += 12
        elif amk_planet == 'Venus':
            team_bonus += 10
        elif amk_planet == 'Mercury':
            team_bonus += 8
        
        # House-based influence
        if amk_house in [1, 10]:
            leadership_bonus += 8
        elif amk_house in [7, 11]:
            team_bonus += 8
        elif amk_house in [4, 12]:
            team_bonus += 5
        
        return leadership_bonus, team_bonus
    
    def _determine_tendency(self, leadership_index, team_index):
        """Determine primary tendency and strength"""
        if leadership_index > team_index + 15:
            return "Leader", "Strong"
        elif leadership_index > team_index + 5:
            return "Leader", "Moderate"
        elif team_index > leadership_index + 15:
            return "Team Player", "Strong"
        elif team_index > leadership_index + 5:
            return "Team Player", "Moderate"
        else:
            return "Balanced", "Adaptive"
    
    def _generate_hierarchy_behaviors(self, leadership_index, team_index, amatyakaraka, yogi_data=None):
        """Generate specific hierarchy behavior examples with inline explanations including Yogi/Badhaka impact"""
        sun_house = self.planets['Sun']['house']
        mars_house = self.planets['Mars']['house']
        moon_house = self.planets['Moon']['house']
        venus_house = self.planets['Venus']['house']
        mercury_house = self.planets['Mercury']['house']
        jupiter_house = self.planets['Jupiter']['house']
        saturn_house = self.planets['Saturn']['house']
        
        amk_planet = amatyakaraka['planet']
        amk_house = amatyakaraka['house']
        
        # Get Yogi significance for key planets
        mars_yogi = self._get_planet_yogi_status('Mars', yogi_data) if yogi_data else 'neutral'
        sun_yogi = self._get_planet_yogi_status('Sun', yogi_data) if yogi_data else 'neutral'
        saturn_yogi = self._get_planet_yogi_status('Saturn', yogi_data) if yogi_data else 'neutral'
        jupiter_yogi = self._get_planet_yogi_status('Jupiter', yogi_data) if yogi_data else 'neutral'
        
        # Get Badhaka status for key planets
        mars_badhaka = self._get_planet_badhaka_status('Mars')
        sun_badhaka = self._get_planet_badhaka_status('Sun')
        saturn_badhaka = self._get_planet_badhaka_status('Saturn')
        jupiter_badhaka = self._get_planet_badhaka_status('Jupiter')
        
        behaviors = {
            'as_subordinate': [],
            'as_peer': [],
            'as_leader': []
        }
        
        # As Subordinate behavior
        if leadership_index > team_index:
            # Amatyakaraka professional approach
            if amk_planet == 'Sun' and amk_house in [1, 10]:
                behaviors['as_subordinate'].append("Professional approach commands respect from superiors")
            elif amk_planet == 'Mars' and amk_house in [1, 6, 10]:
                behaviors['as_subordinate'].append("Takes decisive action even in subordinate position")
            elif amk_planet == 'Jupiter' and amk_house in [1, 9, 10]:
                behaviors['as_subordinate'].append("Advises superiors with wisdom and ethical guidance")
            
            # Sun authority behaviors
            if sun_house in [1, 10]:
                behaviors['as_subordinate'].append({
                    'behavior': "Takes initiative even in subordinate roles",
                    'reason': f"because Sun in H{sun_house} gives natural authority and leadership drive"
                })
                behaviors['as_subordinate'].append({
                    'behavior': "Seeks recognition and visibility from superiors",
                    'reason': f"because Sun in H{sun_house} craves acknowledgment and status"
                })
            elif sun_house in [5, 9]:
                behaviors['as_subordinate'].append({
                    'behavior': "Offers creative solutions and innovative ideas",
                    'reason': f"because Sun in H{sun_house} expresses authority through creativity"
                })
            
            # Mars drive behaviors with Yogi/Badhaka integration
            if mars_house in [1, 10]:
                mars_modifier = self._get_planetary_modifier('Mars', mars_yogi, mars_badhaka)
                behaviors['as_subordinate'].append({
                    'behavior': f"Challenges authority when disagreeing with decisions{mars_modifier['behavior_suffix']}",
                    'reason': f"because Mars in H{mars_house} creates independent, action-oriented energy{mars_modifier['reason_suffix']}"
                })
                behaviors['as_subordinate'].append({
                    'behavior': f"Prefers action-oriented tasks over routine work{mars_modifier['behavior_suffix']}",
                    'reason': f"because Mars in H{mars_house} needs dynamic, challenging activities{mars_modifier['reason_suffix']}"
                })
            elif mars_house in [3, 6]:
                behaviors['as_subordinate'].append("Competes with colleagues for advancement")
            
            # Jupiter guidance behaviors
            if jupiter_house in [1, 9, 10]:
                behaviors['as_subordinate'].append("Provides wisdom and guidance to superiors")
                behaviors['as_subordinate'].append("Questions decisions based on ethical principles")
        else:
            # Team-oriented subordinate behaviors
            if moon_house in [4, 7, 11]:
                behaviors['as_subordinate'].append("Highly responsive to supervisor's emotional needs")
                behaviors['as_subordinate'].append("Seeks approval and emotional connection with authority")
            elif moon_house in [6, 12]:
                behaviors['as_subordinate'].append("Serves diligently without seeking recognition")
            
            if venus_house in [7, 11]:
                behaviors['as_subordinate'].append("Maintains harmonious relationships with all levels")
                behaviors['as_subordinate'].append("Diplomatic in handling conflicts with superiors")
            
            if mercury_house in [3, 7, 11]:
                behaviors['as_subordinate'].append("Excellent at translating supervisor's vision to team")
                behaviors['as_subordinate'].append("Facilitates communication between different levels")
        
        # As Peer behavior
        if leadership_index > team_index:
            if sun_house in [1, 5, 9, 10]:
                behaviors['as_peer'].append({
                    'behavior': "Naturally becomes the informal leader among peers",
                    'reason': f"because Sun in H{sun_house} radiates confidence and natural authority"
                })
            if mars_house in [1, 3, 10, 11]:
                mars_modifier = self._get_planetary_modifier('Mars', mars_yogi, mars_badhaka)
                behaviors['as_peer'].append({
                    'behavior': f"Competitive with peers, drives team performance{mars_modifier['behavior_suffix']}",
                    'reason': f"because Mars in H{mars_house} brings competitive spirit and goal orientation{mars_modifier['reason_suffix']}"
                })
            if jupiter_house in [1, 5, 9, 10]:
                behaviors['as_peer'].append({
                    'behavior': "Mentors and guides colleagues",
                    'reason': f"because Jupiter in H{jupiter_house} enjoys teaching and mentoring others"
                })
            if saturn_house in [1, 10]:
                saturn_modifier = self._get_planetary_modifier('Saturn', saturn_yogi, saturn_badhaka)
                behaviors['as_peer'].append({
                    'behavior': f"Sets high standards and expects discipline from peers{saturn_modifier['behavior_suffix']}",
                    'reason': f"because Saturn in H{saturn_house} demands structure and accountability{saturn_modifier['reason_suffix']}"
                })
        else:
            if moon_house in [3, 4, 7, 11]:
                behaviors['as_peer'].append("Creates emotional bonds and team cohesion")
                behaviors['as_peer'].append("Mediates conflicts between team members")
            if venus_house in [3, 7, 11]:
                behaviors['as_peer'].append("Facilitates collaboration and consensus building")
                behaviors['as_peer'].append("Ensures everyone's voice is heard in discussions")
            if mercury_house in [3, 7, 11]:
                behaviors['as_peer'].append("Excellent networker and information coordinator")
        
        # As Leader behavior
        if leadership_index > team_index:
            if sun_house in [1, 10]:
                behaviors['as_leader'].append({
                    'behavior': "Commands respect through personal authority",
                    'reason': f"because Sun in H{sun_house} provides natural charisma and commanding presence"
                })
                behaviors['as_leader'].append({
                    'behavior': "Makes decisive choices and takes full responsibility",
                    'reason': f"because Sun in H{sun_house} gives confidence in decision-making and accountability"
                })
            if mars_house in [1, 10]:
                mars_modifier = self._get_planetary_modifier('Mars', mars_yogi, mars_badhaka)
                behaviors['as_leader'].append({
                    'behavior': f"Drives team with high energy and clear direction{mars_modifier['behavior_suffix']}",
                    'reason': f"because Mars in H{mars_house} provides dynamic leadership and goal clarity{mars_modifier['reason_suffix']}"
                })
                behaviors['as_leader'].append({
                    'behavior': f"Pushes team members to exceed their limits{mars_modifier['behavior_suffix']}",
                    'reason': f"because Mars in H{mars_house} brings high standards and performance drive{mars_modifier['reason_suffix']}"
                })
            if jupiter_house in [1, 9, 10]:
                behaviors['as_leader'].append({
                    'behavior': "Leads with wisdom and ethical principles",
                    'reason': f"because Jupiter in H{jupiter_house} provides moral guidance and wisdom"
                })
                behaviors['as_leader'].append({
                    'behavior': "Develops long-term vision and strategy",
                    'reason': f"because Jupiter in H{jupiter_house} sees the bigger picture and future possibilities"
                })
            if saturn_house in [1, 10]:
                saturn_modifier = self._get_planetary_modifier('Saturn', saturn_yogi, saturn_badhaka)
                behaviors['as_leader'].append({
                    'behavior': f"Implements structured systems and processes{saturn_modifier['behavior_suffix']}",
                    'reason': f"because Saturn in H{saturn_house} creates order and systematic approaches{saturn_modifier['reason_suffix']}"
                })
                behaviors['as_leader'].append({
                    'behavior': f"Demands discipline and accountability from team{saturn_modifier['behavior_suffix']}",
                    'reason': f"because Saturn in H{saturn_house} expects responsibility and commitment{saturn_modifier['reason_suffix']}"
                })
        else:
            if moon_house in [1, 4, 7, 10]:
                behaviors['as_leader'].append("Leads with empathy and emotional intelligence")
                behaviors['as_leader'].append("Creates nurturing environment for team growth")
            if venus_house in [1, 7, 10, 11]:
                behaviors['as_leader'].append("Builds consensus before making major decisions")
                behaviors['as_leader'].append("Maintains team harmony while achieving goals")
            if mercury_house in [1, 3, 10, 11]:
                behaviors['as_leader'].append("Communicates vision clearly and frequently")
                behaviors['as_leader'].append("Adapts leadership style based on team feedback")
        
        # Ensure each category has at least 2 behaviors
        for category in behaviors:
            if len(behaviors[category]) < 2:
                if category == 'as_subordinate':
                    behaviors[category].extend(["Adapts well to organizational hierarchy", "Balances personal initiative with following directions"])
                elif category == 'as_peer':
                    behaviors[category].extend(["Collaborates effectively with colleagues", "Shares resources and knowledge freely"])
                elif category == 'as_leader':
                    behaviors[category].extend(["Balances authority with approachability", "Focuses on team development and results"])
        
        return behaviors
    
    def _get_calculation_breakdown(self, leadership_scores, team_scores):
        """Provide transparent calculation breakdown"""
        breakdown = {
            'leadership_factors': [],
            'team_factors': [],
            'key_planetary_positions': {}
        }
        
        # Leadership factors explanation
        for factor, score in leadership_scores.items():
            if score > 0:
                factor_name = factor.replace('_', ' ').title()
                breakdown['leadership_factors'].append(f"{factor_name}: +{score} points")
        
        # Team factors explanation
        for factor, score in team_scores.items():
            if score > 0:
                factor_name = factor.replace('_', ' ').title()
                breakdown['team_factors'].append(f"{factor_name}: +{score} points")
        
        # Key planetary positions
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus']:
            if planet in self.planets:
                house = self.planets[planet]['house']
                sign = int(self.planets[planet]['longitude'] / 30)
                sign_name = self._get_sign_name(sign)
                breakdown['key_planetary_positions'][planet] = f"H{house} in {sign_name}"
        
        # Add Amatyakaraka info
        if 'amatyakaraka_influence' in leadership_scores or 'amatyakaraka_influence' in team_scores:
            breakdown['key_planetary_positions']['Amatyakaraka'] = "Professional Minister influence included"
        
        return breakdown
    
    def _analyze_leadership_yogi_impact(self, yogi_data, amatyakaraka):
        """Analyze Yogi impact on leadership tendencies"""
        amk_planet = amatyakaraka['planet']
        
        # Check if key leadership planets are Yogi lords
        yogi_lord = yogi_data['yogi']['lord']
        avayogi_lord = yogi_data['avayogi']['lord']
        dagdha_lord = yogi_data['dagdha_rashi']['lord']
        tithi_shunya_lord = yogi_data['tithi_shunya_rashi']['lord']
        
        leadership_planets = ['Sun', 'Mars', 'Jupiter', amk_planet]
        
        yogi_impact = {
            'yogi_enhanced_planets': [],
            'avayogi_obstructed_planets': [],
            'dagdha_damaged_planets': [],
            'tithi_shunya_affected_planets': [],
            'overall_impact_score': 50
        }
        
        impact_score = 50
        
        for planet in leadership_planets:
            if planet == yogi_lord:
                yogi_impact['yogi_enhanced_planets'].append(planet)
                impact_score += 20
            elif planet == avayogi_lord:
                yogi_impact['avayogi_obstructed_planets'].append(planet)
                impact_score -= 15
            elif planet == dagdha_lord:
                yogi_impact['dagdha_damaged_planets'].append(planet)
                impact_score -= 25
            elif planet == tithi_shunya_lord:
                yogi_impact['tithi_shunya_affected_planets'].append(planet)
                impact_score -= 10
        
        yogi_impact['overall_impact_score'] = max(0, min(100, impact_score))
        return yogi_impact
    
    def _analyze_leadership_badhaka_impact(self, amatyakaraka):
        """Analyze Badhaka impact on leadership tendencies"""
        amk_planet = amatyakaraka['planet']
        amk_house = amatyakaraka['house']
        
        # Check key leadership planets for Badhaka impact
        leadership_planets = ['Sun', 'Mars', 'Jupiter', amk_planet]
        badhaka_house = self.badhaka_calc.get_badhaka_house(self.ascendant_sign)
        badhaka_lord = self.badhaka_calc.get_badhaka_lord(self.ascendant_sign)
        
        badhaka_impact = {
            'badhaka_lord_planets': [],
            'badhaka_house_planets': [],
            'overall_impact_score': 0,
            'badhaka_house': badhaka_house,
            'badhaka_lord': badhaka_lord
        }
        
        impact_score = 0
        
        for planet in leadership_planets:
            # Check if planet IS the Badhaka lord
            if self.badhaka_calc.is_badhaka_planet(planet, self.ascendant_sign):
                badhaka_impact['badhaka_lord_planets'].append(planet)
                impact_score += 30
            
            # Check if planet is placed in Badhaka house
            planet_house = self.planets[planet]['house']
            if planet_house == badhaka_house:
                badhaka_impact['badhaka_house_planets'].append(planet)
                impact_score += 20
        
        badhaka_impact['overall_impact_score'] = min(100, impact_score)
        return badhaka_impact
    
    def _get_leadership_yogi_interpretation(self, yogi_impact):
        """Get interpretation for Yogi impact on leadership"""
        interpretations = []
        
        if yogi_impact['yogi_enhanced_planets']:
            planets = ', '.join(yogi_impact['yogi_enhanced_planets'])
            interpretations.append(f"Leadership enhanced by Yogi lord: {planets}")
            interpretations.append("Natural leadership abilities are blessed with beneficial cosmic energy")
        
        if yogi_impact['avayogi_obstructed_planets']:
            planets = ', '.join(yogi_impact['avayogi_obstructed_planets'])
            interpretations.append(f"Leadership obstructed by Avayogi lord: {planets}")
            interpretations.append("Leadership potential faces internal obstacles and self-doubt")
        
        if yogi_impact['dagdha_damaged_planets']:
            planets = ', '.join(yogi_impact['dagdha_damaged_planets'])
            interpretations.append(f"Leadership damaged by Dagdha lord: {planets}")
            interpretations.append("Leadership approach may be destructive or transformative")
        
        if yogi_impact['tithi_shunya_affected_planets']:
            planets = ', '.join(yogi_impact['tithi_shunya_affected_planets'])
            interpretations.append(f"Leadership affected by Tithi Shunya: {planets}")
            interpretations.append("Leadership success may feel spiritually empty at times")
        
        overall_score = yogi_impact['overall_impact_score']
        if overall_score > 70:
            interpretations.append("Overall Yogi influence strongly supports leadership development")
        elif overall_score < 40:
            interpretations.append("Yogi influence suggests challenges in leadership expression")
        else:
            interpretations.append("Moderate Yogi influence on leadership tendencies")
        
        return interpretations
    
    def _get_leadership_badhaka_interpretation(self, badhaka_impact):
        """Get interpretation for Badhaka impact on leadership"""
        if badhaka_impact['overall_impact_score'] == 0:
            return ["No significant Badhaka obstacles to leadership development"]
        
        interpretations = []
        
        if badhaka_impact['badhaka_lord_planets']:
            planets = ', '.join(badhaka_impact['badhaka_lord_planets'])
            interpretations.append(f"Leadership planets ARE Badhaka lords: {planets}")
            interpretations.append("Leadership creates its own obstacles - self-sabotaging patterns")
        
        if badhaka_impact['badhaka_house_planets']:
            planets = ', '.join(badhaka_impact['badhaka_house_planets'])
            house = badhaka_impact['badhaka_house']
            interpretations.append(f"Leadership planets in Badhaka house H{house}: {planets}")
            interpretations.append("Leadership effectiveness reduced by environmental obstacles")
        
        overall_score = badhaka_impact['overall_impact_score']
        if overall_score > 50:
            interpretations.append("Strong Badhaka influence - leadership faces significant hidden obstacles")
        elif overall_score > 25:
            interpretations.append("Moderate Badhaka influence on leadership expression")
        else:
            interpretations.append("Mild Badhaka obstacles to leadership development")
        
        return interpretations
    
    def _get_planet_yogi_status(self, planet, yogi_data):
        """Get planet's Yogi status (yogi, avayogi, dagdha, tithi_shunya, or neutral)"""
        if not yogi_data:
            return 'neutral'
        
        if planet == yogi_data['yogi']['lord']:
            return 'yogi'
        elif planet == yogi_data['avayogi']['lord']:
            return 'avayogi'
        elif planet == yogi_data['dagdha_rashi']['lord']:
            return 'dagdha'
        elif planet == yogi_data['tithi_shunya_rashi']['lord']:
            return 'tithi_shunya'
        else:
            return 'neutral'
    
    def _get_planet_badhaka_status(self, planet):
        """Get planet's Badhaka status"""
        is_badhaka_lord = self.badhaka_calc.is_badhaka_planet(planet, self.ascendant_sign)
        badhaka_house = self.badhaka_calc.get_badhaka_house(self.ascendant_sign)
        planet_house = self.planets[planet]['house']
        is_in_badhaka_house = planet_house == badhaka_house
        
        if is_badhaka_lord and is_in_badhaka_house:
            return 'double_badhaka'
        elif is_badhaka_lord:
            return 'badhaka_lord'
        elif is_in_badhaka_house:
            return 'in_badhaka_house'
        else:
            return 'neutral'
    
    def _get_planetary_modifier(self, planet, yogi_status, badhaka_status):
        """Get behavior and reason modifiers based on Yogi and Badhaka status"""
        behavior_suffix = ""
        reason_suffix = ""
        
        # Yogi status modifiers
        if yogi_status == 'yogi':
            behavior_suffix += " with exceptional cosmic support"
            reason_suffix += f", enhanced because {planet} IS the Yogi lord bringing beneficial energy"
        elif yogi_status == 'avayogi':
            behavior_suffix += " but faces internal obstacles"
            reason_suffix += f", complicated because {planet} IS the Avayogi lord creating self-sabotaging patterns"
        elif yogi_status == 'dagdha':
            behavior_suffix += " with destructive intensity"
            reason_suffix += f", intensified because {planet} IS the Dagdha lord bringing transformative destruction"
        elif yogi_status == 'tithi_shunya':
            behavior_suffix += " but may feel spiritually empty"
            reason_suffix += f", affected because {planet} IS the Tithi Shunya lord creating periods of void"
        
        # Badhaka status modifiers
        if badhaka_status == 'double_badhaka':
            behavior_suffix += " while creating and facing obstacles"
            reason_suffix += f", complicated because {planet} IS the Badhaka lord AND placed in Badhaka house"
        elif badhaka_status == 'badhaka_lord':
            behavior_suffix += " while creating hidden obstacles"
            reason_suffix += f", complicated because {planet} IS the Badhaka lord creating self-sabotage"
        elif badhaka_status == 'in_badhaka_house':
            behavior_suffix += " despite environmental obstacles"
            reason_suffix += f", challenged because {planet} is placed in the Badhaka house"
        
        return {
            'behavior_suffix': behavior_suffix,
            'reason_suffix': reason_suffix
        }
    
    def _get_house_lord(self, sign_num):
        """Get the lord of a zodiac sign"""
        lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        return lords[sign_num]
    
    def _get_sign_name(self, sign_num):
        """Get sign name from number"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_num]