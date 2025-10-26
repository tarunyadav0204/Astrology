"""Badhaka calculator extracted from BadhakaMarakaAnalyzer"""

from .base_calculator import BaseCalculator

class BadhakaCalculator(BaseCalculator):
    """Calculate Badhaka and Maraka lords and their effects"""
    
    def __init__(self, chart_data):
        super().__init__(chart_data)
        
        # Rasi types classification - extracted from badhaka_maraka.py
        self.chara_rasis = [0, 3, 6, 9]      # Aries, Cancer, Libra, Capricorn (Movable)
        self.sthira_rasis = [1, 4, 7, 10]    # Taurus, Leo, Scorpio, Aquarius (Fixed)
        self.dwiswabhava_rasis = [2, 5, 8, 11]  # Gemini, Virgo, Sagittarius, Pisces (Dual)
        
        # Badhaka house calculation by rasi type
        self.badhaka_houses = {
            'chara': 11,        # 11th house for movable signs
            'sthira': 9,        # 9th house for fixed signs
            'dwiswabhava': 7    # 7th house for dual signs
        }
        
        # Maraka houses
        self.primary_maraka_houses = [2, 7]      # 2nd and 7th houses
        self.secondary_maraka_houses = [12]      # 12th house
        
        # Effects - extracted from badhaka_maraka.py
        self.badhaka_effects = {
            'chara': {
                'nature': 'adaptable obstacles',
                'description': 'Obstacles that can be overcome through movement and change',
                'remedies': ['travel', 'change of location', 'dynamic action']
            },
            'sthira': {
                'nature': 'persistent obstacles', 
                'description': 'Stubborn obstacles requiring steady persistent effort',
                'remedies': ['patience', 'consistent effort', 'structural changes']
            },
            'dwiswabhava': {
                'nature': 'fluctuating obstacles',
                'description': 'Variable obstacles requiring flexible approaches',
                'remedies': ['adaptability', 'multiple strategies', 'timing awareness']
            }
        }
    
    def get_rasi_type(self, ascendant_sign):
        """Determine rasi type - extracted from BadhakaMarakaAnalyzer"""
        if ascendant_sign in self.chara_rasis:
            return 'chara'
        elif ascendant_sign in self.sthira_rasis:
            return 'sthira'
        elif ascendant_sign in self.dwiswabhava_rasis:
            return 'dwiswabhava'
        else:
            return 'chara'  # Default fallback
    
    def get_badhaka_house(self, ascendant_sign):
        """Get badhaka house number - extracted from BadhakaMarakaAnalyzer"""
        rasi_type = self.get_rasi_type(ascendant_sign)
        return self.badhaka_houses[rasi_type]
    
    def get_badhaka_lord(self, ascendant_sign):
        """Get badhaka lord planet - extracted from BadhakaMarakaAnalyzer"""
        badhaka_house = self.get_badhaka_house(ascendant_sign)
        badhaka_sign = (ascendant_sign + badhaka_house - 1) % 12
        return self.get_sign_lord(badhaka_sign)
    
    def get_maraka_lords(self, ascendant_sign):
        """Get maraka lord planets - extracted from BadhakaMarakaAnalyzer"""
        maraka_lords = []
        
        # Primary maraka lords (2nd and 7th house lords)
        for house in self.primary_maraka_houses:
            maraka_sign = (ascendant_sign + house - 1) % 12
            lord = self.get_sign_lord(maraka_sign)
            if lord:
                maraka_lords.append({
                    'planet': lord,
                    'house': house,
                    'type': 'primary'
                })
        
        # Secondary maraka lords
        for house in self.secondary_maraka_houses:
            maraka_sign = (ascendant_sign + house - 1) % 12
            lord = self.get_sign_lord(maraka_sign)
            if lord:
                maraka_lords.append({
                    'planet': lord,
                    'house': house,
                    'type': 'secondary'
                })
        
        return maraka_lords
    
    def is_badhaka_planet(self, planet, ascendant_sign):
        """Check if planet is badhaka lord - extracted from BadhakaMarakaAnalyzer"""
        badhaka_lord = self.get_badhaka_lord(ascendant_sign)
        return planet == badhaka_lord
    
    def is_maraka_planet(self, planet, ascendant_sign):
        """Check if planet is maraka lord - extracted from BadhakaMarakaAnalyzer"""
        maraka_lords = self.get_maraka_lords(ascendant_sign)
        maraka_planets = [lord['planet'] for lord in maraka_lords]
        return planet in maraka_planets
    
    def analyze_badhaka_impact_on_house(self, house_num, ascendant_sign):
        """Analyze how Badhaka affects a specific house"""
        badhaka_lord = self.get_badhaka_lord(ascendant_sign)
        rasi_type = self.get_rasi_type(ascendant_sign)
        
        if badhaka_lord not in self.chart_data['planets']:
            return {
                'has_impact': False,
                'badhaka_lord': badhaka_lord,
                'impact_score': 0
            }
        
        badhaka_data = self.chart_data['planets'][badhaka_lord]
        impact_score = 0
        
        # Direct placement in target house
        if badhaka_data.get('house') == house_num:
            impact_score += 40
        
        # Aspect to target house
        if self._planet_aspects_house(badhaka_lord, house_num):
            impact_score += 25
        
        # Badhaka lord strength affects impact
        if badhaka_data['sign'] == self.EXALTATION_SIGNS.get(badhaka_lord):
            impact_score += 15  # Strong badhaka creates more obstacles
        elif badhaka_data['sign'] == self.DEBILITATION_SIGNS.get(badhaka_lord):
            impact_score -= 10  # Weak badhaka creates fewer obstacles
        
        return {
            'has_impact': impact_score > 0,
            'badhaka_lord': badhaka_lord,
            'badhaka_house': self.get_badhaka_house(ascendant_sign),
            'rasi_type': rasi_type,
            'impact_score': impact_score,
            'effects': self.badhaka_effects[rasi_type],
            'interpretation': self._get_badhaka_interpretation(impact_score, rasi_type, house_num)
        }
    
    def get_chart_badhaka_summary(self, ascendant_sign):
        """Get complete badhaka summary - extracted from BadhakaMarakaAnalyzer"""
        rasi_type = self.get_rasi_type(ascendant_sign)
        badhaka_lord = self.get_badhaka_lord(ascendant_sign)
        badhaka_house = self.get_badhaka_house(ascendant_sign)
        maraka_lords = self.get_maraka_lords(ascendant_sign)
        
        return {
            'rasi_type': rasi_type,
            'badhaka': {
                'house': badhaka_house,
                'lord': badhaka_lord,
                'effects': self.badhaka_effects[rasi_type]
            },
            'maraka': {
                'lords': maraka_lords
            }
        }
    
    def _planet_aspects_house(self, planet, house_num):
        """Check if planet aspects house - reused from YogiCalculator"""
        planet_sign = self.chart_data['planets'][planet]['sign']
        target_house_sign = self.chart_data['houses'][house_num - 1]['sign']
        
        # 7th aspect (all planets)
        if (planet_sign + 6) % 12 == target_house_sign:
            return True
        
        # Special aspects
        if planet == 'Mars':
            if (planet_sign + 3) % 12 == target_house_sign or (planet_sign + 7) % 12 == target_house_sign:
                return True
        elif planet == 'Jupiter':
            if (planet_sign + 4) % 12 == target_house_sign or (planet_sign + 8) % 12 == target_house_sign:
                return True
        elif planet == 'Saturn':
            if (planet_sign + 2) % 12 == target_house_sign or (planet_sign + 9) % 12 == target_house_sign:
                return True
        
        return False
    
    def _get_badhaka_interpretation(self, impact_score, rasi_type, house_num):
        """Get badhaka interpretation for house"""
        if impact_score == 0:
            return "No significant Badhaka influence on this house"
        
        house_matters = {
            1: "personality and health", 2: "wealth and family", 3: "siblings and communication",
            4: "home and mother", 5: "children and creativity", 6: "health and enemies",
            7: "marriage and partnerships", 8: "longevity and transformation", 9: "luck and dharma",
            10: "career and reputation", 11: "gains and friendships", 12: "losses and spirituality"
        }
        
        matter = house_matters.get(house_num, "this area")
        nature = self.badhaka_effects[rasi_type]['nature']
        
        if impact_score > 50:
            return f"Strong Badhaka influence creates {nature} in {matter}"
        elif impact_score > 25:
            return f"Moderate Badhaka influence may cause {nature} in {matter}"
        else:
            return f"Mild Badhaka influence on {matter}"