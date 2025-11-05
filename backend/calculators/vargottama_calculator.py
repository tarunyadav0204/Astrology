"""
Vargottama Calculator
Planets in same sign across multiple divisional charts (D1, D9, D10, etc.)
Based on classical Vedic astrology principles
"""

class VargottamaCalculator:
    """Calculate Vargottama positions - planets in same sign across divisional charts"""
    
    def __init__(self, chart_data, divisional_charts):
        self.chart_data = chart_data
        self.divisional_charts = divisional_charts
        self.planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
    def calculate_vargottama_positions(self):
        """Calculate all Vargottama positions"""
        vargottama_results = {}
        
        for planet in self.planets:
            vargottama_results[planet] = self._analyze_planet_vargottama(planet)
        
        return vargottama_results
    
    def _analyze_planet_vargottama(self, planet):
        """Analyze Vargottama status for a specific planet"""
        d1_position = self.chart_data.get(planet, 0)
        d1_sign = int(d1_position / 30)
        
        vargottama_charts = ['D1']  # D1 is always included
        chart_positions = {'D1': {'degree': d1_position, 'sign': d1_sign}}
        
        # Check each divisional chart
        for chart_name, chart_data in self.divisional_charts.items():
            if chart_data and planet in chart_data:
                div_position = chart_data[planet]
                div_sign = int(div_position / 30)
                
                chart_positions[chart_name] = {
                    'degree': div_position,
                    'sign': div_sign
                }
                
                # If same sign as D1, it's Vargottama
                if div_sign == d1_sign:
                    vargottama_charts.append(chart_name)
        
        # Determine Vargottama strength
        vargottama_strength = self._calculate_vargottama_strength(vargottama_charts)
        
        return {
            'is_vargottama': len(vargottama_charts) > 1,
            'vargottama_charts': vargottama_charts,
            'total_charts': len(vargottama_charts),
            'strength_level': vargottama_strength,
            'chart_positions': chart_positions,
            'effects': self._get_vargottama_effects(planet, vargottama_strength, len(vargottama_charts))
        }
    
    def _calculate_vargottama_strength(self, vargottama_charts):
        """Calculate strength based on number and importance of charts"""
        chart_weights = {
            'D1': 3,    # Rashi - most important
            'D9': 3,    # Navamsa - equally important
            'D10': 2,   # Dasamsa - career
            'D12': 1,   # Dwadasamsa - parents
            'D16': 2,   # Shodasamsa - vehicles
            'D20': 1,   # Vimsamsa - spiritual
            'D24': 1,   # Chaturvimsamsa - learning
            'D27': 1,   # Nakshatramsa - strengths/weaknesses
            'D30': 1,   # Trimsamsa - evils
            'D60': 2    # Shashtiamsa - general
        }
        
        total_weight = sum(chart_weights.get(chart, 1) for chart in vargottama_charts)
        
        if total_weight >= 8:
            return 'Exceptional'
        elif total_weight >= 6:
            return 'Very Strong'
        elif total_weight >= 4:
            return 'Strong'
        elif total_weight >= 2:
            return 'Moderate'
        else:
            return 'Weak'
    
    def _get_vargottama_effects(self, planet, strength, chart_count):
        """Get effects of Vargottama position"""
        base_effects = {
            'general': f"{planet} gains exceptional strength and consistency in results",
            'positive': f"Enhanced {planet} significations, stable and powerful results",
            'timing': f"{planet} periods (dasha/antardasha) will be particularly significant"
        }
        
        strength_modifiers = {
            'Exceptional': "Extraordinary power and influence, life-changing results",
            'Very Strong': "Very powerful results, major positive influence",
            'Strong': "Strong positive results, reliable outcomes",
            'Moderate': "Good results with some consistency",
            'Weak': "Mild positive influence"
        }
        
        return {
            **base_effects,
            'strength_effect': strength_modifiers.get(strength, 'Mild positive influence'),
            'chart_count_note': f"Vargottama in {chart_count} charts increases reliability of results"
        }
    
    def get_vargottama_summary(self):
        """Get summary of all Vargottama planets"""
        vargottama_results = self.calculate_vargottama_positions()
        
        vargottama_planets = []
        for planet, result in vargottama_results.items():
            if result['is_vargottama']:
                vargottama_planets.append({
                    'planet': planet,
                    'charts': result['vargottama_charts'],
                    'strength': result['strength_level'],
                    'chart_count': result['total_charts']
                })
        
        # Sort by strength and chart count
        strength_order = {'Exceptional': 5, 'Very Strong': 4, 'Strong': 3, 'Moderate': 2, 'Weak': 1}
        vargottama_planets.sort(key=lambda x: (strength_order.get(x['strength'], 0), x['chart_count']), reverse=True)
        
        return {
            'total_vargottama_planets': len(vargottama_planets),
            'vargottama_planets': vargottama_planets,
            'detailed_results': vargottama_results,
            'summary': f"{len(vargottama_planets)} planet(s) are Vargottama, providing exceptional strength" if vargottama_planets else "No Vargottama planets found"
        }
    
    def get_strongest_vargottama(self):
        """Get the strongest Vargottama planet"""
        summary = self.get_vargottama_summary()
        
        if summary['vargottama_planets']:
            strongest = summary['vargottama_planets'][0]
            return {
                'planet': strongest['planet'],
                'strength': strongest['strength'],
                'charts': strongest['charts'],
                'significance': f"Most powerful Vargottama planet with {strongest['strength']} strength across {strongest['chart_count']} charts"
            }
        
        return None