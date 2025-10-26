"""Timing calculator extracted from UniversalHouseAnalyzer"""

from .base_calculator import BaseCalculator

class TimingCalculator(BaseCalculator):
    """Calculate timing indicators for house events"""
    
    def get_timing_indicators(self, house_num):
        """Get timing indicators - extracted from UniversalHouseAnalyzer"""
        house_lord = self.get_sign_lord(self.chart_data['houses'][house_num - 1]['sign'])
        
        return {
            'primary_dasha': f"{house_lord} Mahadasha/Antardasha periods",
            'transit_triggers': f"When benefics transit through house {house_num} or aspect it",
            'annual_indicators': f"During {house_lord}'s favorable transit periods"
        }
    
    def get_favorable_periods(self, house_num):
        """Get favorable periods - extracted from UniversalHouseAnalyzer"""
        house_lord = self.get_sign_lord(self.chart_data['houses'][house_num - 1]['sign'])
        
        return [
            f"{house_lord} Mahadasha",
            f"Jupiter transit through house {house_num}",
            f"Benefic planets transiting house {house_num}"
        ]