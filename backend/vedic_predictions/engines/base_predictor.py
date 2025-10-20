from ..config.prediction_templates import PLANET_ASPECT_TEMPLATES, DASHA_AMPLIFIERS, TIMING_MODIFIERS
from ..config.remedies import PLANET_REMEDIES, HOUSE_REMEDIES
from event_prediction.house_significations import HOUSE_SIGNIFICATIONS

class BasePredictionEngine:
    def __init__(self):
        self.templates = PLANET_ASPECT_TEMPLATES
        self.remedies = PLANET_REMEDIES
        self.house_remedies = HOUSE_REMEDIES
        self.house_meanings = HOUSE_SIGNIFICATIONS
    
    def get_base_prediction(self, transiting_planet, aspect_type, natal_planet):
        """Get base prediction template for planet-aspect combination"""
        if transiting_planet not in self.templates:
            return None
        
        if aspect_type not in self.templates[transiting_planet]:
            return None
        
        template = self.templates[transiting_planet][aspect_type].copy()
        template['natal_planet'] = natal_planet
        template['transiting_planet'] = transiting_planet
        
        return template
    
    def calculate_intensity(self, dasha_relevance, timing_phase):
        """Calculate prediction intensity based on dasha and timing"""
        base_intensity = 1.0
        
        # Apply dasha amplification
        if dasha_relevance:
            for dasha_level, amplifier in DASHA_AMPLIFIERS.items():
                if dasha_level in dasha_relevance:
                    base_intensity *= amplifier
                    break
        
        # Apply timing modifier
        timing_modifier = TIMING_MODIFIERS.get(timing_phase, 1.0)
        
        return base_intensity * timing_modifier
    
    def get_house_context(self, house_number):
        """Get house significations for context"""
        return self.house_meanings.get(house_number, {})
    
    def get_remedies(self, transiting_planet, affected_houses):
        """Get remedies for challenging transits"""
        planet_remedies = self.remedies.get(transiting_planet, {})
        house_remedies = []
        
        for house in affected_houses:
            house_remedies.extend(self.house_remedies.get(house, []))
        
        return {
            'planet_remedies': planet_remedies,
            'house_remedies': list(set(house_remedies))
        }