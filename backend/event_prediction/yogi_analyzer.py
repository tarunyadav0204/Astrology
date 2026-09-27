from .house_significations import NATURAL_BENEFICS, NATURAL_MALEFICS, EXALTATION_SIGNS, DEBILITATION_SIGNS
from calculators.yogi_calculator import YogiCalculator
from calculators.avayogi_policy import avayogi_effect

class YogiAnalyzer:
    """Analyzes Yogi/Avayogi impact on houses"""
    
    def __init__(self, birth_data, chart_data):
        self.birth_data = birth_data
        self.chart_data = chart_data
        self.yogi_data = YogiCalculator(chart_data).calculate_yogi_points(birth_data)
        
    def _calculate_yogi_points(self):
        """Compatibility entry point; the shared calculator is authoritative."""
        return YogiCalculator(self.chart_data).calculate_yogi_points(self.birth_data)
    
    def analyze_yogi_impact_on_house(self, house_num):
        """Analyze how Yogi/Avayogi affects a specific house"""
        house_sign = self.chart_data['houses'][house_num - 1]['sign']
        impact_score = 50  # Neutral base
        
        yogi_lord = self.yogi_data['yogi']['lord']
        avayogi_lord = self.yogi_data['avayogi']['lord']
        dagdha_lord = (self.yogi_data.get('dagdha_rashi') or {}).get('lord')
        
        # Yogi lord impact (beneficial)
        yogi_impact = self._calculate_planet_impact_on_house(yogi_lord, house_num)
        impact_score += yogi_impact * 0.4  # 40% weight for Yogi
        
        # Avayogi contribution follows the shared cancellation/reversal policy.
        avayogi_impact = self._calculate_planet_impact_on_house(avayogi_lord, house_num)
        placement_house = self._get_planet_house(avayogi_lord)
        relation = (
            'occupant' if placement_house == house_num
            else 'aspector' if self._planet_aspects_house(avayogi_lord, house_num)
            else 'house_lord'
        )
        avayogi_resolution = avayogi_effect(
            placement_house=placement_house,
            target_house=house_num,
            relation=relation,
            tithi_shunya_overlap=bool(
                (self.yogi_data.get('avayogi_tithi_shunya_overlap') or {}).get('is_active')
            ),
        )
        if avayogi_resolution['polarity'] == 'supportive':
            impact_score += avayogi_impact * 0.3
        elif avayogi_resolution['polarity'] == 'challenging':
            impact_score -= avayogi_impact * 0.3
        
        # Dagdha lord impact (destructive)
        dagdha_impact = self._calculate_planet_impact_on_house(dagdha_lord, house_num)
        impact_score -= dagdha_impact * 0.2  # 20% negative weight for Dagdha
        
        return {
            'total_impact': max(0, min(100, impact_score)),
            'yogi_lord': yogi_lord,
            'avayogi_lord': avayogi_lord,
            'dagdha_lord': dagdha_lord,
            'yogi_impact': yogi_impact,
            'avayogi_impact': avayogi_impact,
            'avayogi_effect': avayogi_resolution,
            'dagdha_impact': dagdha_impact
        }
    
    def _calculate_planet_impact_on_house(self, planet, house_num):
        """Calculate how a planet impacts a specific house"""
        if planet not in self.chart_data['planets']:
            return 0
        
        planet_data = self.chart_data['planets'][planet]
        impact = 50  # Base impact
        
        # Planet's own strength
        if planet_data['sign'] == EXALTATION_SIGNS.get(planet):
            impact += 25
        elif planet_data['sign'] == DEBILITATION_SIGNS.get(planet):
            impact -= 25
        
        # Natural benefic/malefic
        if planet in NATURAL_BENEFICS:
            impact += 15
        elif planet in NATURAL_MALEFICS:
            impact -= 10
        
        # House position of the planet
        planet_house = self._get_planet_house(planet)
        if planet_house in [1, 4, 7, 10]:  # Kendra
            impact += 10
        elif planet_house in [1, 5, 9]:  # Trikona
            impact += 15
        elif planet_house in [6, 8, 12]:  # Dusthana
            impact -= 10
        
        # Aspect to target house
        if self._planet_aspects_house(planet, house_num):
            impact += 10
        
        return max(0, min(100, impact))
    
    def _get_planet_house(self, planet):
        """Get house number where planet is positioned"""
        planet_sign = self.chart_data['planets'][planet]['sign']
        
        for i, house in enumerate(self.chart_data['houses']):
            if house['sign'] == planet_sign:
                return i + 1
        return 1
    
    def _planet_aspects_house(self, planet, house_num):
        """Check if planet aspects the given house"""
        planet_sign = self.chart_data['planets'][planet]['sign']
        target_house_sign = self.chart_data['houses'][house_num - 1]['sign']
        
        # 7th aspect (all planets)
        if (planet_sign + 6) % 12 == target_house_sign:
            return True
        
        # Special aspects
        if planet == 'Mars':
            # 4th and 8th aspects
            if (planet_sign + 3) % 12 == target_house_sign or (planet_sign + 7) % 12 == target_house_sign:
                return True
        elif planet == 'Jupiter':
            # 5th and 9th aspects
            if (planet_sign + 4) % 12 == target_house_sign or (planet_sign + 8) % 12 == target_house_sign:
                return True
        elif planet == 'Saturn':
            # 3rd and 10th aspects
            if (planet_sign + 2) % 12 == target_house_sign or (planet_sign + 9) % 12 == target_house_sign:
                return True
        elif planet in ['Rahu', 'Ketu']:
            # Only 3rd and 11th aspects for Rahu/Ketu
            if (planet_sign + 2) % 12 == target_house_sign or (planet_sign + 10) % 12 == target_house_sign:
                return True
        
        return False
    
