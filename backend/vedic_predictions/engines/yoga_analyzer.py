class YogaAnalyzer:
    """Analyzes activated yogas based on house combinations from transit and dasha"""
    
    def __init__(self):
        self.yoga_definitions = {
            # Raja Yogas (Power/Status)
            'kendra_trikona': {
                'name': 'Kendra-Trikona Raja Yoga',
                'description': 'Power and authority through angular-trinal house connection',
                'houses': {'kendra': [1, 4, 7, 10], 'trikona': [1, 5, 9]},
                'type': 'raja',
                'strength': 'high'
            },
            'dharma_karma': {
                'name': 'Dharma-Karma Yoga',
                'description': 'Righteous success through 9th-10th house activation',
                'houses': [9, 10],
                'type': 'raja',
                'strength': 'high'
            },
            
            # Dhana Yogas (Wealth)
            'dhana_primary': {
                'name': 'Primary Dhana Yoga',
                'description': 'Wealth accumulation through 2nd-11th house connection',
                'houses': [2, 11],
                'type': 'dhana',
                'strength': 'high'
            },
            'dhana_speculation': {
                'name': 'Speculation Dhana Yoga',
                'description': 'Gains through speculation and investments',
                'houses': [5, 11],
                'type': 'dhana',
                'strength': 'medium'
            },
            'wealth_triangle': {
                'name': 'Wealth Triangle',
                'description': 'Complete wealth activation through self-resources-gains',
                'houses': [1, 2, 11],
                'type': 'dhana',
                'strength': 'high'
            },
            
            # Career/Professional
            'career_peak': {
                'name': 'Career Peak Yoga',
                'description': 'Professional recognition and advancement',
                'houses': [10],
                'type': 'career',
                'strength': 'medium',
                'multiple_activation': True
            },
            'service_success': {
                'name': 'Service Success Yoga',
                'description': 'Success in service and overcoming competition',
                'houses': [6, 10],
                'type': 'career',
                'strength': 'medium'
            },
            'communication_skills': {
                'name': 'Communication Skills Yoga',
                'description': 'Recognition through communication and skills',
                'houses': [3, 10],
                'type': 'career',
                'strength': 'medium'
            },
            
            # Relationship/Marriage
            'partnership': {
                'name': 'Partnership Yoga',
                'description': 'Opportunities in partnerships and relationships',
                'houses': [7],
                'type': 'relationship',
                'strength': 'medium',
                'multiple_activation': True
            },
            'marriage_wealth': {
                'name': 'Marriage-Wealth Yoga',
                'description': 'Marriage bringing wealth and social connections',
                'houses': [2, 7, 11],
                'type': 'relationship',
                'strength': 'high'
            },
            'romance_marriage': {
                'name': 'Romance-Marriage Yoga',
                'description': 'Romance leading to marriage',
                'houses': [5, 7],
                'type': 'relationship',
                'strength': 'medium'
            },
            
            # Spiritual/Knowledge
            'trikona_spiritual': {
                'name': 'Complete Trikona Yoga',
                'description': 'Spiritual growth and dharmic advancement',
                'houses': [1, 5, 9],
                'type': 'spiritual',
                'strength': 'high'
            },
            'higher_learning': {
                'name': 'Higher Learning Yoga',
                'description': 'Advanced education and guru connection',
                'houses': [4, 9],
                'type': 'spiritual',
                'strength': 'medium'
            },
            'foreign_spiritual': {
                'name': 'Foreign Spiritual Yoga',
                'description': 'Spiritual connections through foreign sources',
                'houses': [9, 12],
                'type': 'spiritual',
                'strength': 'medium'
            },
            
            # Transformation/Challenges
            'dusthana_transformation': {
                'name': 'Dusthana Transformation Yoga',
                'description': 'Growth through challenges and transformation',
                'houses': [6, 8, 12],
                'type': 'transformation',
                'strength': 'medium'
            },
            'health_victory': {
                'name': 'Health-Victory Yoga',
                'description': 'Overcoming health issues and enemies',
                'houses': [1, 6],
                'type': 'transformation',
                'strength': 'medium'
            }
        }
    
    def analyze_activated_yogas(self, house_activations):
        """Analyze which yogas are activated based on house combinations"""
        activated_yogas = []
        
        # Get all activated houses by priority
        all_houses = set()
        primary_houses = set()
        secondary_houses = set()
        tertiary_houses = set()
        
        for activation in house_activations.get('primary', []):
            house = activation['house']
            all_houses.add(house)
            primary_houses.add(house)
        
        for activation in house_activations.get('secondary', []):
            house = activation['house']
            all_houses.add(house)
            secondary_houses.add(house)
        
        for activation in house_activations.get('tertiary', []):
            house = activation['house']
            all_houses.add(house)
            tertiary_houses.add(house)
        
        # Check each yoga definition
        for yoga_key, yoga_def in self.yoga_definitions.items():
            yoga_strength = self._check_yoga_activation(
                yoga_def, all_houses, primary_houses, secondary_houses, tertiary_houses
            )
            
            if yoga_strength:
                activation_details = self._get_activation_details(
                    yoga_def, all_houses, primary_houses, secondary_houses, tertiary_houses, house_activations
                )
                activated_yogas.append({
                    'name': yoga_def['name'],
                    'description': yoga_def['description'],
                    'type': yoga_def['type'],
                    'strength': yoga_strength,
                    'base_strength': yoga_def['strength'],
                    'activation_details': activation_details
                })
        
        # Sort by strength and type
        activated_yogas.sort(key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}[x['strength']],
            {'raja': 5, 'dhana': 4, 'career': 3, 'relationship': 2, 'spiritual': 2, 'transformation': 1}[x['type']]
        ), reverse=True)
        
        return activated_yogas[:8]  # Limit to top 8 yogas
    
    def _check_yoga_activation(self, yoga_def, all_houses, primary_houses, secondary_houses, tertiary_houses):
        """Check if a specific yoga is activated and determine its strength"""
        required_houses = yoga_def['houses']
        
        # Handle special kendra-trikona case
        if isinstance(required_houses, dict) and 'kendra' in required_houses:
            kendra_activated = any(h in all_houses for h in required_houses['kendra'])
            trikona_activated = any(h in all_houses for h in required_houses['trikona'])
            if not (kendra_activated and trikona_activated):
                return None
            
            # Determine strength based on activation level
            if any(h in primary_houses for h in required_houses['kendra']) and \
               any(h in primary_houses for h in required_houses['trikona']):
                return 'high'
            elif any(h in primary_houses for h in required_houses['kendra'] + required_houses['trikona']):
                return 'medium'
            else:
                return 'low'
        
        # Handle regular house list
        elif isinstance(required_houses, list):
            # Check if multiple activation is required
            if yoga_def.get('multiple_activation'):
                # For single house yogas that need multiple activations
                if len(required_houses) == 1:
                    house = required_houses[0]
                    activation_count = sum([
                        1 for level_houses in [primary_houses, secondary_houses, tertiary_houses]
                        if house in level_houses
                    ])
                    if activation_count >= 2:
                        return 'high'
                    elif house in primary_houses:
                        return 'medium'
                    elif house in all_houses:
                        return 'low'
                    else:
                        return None
            
            # Check if all required houses are activated
            if not all(h in all_houses for h in required_houses):
                return None
            
            # Determine strength based on activation level
            primary_count = sum(1 for h in required_houses if h in primary_houses)
            secondary_count = sum(1 for h in required_houses if h in secondary_houses)
            
            if primary_count == len(required_houses):
                return 'high'
            elif primary_count >= len(required_houses) // 2:
                return 'medium'
            elif primary_count > 0 or secondary_count > 0:
                return 'low'
        
        return None
    
    def _get_activation_details(self, yoga_def, all_houses, primary_houses, secondary_houses, tertiary_houses, house_activations):
        """Get details about what is activating this yoga"""
        required_houses = yoga_def['houses']
        activation_details = []
        
        # Handle kendra-trikona case
        if isinstance(required_houses, dict) and 'kendra' in required_houses:
            kendra_houses = [h for h in required_houses['kendra'] if h in all_houses]
            trikona_houses = [h for h in required_houses['trikona'] if h in all_houses]
            
            for house in kendra_houses + trikona_houses:
                reasons = self._get_house_activation_reasons(house, house_activations)
                if reasons:
                    house_type = 'Kendra' if house in required_houses['kendra'] else 'Trikona'
                    activation_details.append(f"H{house} ({house_type}): {', '.join(reasons)}")
        
        # Handle regular house list
        elif isinstance(required_houses, list):
            for house in required_houses:
                if house in all_houses:
                    reasons = self._get_house_activation_reasons(house, house_activations)
                    if reasons:
                        activation_details.append(f"H{house}: {', '.join(reasons)}")
        
        return activation_details
    
    def _get_house_activation_reasons(self, house, house_activations):
        """Get reasons why a specific house is activated"""
        reasons = []
        
        # Check primary activations
        for activation in house_activations.get('primary', []):
            if activation['house'] == house:
                reasons.extend(activation['reasons'])
        
        # Check secondary activations
        for activation in house_activations.get('secondary', []):
            if activation['house'] == house:
                reasons.extend([f"{reason} (2°)" for reason in activation['reasons']])
        
        # Check tertiary activations
        for activation in house_activations.get('tertiary', []):
            if activation['house'] == house:
                reasons.extend([f"{reason} (3°)" for reason in activation['reasons']])
        
        return reasons