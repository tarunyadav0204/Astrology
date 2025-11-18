import swisseph as swe

class AshtakavargaCalculator:
    def __init__(self, birth_data, chart_data):
        self.birth_data = birth_data
        self.chart_data = chart_data
        self.planets = chart_data['planets']
        
        # Authentic Vedic Ashtakavarga rules - houses where each planet gives bindus to target planet
        self.contribution_rules = {
            'Sun': {
                'Sun': [1, 2, 4, 7, 8, 9, 10, 11],
                'Moon': [3, 6, 10, 11],
                'Mars': [1, 2, 4, 7, 8, 9, 10, 11],
                'Mercury': [3, 5, 6, 9, 10, 11, 12],
                'Jupiter': [5, 6, 9, 11],
                'Venus': [6, 7, 12],
                'Saturn': [1, 2, 4, 7, 8, 9, 10, 11],
                'Ascendant': [3, 4, 6, 10, 11, 12]
            },
            'Moon': {
                'Sun': [3, 6, 7, 8, 10, 11],
                'Moon': [1, 3, 6, 7, 10, 11],
                'Mars': [2, 3, 5, 6, 10, 11],
                'Mercury': [1, 3, 4, 5, 7, 8, 10, 11],
                'Jupiter': [1, 4, 7, 8, 10, 11, 12],
                'Venus': [3, 4, 5, 7, 9, 10, 11],
                'Saturn': [3, 5, 6, 11],
                'Ascendant': [3, 6, 10, 11, 12]
            },
            'Mars': {
                'Sun': [3, 5, 6, 10, 11],
                'Moon': [3, 6, 8, 10, 11],
                'Mars': [1, 2, 4, 7, 8, 10, 11],
                'Mercury': [3, 5, 6, 11],
                'Jupiter': [6, 10, 11, 12],
                'Venus': [6, 8, 11, 12],
                'Saturn': [1, 4, 7, 8, 9, 10, 11],
                'Ascendant': [1, 3, 6, 10, 11]
            },
            'Mercury': {
                'Sun': [5, 6, 9, 11, 12],
                'Moon': [2, 4, 6, 8, 10, 11],
                'Mars': [1, 2, 4, 7, 8, 9, 10, 11],
                'Mercury': [1, 3, 5, 6, 9, 10, 11, 12],
                'Jupiter': [6, 8, 11, 12],
                'Venus': [1, 3, 5, 6, 9, 11, 12],
                'Saturn': [1, 2, 4, 7, 8, 9, 10, 11],
                'Ascendant': [1, 2, 4, 6, 8, 10, 11]
            },
            'Jupiter': {
                'Sun': [1, 2, 3, 4, 7, 8, 9, 10, 11],
                'Moon': [2, 5, 7, 9, 11],
                'Mars': [1, 2, 4, 7, 8, 10, 11],
                'Mercury': [1, 2, 4, 5, 6, 9, 10, 11],
                'Jupiter': [1, 2, 3, 4, 7, 8, 10, 11],
                'Venus': [2, 5, 6, 9, 10, 11],
                'Saturn': [3, 5, 6, 12],
                'Ascendant': [1, 2, 4, 5, 6, 7, 9, 10, 11]
            },
            'Venus': {
                'Sun': [8, 11, 12],
                'Moon': [1, 2, 3, 4, 5, 8, 9, 11, 12],
                'Mars': [3, 4, 6, 9, 11, 12],
                'Mercury': [3, 5, 6, 9, 11],
                'Jupiter': [5, 8, 9, 10, 11],
                'Venus': [1, 2, 3, 4, 5, 8, 9, 10, 11],
                'Saturn': [3, 4, 5, 8, 9, 10, 11],
                'Ascendant': [1, 2, 3, 4, 5, 8, 9, 11]
            },
            'Saturn': {
                'Sun': [1, 2, 4, 7, 8, 10, 11],
                'Moon': [3, 5, 6, 11],
                'Mars': [3, 5, 6, 10, 11, 12],
                'Mercury': [6, 8, 9, 10, 11, 12],
                'Jupiter': [5, 6, 11, 12],
                'Venus': [6, 11, 12],
                'Saturn': [3, 5, 6, 11],
                'Ascendant': [1, 3, 4, 6, 10, 11]
            }
        }
    
    def calculate_individual_ashtakavarga(self, target_planet):
        """Calculate individual Ashtakavarga for a specific planet using authentic Vedic rules"""
        if target_planet not in self.contribution_rules:
            return {}
        
        # Initialize bindu array for 12 signs
        bindus = [0] * 12
        
        # Get rules for this target planet
        rules = self.contribution_rules[target_planet]
        
        # Check each contributor (Sun, Moon, Mars, etc.)
        for contributor, beneficial_houses in rules.items():
            # Get contributor's position
            if contributor == 'Ascendant':
                contributor_sign = int(self.chart_data['ascendant'] / 30)
            else:
                contributor_sign = self.planets[contributor]['sign']
            
            # Check each beneficial house from contributor
            for house_num in beneficial_houses:
                # Calculate which sign this house falls in
                target_sign = (contributor_sign + house_num - 1) % 12
                bindus[target_sign] += 1  # Add bindu (can be multiple from different contributors)
        
        return {
            'planet': target_planet,
            'bindus': {i: bindus[i] for i in range(12)},
            'total': sum(bindus)
        }
    
    def calculate_sarvashtakavarga(self):
        """Calculate Sarvashtakavarga (combined chart)"""
        sarva = {i: 0 for i in range(12)}
        individual_charts = {}
        
        # Calculate for all planets
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for planet in planets:
            chart = self.calculate_individual_ashtakavarga(planet)
            individual_charts[planet] = chart
            
            # Add to Sarvashtakavarga
            for sign, bindus in chart['bindus'].items():
                sarva[sign] += bindus
        
        return {
            'sarvashtakavarga': sarva,
            'total_bindus': sum(sarva.values()),
            'individual_charts': individual_charts
        }
    
    def get_ashtakavarga_analysis(self, chart_type='lagna'):
        """Get analysis based on chart type"""
        if chart_type == 'lagna':
            return self._analyze_lagna_ashtakavarga()
        elif chart_type == 'navamsa':
            return self._analyze_navamsa_ashtakavarga()
        elif chart_type == 'transit':
            return self._analyze_transit_ashtakavarga()
        else:
            return self._analyze_general_ashtakavarga()
    
    def _analyze_lagna_ashtakavarga(self):
        """Analyze Ashtakavarga for Lagna chart"""
        sarva = self.calculate_sarvashtakavarga()
        bindus = sarva['sarvashtakavarga']
        strongest_sign = max(bindus, key=bindus.get)
        weakest_sign = min(bindus, key=bindus.get)
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Get ascendant sign for personalized analysis
        asc_sign = int(self.chart_data['ascendant'] / 30)
        
        # House meanings for life analysis
        house_meanings = {
            0: 'personality and health', 1: 'wealth and family', 2: 'communication and siblings',
            3: 'home and mother', 4: 'education and children', 5: 'health and enemies',
            6: 'marriage and partnerships', 7: 'longevity and transformation', 8: 'fortune and dharma',
            9: 'career and reputation', 10: 'gains and friendships', 11: 'expenses and spirituality'
        }
        
        recommendations = []
        
        # Analyze each sign relative to ascendant
        for sign, count in bindus.items():
            house_num = (sign - asc_sign) % 12
            house_meaning = house_meanings[house_num]
            
            if count >= 30:
                if house_num == 0:
                    recommendations.append(f"Your {house_num + 1}st house ({sign_names[sign]}) has {count} bindus - Strong vitality and confidence. Good health and leadership abilities.")
                elif house_num == 1:
                    recommendations.append(f"Your {house_num + 1}nd house ({sign_names[sign]}) has {count} bindus - Strong financial potential. Good for wealth accumulation and family harmony.")
                elif house_num == 6:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Strong marriage prospects. Harmonious partnerships and business relationships.")
                elif house_num == 9:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Strong career potential. Recognition, authority, and professional success.")
                elif house_num == 10:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Excellent for gains and friendships. Strong network and income potential.")
                elif house_num == 11:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Strong spiritual inclination. Good for charitable giving and letting go of attachments.")
                elif house_num == 2:
                    recommendations.append(f"Your {house_num + 1}rd house ({sign_names[sign]}) has {count} bindus - Excellent communication skills. Strong bonds with siblings.")
                elif house_num == 3:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Strong connection with home and mother. Good property prospects.")
                elif house_num == 4:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Excellent for education and children. Creative abilities.")
                elif house_num == 5:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Good health and ability to overcome obstacles.")
                elif house_num == 7:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Strong transformative abilities. Good longevity.")
                elif house_num == 8:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Strong fortune and dharmic path. Good for higher learning.")
                else:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Strong support for {house_meaning}.")
            elif count <= 25:
                if house_num == 0:
                    recommendations.append(f"Your {house_num + 1}st house ({sign_names[sign]}) has {count} bindus - Focus on health and self-care. Build confidence gradually.")
                elif house_num == 1:
                    recommendations.append(f"Your {house_num + 1}nd house ({sign_names[sign]}) has {count} bindus - Be careful with finances. Plan investments wisely.")
                elif house_num == 2:
                    recommendations.append(f"Your {house_num + 1}rd house ({sign_names[sign]}) has {count} bindus - Work on communication skills. Strengthen sibling relationships.")
                elif house_num == 3:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Focus on home harmony. Be patient with mother's health.")
                elif house_num == 4:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Education may need extra effort. Be patient with children.")
                elif house_num == 5:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Focus on health maintenance. Avoid unnecessary conflicts.")
                elif house_num == 6:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Marriage may need extra effort. Work on relationship skills.")
                elif house_num == 7:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Be prepared for life changes. Focus on inner strength.")
                elif house_num == 8:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Develop spiritual practices. Be patient with fortune.")
                elif house_num == 9:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Career growth requires patience. Build skills steadily.")
                elif house_num == 10:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Focus on building genuine friendships. Be cautious with investments.")
                elif house_num == 11:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Control unnecessary expenses. Develop spiritual practices for inner peace.")
                else:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - {house_meaning.title()} may need extra attention.")
            else:
                # Average strength houses (26-29 bindus)
                if house_num == 0:
                    recommendations.append(f"Your {house_num + 1}st house ({sign_names[sign]}) has {count} bindus - Moderate health and confidence. Maintain good habits.")
                elif house_num == 1:
                    recommendations.append(f"Your {house_num + 1}nd house ({sign_names[sign]}) has {count} bindus - Steady financial growth. Balance saving and spending.")
                elif house_num == 2:
                    recommendations.append(f"Your {house_num + 1}rd house ({sign_names[sign]}) has {count} bindus - Good communication abilities. Keep nurturing sibling bonds.")
                elif house_num == 3:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Stable home environment. Maintain family connections.")
                elif house_num == 4:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Steady progress in education. Good relationship with children.")
                elif house_num == 5:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Moderate health. Handle conflicts diplomatically.")
                elif house_num == 6:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Stable relationships. Work on deeper connections.")
                elif house_num == 7:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Gradual transformation. Embrace change positively.")
                elif house_num == 8:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Steady fortune. Continue dharmic practices.")
                elif house_num == 9:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Consistent career progress. Keep building reputation.")
                elif house_num == 10:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Moderate gains. Maintain good friendships.")
                elif house_num == 11:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Balanced expenses. Continue spiritual practices.")
                else:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign]}) has {count} bindus - Moderate support for {house_meaning}.")
        
        return {
            'strongest_sign': {
                'sign': strongest_sign,
                'name': sign_names[strongest_sign],
                'bindus': bindus[strongest_sign]
            },
            'weakest_sign': {
                'sign': weakest_sign,
                'name': sign_names[weakest_sign],
                'bindus': bindus[weakest_sign]
            },
            'recommendations': recommendations
        }
    
    def _analyze_navamsa_ashtakavarga(self):
        """Analyze for Navamsa chart context"""
        sarva = self.calculate_sarvashtakavarga()
        bindus = sarva['sarvashtakavarga']
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Focus on 7th house (marriage) and Venus/Jupiter positions
        venus_sign = self.planets['Venus']['sign']
        jupiter_sign = self.planets['Jupiter']['sign']
        
        recommendations = []
        if bindus[venus_sign] >= 28:
            recommendations.append(f"Venus in {sign_names[venus_sign]} has {bindus[venus_sign]} bindus - Excellent marriage compatibility and romantic happiness.")
        elif bindus[venus_sign] >= 25:
            recommendations.append(f"Venus in {sign_names[venus_sign]} has {bindus[venus_sign]} bindus - Good marriage prospects with some adjustments needed.")
        else:
            recommendations.append(f"Venus in {sign_names[venus_sign]} has {bindus[venus_sign]} bindus - Marriage requires patience and understanding.")
            
        if bindus[jupiter_sign] >= 28:
            recommendations.append(f"Jupiter in {sign_names[jupiter_sign]} has {bindus[jupiter_sign]} bindus - Strong spiritual growth and wisdom development.")
        else:
            recommendations.append(f"Jupiter in {sign_names[jupiter_sign]} has {bindus[jupiter_sign]} bindus - Spiritual progress through dedicated practice.")
        
        return {
            'focus': 'Marriage and spiritual growth',
            'analysis': 'Navamsa Ashtakavarga reveals marriage compatibility and spiritual potential',
            'recommendations': recommendations
        }
    
    def _analyze_transit_ashtakavarga(self):
        """Analyze for transit context"""
        sarva = self.calculate_sarvashtakavarga()
        bindus = sarva['sarvashtakavarga']
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Find best timing signs
        best_signs = [sign for sign, count in bindus.items() if count >= 30]
        avoid_signs = [sign for sign, count in bindus.items() if count <= 25]
        
        recommendations = []
        if best_signs:
            recommendations.append(f"When planets transit through {', '.join([sign_names[s] for s in best_signs])}, you'll have strong support for new projects and important decisions.")
        if avoid_signs:
            recommendations.append(f"When planets transit through {', '.join([sign_names[s] for s in avoid_signs])}, be more cautious and avoid major life changes.")
        
        return {
            'focus': 'Timing for activities and decisions',
            'analysis': 'Transit Ashtakavarga shows when planetary energies are most supportive',
            'recommendations': recommendations
        }
    
    def _analyze_general_ashtakavarga(self):
        """General analysis for other charts"""
        sarva = self.calculate_sarvashtakavarga()
        bindus = sarva['sarvashtakavarga']
        
        strong_count = sum(1 for count in bindus.values() if count >= 30)
        weak_count = sum(1 for count in bindus.values() if count <= 25)
        
        return {
            'focus': 'Overall planetary strength distribution',
            'analysis': f'Your chart has {strong_count} areas of natural strength and {weak_count} areas needing attention',
            'recommendations': [f"Focus on developing your {strong_count} strong areas while gradually improving the {weak_count} weaker areas through conscious effort."]
        }