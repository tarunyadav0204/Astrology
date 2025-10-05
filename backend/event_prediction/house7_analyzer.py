import swisseph as swe
from datetime import datetime, timedelta
from .house_significations import HOUSE_SIGNIFICATIONS, SIGN_LORDS, NATURAL_BENEFICS, NATURAL_MALEFICS, EXALTATION_SIGNS, DEBILITATION_SIGNS
from .dasha_integration import DashaIntegration

class House7Analyzer:
    """Analyzes House 7 for marriage and partnership predictions"""
    
    def __init__(self, birth_data, chart_data):
        self.birth_data = birth_data
        self.chart_data = chart_data
        self.house_7_sign = chart_data['houses'][6]['sign']  # 7th house (0-indexed)
        self.house_7_lord = SIGN_LORDS[self.house_7_sign]
        self.dasha_system = DashaIntegration(birth_data)
        
    def analyze_house_strength(self):
        """Calculate overall strength of 7th house"""
        strength_factors = {
            'house_lord_strength': self._calculate_lord_strength(),
            'resident_planets_strength': self._calculate_resident_planets_strength(),
            'aspects_strength': self._calculate_aspects_strength(),
            'yogi_avayogi_impact': self._calculate_yogi_impact(),
            'friendship_harmony': self._calculate_friendship_harmony()
        }
        
        # Weighted average (traditional Vedic weights)
        total_strength = (
            strength_factors['house_lord_strength'] * 0.3 +
            strength_factors['resident_planets_strength'] * 0.25 +
            strength_factors['aspects_strength'] * 0.2 +
            strength_factors['yogi_avayogi_impact'] * 0.15 +
            strength_factors['friendship_harmony'] * 0.1
        )
        
        return {
            'total_strength': round(total_strength, 2),
            'factors': strength_factors,
            'interpretation': self._interpret_strength(total_strength)
        }
    
    def _calculate_lord_strength(self):
        """Calculate 7th house lord strength"""
        lord_planet = self.house_7_lord
        lord_position = None
        
        # Find lord's position
        for planet, data in self.chart_data['planets'].items():
            if planet == lord_planet:
                lord_position = data
                break
        
        if not lord_position:
            return 50  # Neutral if not found
        
        strength = 50  # Base strength
        
        # Exaltation/Debilitation
        if lord_position['sign'] == EXALTATION_SIGNS.get(lord_planet):
            strength += 30
        elif lord_position['sign'] == DEBILITATION_SIGNS.get(lord_planet):
            strength -= 30
        
        # Own sign
        if lord_position['sign'] in [s for s, l in SIGN_LORDS.items() if l == lord_planet]:
            strength += 20
        
        # House position (Kendra/Trikona are strong)
        lord_house = self._get_planet_house(lord_planet)
        if lord_house in [1, 4, 7, 10]:  # Kendra
            strength += 15
        elif lord_house in [1, 5, 9]:  # Trikona
            strength += 20
        elif lord_house in [6, 8, 12]:  # Dusthana
            strength -= 15
        
        return max(0, min(100, strength))
    
    def _calculate_resident_planets_strength(self):
        """Calculate strength of planets in 7th house"""
        resident_planets = self._get_planets_in_house(7)
        
        if not resident_planets:
            return 60  # Neutral if empty
        
        total_strength = 0
        for planet in resident_planets:
            planet_strength = 50
            
            # Natural benefic/malefic
            if planet in NATURAL_BENEFICS:
                planet_strength += 20
            elif planet in NATURAL_MALEFICS:
                planet_strength -= 10
            
            # Exaltation/Debilitation in 7th house
            planet_data = self.chart_data['planets'][planet]
            if planet_data['sign'] == EXALTATION_SIGNS.get(planet):
                planet_strength += 25
            elif planet_data['sign'] == DEBILITATION_SIGNS.get(planet):
                planet_strength -= 25
            
            total_strength += planet_strength
        
        return max(0, min(100, total_strength / len(resident_planets)))
    
    def _calculate_aspects_strength(self):
        """Calculate strength of aspects on 7th house"""
        aspecting_planets = self._get_aspecting_planets(7)
        
        if not aspecting_planets:
            return 50  # Neutral if no aspects
        
        total_strength = 0
        for planet in aspecting_planets:
            aspect_strength = 50
            
            # Benefic aspects are good for 7th house
            if planet in NATURAL_BENEFICS:
                aspect_strength += 15
            elif planet in NATURAL_MALEFICS:
                aspect_strength -= 10
            
            # Jupiter aspect is especially good for marriage
            if planet == 'Jupiter':
                aspect_strength += 20
            
            total_strength += aspect_strength
        
        return max(0, min(100, total_strength / len(aspecting_planets)))
    
    def _calculate_yogi_impact(self):
        """Calculate Yogi/Avayogi impact on 7th house"""
        # Simplified - would need Yogi calculation from main system
        return 50  # Neutral for now
    
    def _calculate_friendship_harmony(self):
        """Calculate friendship between 7th house planets and lord"""
        resident_planets = self._get_planets_in_house(7)
        
        if not resident_planets:
            return 60  # Neutral if empty
        
        # Would use friendship matrix from main system
        return 55  # Slightly positive for now
    
    def _get_planets_in_house(self, house_num):
        """Get planets residing in specified house"""
        house_sign = self.chart_data['houses'][house_num - 1]['sign']
        planets_in_house = []
        
        for planet, data in self.chart_data['planets'].items():
            if data['sign'] == house_sign:
                planets_in_house.append(planet)
        
        return planets_in_house
    
    def _get_planet_house(self, planet):
        """Get house number where planet is positioned"""
        planet_sign = self.chart_data['planets'][planet]['sign']
        
        for i, house in enumerate(self.chart_data['houses']):
            if house['sign'] == planet_sign:
                return i + 1
        return 1
    
    def _get_aspecting_planets(self, house_num):
        """Get planets aspecting the specified house (simplified)"""
        # Simplified aspect calculation - 7th house aspects
        aspecting = []
        target_house_sign = self.chart_data['houses'][house_num - 1]['sign']
        
        for planet, data in self.chart_data['planets'].items():
            # 7th aspect (opposition)
            aspect_sign = (data['sign'] + 6) % 12
            if aspect_sign == target_house_sign:
                aspecting.append(planet)
        
        return aspecting
    
    def _interpret_strength(self, strength):
        """Interpret numerical strength into descriptive text"""
        if strength >= 80:
            return "Excellent - Very favorable for marriage and partnerships"
        elif strength >= 65:
            return "Good - Favorable conditions for relationships"
        elif strength >= 50:
            return "Average - Mixed results, timing important"
        elif strength >= 35:
            return "Challenging - Obstacles in relationships, remedies needed"
        else:
            return "Difficult - Significant challenges, strong remedies required"
    
    def predict_marriage_timing(self, start_year=None, end_year=None):
        """Predict marriage timing based on dasha and transits"""
        if not start_year:
            start_year = datetime.now().year
        if not end_year:
            end_year = start_year + 10
        
        predictions = []
        
        # Get relevant planets for 7th house
        relevant_planets = [self.house_7_lord]
        relevant_planets.extend(self._get_planets_in_house(7))
        relevant_planets.extend(self._get_aspecting_planets(7))
        
        # Add Venus (natural significator for marriage)
        if 'Venus' not in relevant_planets:
            relevant_planets.append('Venus')
        
        # Get actual Dasha periods when relevant planets are active
        dasha_periods = self.dasha_system.find_relevant_dasha_periods(
            relevant_planets, start_year, end_year
        )
        
        # Convert dasha periods to predictions
        for period in dasha_periods:
            year = period['start'].year
            
            # Calculate strength based on dasha type and planet
            base_strength = self._calculate_dasha_strength(period)
            
            # Adjust for house strength
            house_strength = self.analyze_house_strength()['total_strength']
            final_strength = (base_strength + house_strength) / 2
            
            if final_strength >= 70:
                probability = 'High'
                events = ['marriage', 'engagement']
                description = f"{period['planet']} {period['type']} dasha - Strong marriage period"
            elif final_strength >= 55:
                probability = 'Medium'
                events = ['relationship_opportunities', 'partnership_formation']
                description = f"{period['planet']} {period['type']} dasha - Relationship opportunities"
            else:
                continue  # Skip low probability periods
            
            # Check if we already have a prediction for this year
            existing = next((p for p in predictions if p['year'] == year), None)
            if existing:
                # Update if this period is stronger
                if final_strength > existing['strength']:
                    existing.update({
                        'probability': probability,
                        'strength': final_strength,
                        'events': events,
                        'description': description,
                        'dasha_info': {
                            'type': period['type'],
                            'planet': period['planet'],
                            'start': period['start'].strftime('%Y-%m-%d'),
                            'end': period['end'].strftime('%Y-%m-%d')
                        }
                    })
            else:
                predictions.append({
                    'year': year,
                    'probability': probability,
                    'strength': round(final_strength, 1),
                    'events': events,
                    'description': description,
                    'dasha_info': {
                        'type': period['type'],
                        'planet': period['planet'],
                        'start': period['start'].strftime('%Y-%m-%d'),
                        'end': period['end'].strftime('%Y-%m-%d')
                    }
                })
        
        return sorted(predictions, key=lambda x: x['year'])
    
    def _calculate_dasha_strength(self, period):
        """Calculate strength based on dasha period characteristics"""
        base_strength = 50
        
        # Dasha type strength
        if period['strength'] == 'very_high':
            base_strength += 30  # Both Maha and Antar lords relevant
        elif period['strength'] == 'high':
            base_strength += 20  # Maha Dasha lord relevant
        elif period['strength'] == 'medium':
            base_strength += 10  # Antar Dasha lord relevant
        
        # Planet-specific adjustments for marriage
        planet = period['planet']
        if planet == 'Venus':  # Natural significator
            base_strength += 15
        elif planet == 'Jupiter':  # Benefic, good for marriage
            base_strength += 10
        elif planet in ['Sun', 'Mars', 'Saturn']:  # Malefics
            base_strength -= 5
        elif planet in ['Rahu', 'Ketu']:  # Nodes can delay
            base_strength -= 10
        
        # 7th house lord gets extra strength
        if planet == self.house_7_lord:
            base_strength += 15
        
        return max(0, min(100, base_strength))