from typing import Dict, Any, List

# Nakshatra list in order (index 0..26) for Vedha calculation
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
        # Sarvatobhadra Chakra: Nakshatra-Commodity mapping
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

        # Commodity impacts (direct + Vedha)
        commodity_impacts = self._check_commodity_impacts(chart_data)

        return {
            'yogas': yogas,
            'commodity_impacts': commodity_impacts,
            'overall_assessment': self._generate_assessment(yogas, commodity_impacts)
        }

    def _check_graha_yuddha(self, chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Graha Yuddha: two planets within 1° - sudden shocks, leadership events, market crashes."""
        results = []
        planets = chart_data.get('planets', {})
        planet_names = [p for p in planets if p not in ('Rahu', 'Ketu') or True]
        # Pairs that matter for mundane (all classical + nodes)
        pairs = [
            ('Mars', 'Saturn'), ('Sun', 'Mars'), ('Sun', 'Mercury'), ('Mars', 'Mercury'),
            ('Jupiter', 'Saturn'), ('Venus', 'Saturn'), ('Venus', 'Mars'),
            ('Sun', 'Venus'), ('Mercury', 'Jupiter'), ('Moon', 'Mars'), ('Moon', 'Saturn'),
            ('Rahu', 'Mars'), ('Rahu', 'Saturn'), ('Rahu', 'Jupiter'), ('Ketu', 'Mars'), ('Ketu', 'Saturn'),
        ]
        for p1, p2 in pairs:
            a, b = planets.get(p1), planets.get(p2)
            if not a or not b:
                continue
            long1 = a.get('longitude', 0)
            long2 = b.get('longitude', 0)
            diff = abs((long1 - long2 + 180) % 360 - 180)
            if diff <= 1.0:
                results.append({
                    'name': f'Graha Yuddha ({p1}-{p2})',
                    'type': 'planetary_war',
                    'severity': 'critical',
                    'graha_yuddha': True,
                    'description': f'{p1} and {p2} within 1° (Graha Yuddha). High-intensity trigger for sudden shocks, leadership events, or market volatility.',
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
        
        mars_long = mars.get('longitude', 0)
        saturn_long = saturn.get('longitude', 0)
        diff = abs(mars_long - saturn_long)
        
        # Conjunction (within 10 degrees)
        if diff < 10 or diff > 350:
            return {
                'name': 'Sanghatta Yoga (War Indicator)',
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
                'name': 'Durbhiksha Yoga (Famine Indicator)',
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
           (abs(venus.get('longitude', 0) - rahu.get('longitude', 0)) < 15):
            return {
                'name': 'Mahargha Yoga (Inflation Indicator)',
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
        
        uranus_long = uranus.get('longitude', 0)
        pluto_long = pluto.get('longitude', 0)
        diff = abs(uranus_long - pluto_long) % 360
        
        # Square (90°) or Opposition (180°)
        if (85 < diff < 95) or (175 < diff < 185):
            return {
                'name': 'Parivartan Yoga (Revolution Indicator)',
                'type': 'transformation',
                'severity': 'high',
                'description': 'Uranus-Pluto hard aspect indicates revolutionary changes, regime shifts, or major social upheavals',
                'manifestations': ['Political Revolution', 'Technological Disruption', 'Social Movements']
            }
        
        return None
    
    def _check_commodity_impacts(self, chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sarvatobhadra Chakra: direct (planet in nakshatra) + Vedha (aspect to commodity nakshatra)."""
        impacts = []
        planets = chart_data.get('planets', {})
        malefics = ['Mars', 'Saturn', 'Rahu', 'Ketu']

        for planet_name in malefics:
            planet = planets.get(planet_name, {})
            if not planet:
                continue
            nakshatra = planet.get('nakshatra', {}).get('name', '') or self._nakshatra_from_longitude(planet.get('longitude', 0))
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
                        'impact': 'price_volatility',
                        'prediction': f"{planet_name} in {nakshatra} suggests volatility in {commodity} prices"
                    })
            # Vedha: 7th aspect in SBC = nakshatra (index + 14) mod 27
            vedha_index = (nak_index + 14) % 27
            vedha_nakshatra = NAKSHATRAS_ORDER[vedha_index]
            for commodity, nakshatras in self.commodity_nakshatras.items():
                if vedha_nakshatra in nakshatras:
                    impacts.append({
                        'commodity': commodity,
                        'planet': planet_name,
                        'nakshatra': nakshatra,
                        'vedha_nakshatra': vedha_nakshatra,
                        'impact_type': 'vedha',
                        'impact': 'price_affliction_by_aspect',
                        'prediction': f"{planet_name} in {nakshatra} aspects (Vedha) {vedha_nakshatra} → {commodity} afflicted"
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
            return "Stable period with no major mundane indicators"
        
        severity_count = sum(1 for y in yogas if y.get('severity') == 'high')
        
        if severity_count >= 2:
            return "Critical period: Multiple high-severity yogas indicate major global events"
        elif severity_count == 1:
            return "Significant period: Important events likely in indicated sectors"
        elif yogas:
            return "Moderate period: Some challenges in specific areas"
        else:
            return "Commodity volatility expected, but no major crisis indicators"
