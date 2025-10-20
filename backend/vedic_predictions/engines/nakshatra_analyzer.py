from ..config.nakshatra_data import NAKSHATRA_DATA, NAKSHATRA_COMPATIBILITY, PLANETARY_RELATIONSHIPS, PADA_CHARACTERISTICS

class NakshatraAnalyzer:
    """Analyze Nakshatra-level influences for transit predictions"""
    
    def __init__(self):
        self.nakshatra_data = NAKSHATRA_DATA
        self.compatibility = NAKSHATRA_COMPATIBILITY
        self.relationships = PLANETARY_RELATIONSHIPS
        self.pada_info = PADA_CHARACTERISTICS
    
    def get_nakshatra_from_longitude(self, longitude):
        """Calculate nakshatra and pada from longitude"""
        # Each nakshatra is 13°20' (800 minutes)
        nakshatra_length = 13.333333  # 13°20'
        pada_length = nakshatra_length / 4  # 3°20' per pada
        
        nakshatra_number = int(longitude / nakshatra_length) + 1
        if nakshatra_number > 27:
            nakshatra_number = 27
        
        # Calculate pada (1-4)
        nakshatra_start = (nakshatra_number - 1) * nakshatra_length
        pada_position = longitude - nakshatra_start
        pada_number = int(pada_position / pada_length) + 1
        if pada_number > 4:
            pada_number = 4
        
        return {
            'nakshatra_number': nakshatra_number,
            'nakshatra_name': self.nakshatra_data[nakshatra_number]['name'],
            'nakshatra_lord': self.nakshatra_data[nakshatra_number]['lord'],
            'pada_number': pada_number,
            'pada_lord': self.nakshatra_data[nakshatra_number]['pada_lords'][pada_number - 1],
            'degree_in_nakshatra': pada_position,
            'degree_in_pada': pada_position % pada_length
        }
    
    def analyze_nakshatra_influence(self, transiting_planet, natal_planet, transiting_longitude, natal_longitude):
        """Comprehensive nakshatra analysis for transit aspect"""
        
        # Get nakshatra details for both planets
        transit_nakshatra = self.get_nakshatra_from_longitude(transiting_longitude)
        natal_nakshatra = self.get_nakshatra_from_longitude(natal_longitude)
        
        # Calculate compatibility between nakshatras
        compatibility_score = self._calculate_nakshatra_compatibility(
            transit_nakshatra, natal_nakshatra
        )
        
        # Analyze nakshatra lord influences
        lord_analysis = self._analyze_nakshatra_lords(
            transiting_planet, natal_planet, 
            transit_nakshatra['nakshatra_lord'], 
            natal_nakshatra['nakshatra_lord']
        )
        
        # Pada-level timing analysis
        timing_precision = self._analyze_pada_timing(
            transit_nakshatra, natal_nakshatra
        )
        
        # Generate nakshatra-specific effects
        nakshatra_effects = self._generate_nakshatra_effects(
            transiting_planet, transit_nakshatra, natal_nakshatra, compatibility_score
        )
        
        return {
            'transiting_nakshatra': transit_nakshatra,
            'natal_nakshatra': natal_nakshatra,
            'compatibility_score': compatibility_score,
            'lord_analysis': lord_analysis,
            'timing_precision': timing_precision,
            'nakshatra_effects': nakshatra_effects,
            'summary': self._create_nakshatra_summary(
                transiting_planet, natal_planet, 
                transit_nakshatra, natal_nakshatra, compatibility_score
            )
        }
    
    def _calculate_nakshatra_compatibility(self, transit_nak, natal_nak):
        """Calculate compatibility between two nakshatras"""
        
        # Same nakshatra
        if transit_nak['nakshatra_number'] == natal_nak['nakshatra_number']:
            return self.compatibility['same_nakshatra']
        
        # Check nakshatra lord relationship
        transit_lord = transit_nak['nakshatra_lord']
        natal_lord = natal_nak['nakshatra_lord']
        
        if transit_lord == natal_lord:
            return self.compatibility['same_lord']
        
        # Check planetary friendship
        if transit_lord in self.relationships:
            if natal_lord in self.relationships[transit_lord]['friends']:
                return self.compatibility['friendly_lords']
            elif natal_lord in self.relationships[transit_lord]['enemies']:
                return self.compatibility['enemy_lords']
            else:
                return self.compatibility['neutral_lords']
        
        # Check trine relationship (5th and 9th positions)
        nakshatra_diff = abs(transit_nak['nakshatra_number'] - natal_nak['nakshatra_number'])
        if nakshatra_diff in [4, 8, 22, 23]:  # 5th and 9th positions considering wrap-around
            return self.compatibility['trine_nakshatras']
        
        # Check opposition (7th position)
        if nakshatra_diff in [13, 14]:  # 7th position
            return self.compatibility['opposite_nakshatras']
        
        return self.compatibility['neutral_lords']
    
    def _analyze_nakshatra_lords(self, transiting_planet, natal_planet, transit_lord, natal_lord):
        """Analyze the influence of nakshatra lords"""
        
        analysis = {
            'transit_lord_influence': self._get_lord_influence(transit_lord, transiting_planet),
            'natal_lord_influence': self._get_lord_influence(natal_lord, natal_planet),
            'lord_relationship': self._get_lord_relationship(transit_lord, natal_lord),
            'combined_effect': ''
        }
        
        # Determine combined effect
        if analysis['lord_relationship'] == 'friendly':
            analysis['combined_effect'] = f"{transit_lord} and {natal_lord} create harmonious energy flow"
        elif analysis['lord_relationship'] == 'enemy':
            analysis['combined_effect'] = f"{transit_lord} and {natal_lord} create challenging energy dynamics"
        else:
            analysis['combined_effect'] = f"{transit_lord} and {natal_lord} create neutral energy exchange"
        
        return analysis
    
    def _get_lord_influence(self, lord, planet):
        """Get specific influence of nakshatra lord"""
        influences = {
            'Sun': 'Authority, leadership, vitality, ego expression',
            'Moon': 'Emotions, intuition, nurturing, changeability',
            'Mars': 'Action, courage, conflict, energy',
            'Mercury': 'Communication, intelligence, adaptability, commerce',
            'Jupiter': 'Wisdom, expansion, spirituality, guidance',
            'Venus': 'Love, beauty, creativity, harmony',
            'Saturn': 'Discipline, restriction, karma, endurance',
            'Rahu': 'Amplification, obsession, foreign influence, innovation',
            'Ketu': 'Detachment, spirituality, past-life karma, liberation'
        }
        
        base_influence = influences.get(lord, 'Unknown influence')
        
        if lord == planet:
            return f"Strong {base_influence} (same as transiting planet)"
        else:
            return f"Modified {base_influence} (through {lord}'s nakshatra)"
    
    def _get_lord_relationship(self, lord1, lord2):
        """Get relationship between two nakshatra lords"""
        if lord1 == lord2:
            return 'same'
        
        if lord1 in self.relationships:
            if lord2 in self.relationships[lord1]['friends']:
                return 'friendly'
            elif lord2 in self.relationships[lord1]['enemies']:
                return 'enemy'
        
        return 'neutral'
    
    def _analyze_pada_timing(self, transit_nak, natal_nak):
        """Analyze pada-level timing for precise predictions"""
        
        transit_pada = transit_nak['pada_number']
        natal_pada = natal_nak['pada_number']
        
        transit_pada_char = self.pada_info[transit_pada]
        natal_pada_char = self.pada_info[natal_pada]
        
        # Calculate timing intensity based on pada interaction
        if transit_pada == natal_pada:
            intensity = 'High'
            timing_note = f"Same pada ({transit_pada}) creates intense focus"
        elif abs(transit_pada - natal_pada) == 2:
            intensity = 'Medium'
            timing_note = f"Pada {transit_pada} to {natal_pada} creates balanced energy"
        else:
            intensity = 'Moderate'
            timing_note = f"Pada {transit_pada} to {natal_pada} creates gradual influence"
        
        return {
            'transit_pada_element': transit_pada_char['element'],
            'natal_pada_element': natal_pada_char['element'],
            'timing_intensity': intensity,
            'timing_note': timing_note,
            'elemental_harmony': self._check_elemental_harmony(
                transit_pada_char['element'], 
                natal_pada_char['element']
            )
        }
    
    def _check_elemental_harmony(self, element1, element2):
        """Check harmony between pada elements"""
        harmony_matrix = {
            ('Fire', 'Fire'): 'Intense',
            ('Fire', 'Air'): 'Supportive',
            ('Fire', 'Water'): 'Challenging',
            ('Fire', 'Earth'): 'Neutral',
            ('Air', 'Air'): 'Harmonious',
            ('Air', 'Water'): 'Neutral',
            ('Air', 'Earth'): 'Challenging',
            ('Water', 'Water'): 'Flowing',
            ('Water', 'Earth'): 'Supportive',
            ('Earth', 'Earth'): 'Stable'
        }
        
        key = (element1, element2) if (element1, element2) in harmony_matrix else (element2, element1)
        return harmony_matrix.get(key, 'Neutral')
    
    def _generate_nakshatra_effects(self, transiting_planet, transit_nak, natal_nak, compatibility):
        """Generate specific effects based on nakshatra combination"""
        
        transit_data = self.nakshatra_data[transit_nak['nakshatra_number']]
        natal_data = self.nakshatra_data[natal_nak['nakshatra_number']]
        
        effects = {
            'enhanced_qualities': [],
            'challenges': [],
            'opportunities': [],
            'timing_advice': ''
        }
        
        # Based on compatibility score
        if compatibility >= 0.75:
            effects['enhanced_qualities'] = [
                f"Harmonious blend of {transit_data['nature']} and {natal_data['nature']}",
                f"Enhanced {', '.join(transit_data['characteristics'][:2])}",
                f"Supportive energy from {transit_data['deity']} to {natal_data['deity']}"
            ]
            effects['timing_advice'] = "Excellent time for initiatives related to both nakshatras"
            
        elif compatibility >= 0.5:
            effects['enhanced_qualities'] = [
                f"Balanced interaction between {transit_data['nature']} and {natal_data['nature']}"
            ]
            effects['opportunities'] = [
                f"Learning from {transit_data['characteristics'][0]}",
                f"Developing {natal_data['characteristics'][0]}"
            ]
            effects['timing_advice'] = "Moderate period requiring conscious effort"
            
        else:
            effects['challenges'] = [
                f"Tension between {transit_data['nature']} and {natal_data['nature']}",
                f"Need to balance {transit_data['characteristics'][0]} with {natal_data['characteristics'][0]}"
            ]
            effects['opportunities'] = [
                "Growth through overcoming differences",
                "Learning patience and adaptation"
            ]
            effects['timing_advice'] = "Challenging period requiring careful navigation"
        
        return effects
    
    def _create_nakshatra_summary(self, transiting_planet, natal_planet, transit_nak, natal_nak, compatibility):
        """Create a concise summary of nakshatra analysis"""
        
        compatibility_desc = {
            1.0: "Perfect",
            0.75: "Excellent", 
            0.5: "Moderate",
            0.25: "Challenging"
        }
        
        compat_level = compatibility_desc.get(compatibility, "Neutral")
        
        return f"Transit {transiting_planet} in {transit_nak['nakshatra_name']} ({transit_nak['pada_number']}th pada) " \
               f"aspecting natal {natal_planet} in {natal_nak['nakshatra_name']} ({natal_nak['pada_number']}th pada). " \
               f"Nakshatra compatibility: {compat_level} ({int(compatibility*100)}%). " \
               f"Lords {transit_nak['nakshatra_lord']} and {natal_nak['nakshatra_lord']} create " \
               f"{self._get_lord_relationship(transit_nak['nakshatra_lord'], natal_nak['nakshatra_lord'])} energy."