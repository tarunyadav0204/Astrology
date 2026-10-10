from typing import Dict, Any, List
from itertools import combinations

# Nakshatra list in order (index 0..26) for direct sector associations
NAKSHATRAS_ORDER = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
    'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
    'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
    'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
    'Uttara Bhadrapada', 'Revati'
]


class MundaneYogaCalculator:
    """Detects specialized yogas for war, famine, inflation, and economic events"""

    def __init__(self):
        # Heuristic nakshatra-ruler to commodity mapping; not SBC geometry
        self.commodity_nakshatras = {
            'Gold': ['Krittika', 'Uttara Phalguni', 'Uttara Ashadha'],  # Sun-ruled
            'Silver': ['Rohini', 'Hasta', 'Shravana'],  # Moon-ruled
            'Oil': ['Ardra', 'Swati', 'Shatabhisha'],  # Rahu-ruled
            'Grains': ['Punarvasu', 'Vishakha', 'Purva Bhadrapada'],  # Jupiter-ruled
            'Metals': ['Mrigashira', 'Chitra', 'Dhanishta'],  # Mars-ruled
            'Technology': ['Ashlesha', 'Jyeshtha', 'Revati']  # Mercury-ruled
        }

    def analyze_chart(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze mundane chart for economic and political yogas"""
        yogas = []

        # Graha Yuddha (Planetary War): within 1° - high-priority trigger
        graha_yuddhas = self._check_graha_yuddha(chart_data)
        yogas.extend(graha_yuddhas)

        # War Yoga: Mars-Saturn conjunction or aspect
        war_yoga = self._check_war_yoga(chart_data)
        if war_yoga:
            yogas.append(war_yoga)

        # Famine Yoga: Afflicted Moon and Jupiter
        famine_yoga = self._check_famine_yoga(chart_data)
        if famine_yoga:
            yogas.append(famine_yoga)

        # Inflation Yoga: Venus-Rahu in 2nd/11th house
        inflation_yoga = self._check_inflation_yoga(chart_data)
        if inflation_yoga:
            yogas.append(inflation_yoga)

        # Revolution Yoga: Uranus-Pluto hard aspect
        revolution_yoga = self._check_revolution_yoga(chart_data)
        if revolution_yoga:
            yogas.append(revolution_yoga)

        # Direct commodity associations only; no invented Vedha
        commodity_impacts = self._check_commodity_impacts(chart_data)

        for row in yogas:
            if row.get('type') != 'planetary_war':
                row['method'] = 'unvalidated_mundane_heuristic'
                row['classical_yoga_verified'] = False
                row['severity'] = 'unassessed'
                row['description'] = 'Calculated configuration only; does not establish the suggested external event.'
        return {
            'methodology_limits': ['No Sanghatta or Sarvatobhadra Chakra geometry is implemented.', 'Sector associations are heuristics, not verified price/event forecasts.'],
            'yogas': yogas,
            'commodity_impacts': commodity_impacts,
            'overall_assessment': self._generate_assessment(yogas, commodity_impacts)
        }

    def _check_graha_yuddha(self, chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Longitude-proximity candidates; neither victory nor outcomes are computed."""
        results = []
        planets = chart_data.get('planets', {})
        # Classical longitude-proximity screening of the five tara grahas.
        # This detects candidates; victory requires a separate declared doctrine.
        pairs = combinations(['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'], 2)
        for p1, p2 in pairs:
            a, b = planets.get(p1), planets.get(p2)
            if not a or not b:
                continue
            long1, long2 = a.get('longitude'), b.get('longitude')
            if long1 is None or long2 is None:
                continue
            diff = abs((long1 - long2 + 180) % 360 - 180)
            if diff <= 1.0:
                results.append({
                    'name': f'Graha Yuddha proximity candidate ({p1}-{p2})',
                    'type': 'planetary_war',
                    'severity': 'unassessed',
                    'graha_yuddha': True,
                    'status': 'proximity_candidate',
                    'separation_degrees': round(diff, 6),
                    'winner': None,
                    'method': 'five_tara_grahas_longitude_separation_at_most_one_degree',
                    'description': f'{p1} and {p2} are within 1° longitude. Proximity screen only; no winner, defeat or external outcome is established.',
                    'planets': [p1, p2],
                })
        return results
    
    def _check_war_yoga(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for war indicators"""
        planets = chart_data.get('planets', {})
        mars = planets.get('Mars', {})
        saturn = planets.get('Saturn', {})
        
        if not mars or not saturn:
            return None
        
        mars_long, saturn_long = mars.get('longitude'), saturn.get('longitude')
        if mars_long is None or saturn_long is None:
            return None
        diff = abs(mars_long - saturn_long)
        
        # Conjunction (within 10 degrees)
        if diff < 10 or diff > 350:
            return {
                'name': 'Mars–Saturn conjunction (heuristic)',
                'type': 'conflict',
                'severity': 'high',
                'description': 'Mars-Saturn conjunction indicates military conflicts, violence, or political tensions',
                'houses_affected': [mars.get('house'), saturn.get('house')]
            }
        
        return None
    
    def _check_famine_yoga(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for famine/drought indicators"""
        planets = chart_data.get('planets', {})
        moon = planets.get('Moon', {})
        jupiter = planets.get('Jupiter', {})
        
        if not moon or not jupiter:
            return None
        
        # Check if both are afflicted (in 6th, 8th, or 12th house)
        moon_house = moon.get('house', 0)
        jupiter_house = jupiter.get('house', 0)
        
        if moon_house in [6, 8, 12] and jupiter_house in [6, 8, 12]:
            return {
                'name': 'Moon/Jupiter dusthana placement (heuristic)',
                'type': 'scarcity',
                'severity': 'medium',
                'description': 'Afflicted Moon and Jupiter indicate agricultural issues, food scarcity, or water problems',
                'affected_areas': ['Agriculture', 'Food Supply', 'Water Resources']
            }
        
        return None
    
    def _check_inflation_yoga(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for inflation indicators"""
        planets = chart_data.get('planets', {})
        venus = planets.get('Venus', {})
        rahu = planets.get('Rahu', {})
        
        if not venus or not rahu:
            return None
        
        venus_house = venus.get('house', 0)
        rahu_house = rahu.get('house', 0)
        
        # Venus-Rahu in wealth houses (2nd or 11th)
        if (venus_house in [2, 11] and rahu_house in [2, 11]) or \
           (venus.get('longitude') is not None and rahu.get('longitude') is not None and abs((venus['longitude'] - rahu['longitude'] + 180) % 360 - 180) < 15):
            return {
                'name': 'Venus–Rahu association (heuristic)',
                'type': 'economic',
                'severity': 'medium',
                'description': 'Venus-Rahu combination indicates price rises, currency devaluation, or market speculation',
                'affected_sectors': ['Currency', 'Commodities', 'Real Estate']
            }
        
        return None
    
    def _check_revolution_yoga(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for revolutionary/transformative indicators"""
        planets = chart_data.get('planets', {})
        
        # This requires outer planets (Uranus, Pluto) which may not be in standard chart
        uranus = planets.get('Uranus', {})
        pluto = planets.get('Pluto', {})
        
        if not uranus or not pluto:
            return None
        
        uranus_long, pluto_long = uranus.get('longitude'), pluto.get('longitude')
        if uranus_long is None or pluto_long is None:
            return None
        diff = abs((uranus_long - pluto_long + 180) % 360 - 180)
        
        # Square (90°) or Opposition (180°)
        if (85 < diff < 95) or (175 < diff < 185):
            return {
                'name': 'Uranus–Pluto hard aspect (modern heuristic)',
                'type': 'transformation',
                'severity': 'high',
                'description': 'Uranus-Pluto hard aspect indicates revolutionary changes, regime shifts, or major social upheavals',
                'manifestations': ['Political Revolution', 'Technological Disruption', 'Social Movements']
            }
        
        return None
    
    def _check_commodity_impacts(self, chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Direct planetary-rulership sector analogy; no Sarvatobhadra Vedha."""
        impacts = []
        planets = chart_data.get('planets', {})
        malefics = ['Mars', 'Saturn', 'Rahu', 'Ketu']

        for planet_name in malefics:
            planet = planets.get(planet_name, {})
            if not planet:
                continue
            nak = planet.get('nakshatra')
            nakshatra = (nak.get('name', '') if isinstance(nak, dict) else nak if isinstance(nak, str) else '') or self._nakshatra_from_longitude(planet.get('longitude'))
            if not nakshatra:
                continue
            try:
                nak_index = NAKSHATRAS_ORDER.index(nakshatra)
            except ValueError:
                continue
            # Direct: planet in commodity nakshatra
            for commodity, nakshatras in self.commodity_nakshatras.items():
                if nakshatra in nakshatras:
                    impacts.append({
                        'commodity': commodity,
                        'planet': planet_name,
                        'nakshatra': nakshatra,
                        'impact_type': 'direct',
                        'method': 'planetary_rulership_sector_analogy',
                        'classical_sarvatobhadra_vedha': False,
                        'impact': 'price_volatility',
                        'prediction': f"{planet_name} in {nakshatra} suggests volatility in {commodity} prices"
                    })
        return impacts
    
    def _nakshatra_from_longitude(self, longitude: float) -> str:
        if longitude is None:
            return ''
        span = 360 / 27
        idx = int(longitude / span) % 27
        return NAKSHATRAS_ORDER[idx]

    def _generate_assessment(self, yogas: List[Dict], commodity_impacts: List[Dict]) -> str:
        """Generate overall mundane assessment"""
        if not yogas and not commodity_impacts:
            return "No configured indicators detected; this is not evidence of stability."
        return "Configurations detected; external-event severity and predictive validity are unassessed."
