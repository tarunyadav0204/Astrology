"""
Backward compatibility wrapper for classical_shadbala
This file provides the ShadbalaCalculator class that wraps the classical implementation
"""
from .classical_shadbala import calculate_classical_shadbala
from .divisional_chart_calculator import DivisionalChartCalculator

class ShadbalaCalculator:
    """Wrapper class for backward compatibility with classical_shadbala"""
    
    def __init__(self, chart_data, birth_data=None):
        self.chart_data = chart_data
        self.birth_data = birth_data or {}
        
    def calculate_shadbala(self):
        """Calculate shadbala using classical implementation"""
        chart_data = self.chart_data
        if not chart_data.get('divisions'):
            chart_data = dict(chart_data)
            chart_data['divisions'] = DivisionalChartCalculator(
                chart_data
            ).calculate_all_divisional_charts()
        return calculate_classical_shadbala(self.birth_data, chart_data)
