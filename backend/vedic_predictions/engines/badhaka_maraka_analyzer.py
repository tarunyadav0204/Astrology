from event_prediction.house_significations import SIGN_LORDS

class BadhakaMarakaAnalyzer:
    """Reusable component for Badhaka and Maraka analysis"""
    
    def __init__(self):
        from ..config.badhaka_maraka import (
            CHARA_RASIS, STHIRA_RASIS, DWISWABHAVA_RASIS,
            BADHAKA_HOUSES, PRIMARY_MARAKA_HOUSES, SECONDARY_MARAKA_HOUSES,
            BADHAKA_EFFECTS, MARAKA_EFFECTS
        )
        
        self.chara_rasis = CHARA_RASIS
        self.sthira_rasis = STHIRA_RASIS
        self.dwiswabhava_rasis = DWISWABHAVA_RASIS
        self.badhaka_houses = BADHAKA_HOUSES
        self.primary_maraka_houses = PRIMARY_MARAKA_HOUSES
        self.secondary_maraka_houses = SECONDARY_MARAKA_HOUSES
        self.badhaka_effects = BADHAKA_EFFECTS
        self.maraka_effects = MARAKA_EFFECTS
    
    def get_rasi_type(self, ascendant_sign):
        """Determine rasi type (chara/sthira/dwiswabhava) for given ascendant"""
        if ascendant_sign in self.chara_rasis:
            return 'chara'
        elif ascendant_sign in self.sthira_rasis:
            return 'sthira'
        elif ascendant_sign in self.dwiswabhava_rasis:
            return 'dwiswabhava'
        else:
            return 'chara'  # Default fallback
    
    def get_badhaka_house(self, ascendant_sign):
        """Get badhaka house number for given ascendant"""
        rasi_type = self.get_rasi_type(ascendant_sign)
        return self.badhaka_houses[rasi_type]
    
    def get_badhaka_lord(self, ascendant_sign):
        """Get badhaka lord planet for given ascendant"""
        badhaka_house = self.get_badhaka_house(ascendant_sign)
        badhaka_sign = (ascendant_sign + badhaka_house - 1) % 12
        return SIGN_LORDS.get(badhaka_sign)
    
    def get_maraka_lords(self, ascendant_sign):
        """Get maraka lord planets for given ascendant"""
        maraka_lords = []
        
        # Primary maraka lords (2nd and 7th house lords)
        for house in self.primary_maraka_houses:
            maraka_sign = (ascendant_sign + house - 1) % 12
            lord = SIGN_LORDS.get(maraka_sign)
            if lord:
                maraka_lords.append({
                    'planet': lord,
                    'house': house,
                    'type': 'primary'
                })
        
        # Secondary maraka lords
        for house in self.secondary_maraka_houses:
            maraka_sign = (ascendant_sign + house - 1) % 12
            lord = SIGN_LORDS.get(maraka_sign)
            if lord:
                maraka_lords.append({
                    'planet': lord,
                    'house': house,
                    'type': 'secondary'
                })
        
        return maraka_lords
    
    def is_badhaka_planet(self, planet, ascendant_sign):
        """Check if planet is badhaka lord for given ascendant"""
        badhaka_lord = self.get_badhaka_lord(ascendant_sign)
        return planet == badhaka_lord
    
    def is_maraka_planet(self, planet, ascendant_sign):
        """Check if planet is maraka lord for given ascendant"""
        maraka_lords = self.get_maraka_lords(ascendant_sign)
        maraka_planets = [lord['planet'] for lord in maraka_lords]
        return planet in maraka_planets
    
    def get_maraka_type(self, planet, ascendant_sign):
        """Get maraka type (primary/secondary) for planet"""
        maraka_lords = self.get_maraka_lords(ascendant_sign)
        for lord in maraka_lords:
            if lord['planet'] == planet:
                return lord['type']
        return None
    
    def analyze_planet_badhaka_maraka(self, planet, natal_chart):
        """Comprehensive badhaka/maraka analysis for a planet"""
        if not natal_chart or 'ascendant' not in natal_chart:
            return {
                'is_badhaka': False,
                'is_maraka': False,
                'analysis': {}
            }
        
        ascendant_sign = int(natal_chart['ascendant'] / 30) % 12
        rasi_type = self.get_rasi_type(ascendant_sign)
        
        is_badhaka = self.is_badhaka_planet(planet, ascendant_sign)
        is_maraka = self.is_maraka_planet(planet, ascendant_sign)
        maraka_type = self.get_maraka_type(planet, ascendant_sign) if is_maraka else None
        
        analysis = {
            'rasi_type': rasi_type,
            'ascendant_sign': ascendant_sign
        }
        
        if is_badhaka:
            badhaka_house = self.get_badhaka_house(ascendant_sign)
            analysis['badhaka'] = {
                'house': badhaka_house,
                'effects': self.badhaka_effects[rasi_type],
                'description': f"Lord of {badhaka_house}th house - creates {self.badhaka_effects[rasi_type]['nature']}"
            }
        
        if is_maraka:
            maraka_info = self.maraka_effects[maraka_type]
            analysis['maraka'] = {
                'type': maraka_type,
                'effects': maraka_info,
                'description': f"{maraka_type.title()} maraka - {maraka_info['description']}"
            }
        
        return {
            'is_badhaka': is_badhaka,
            'is_maraka': is_maraka,
            'maraka_type': maraka_type,
            'analysis': analysis
        }
    
    def get_chart_badhaka_maraka_summary(self, natal_chart):
        """Get complete badhaka/maraka summary for a chart"""
        if not natal_chart or 'ascendant' not in natal_chart:
            return {}
        
        ascendant_sign = int(natal_chart['ascendant'] / 30) % 12
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
                'lords': maraka_lords,
                'primary_effects': self.maraka_effects['primary'],
                'secondary_effects': self.maraka_effects['secondary']
            }
        }