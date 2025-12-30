"""
Comprehensive Calculator that combines all existing calculators
Provides a unified interface to all calculation modules
"""

from .chart_calculator import ChartCalculator
from .transit_calculator import TransitCalculator
from .panchang_calculator import PanchangCalculator
from .friendship_calculator import FriendshipCalculator
from .divisional_chart_calculator import DivisionalChartCalculator
from .shadbala_calculator import ShadbalaCalculator
from .chara_karaka_calculator import CharaKarakaCalculator
from .nakshatra_calculator import NakshatraCalculator
from .yoga_calculator import YogaCalculator
from .planetary_dignities_calculator import PlanetaryDignitiesCalculator
from .argala_calculator import ArgalaCalculator
from .profession_calculator import ProfessionCalculator
from utils.timezone_service import get_timezone_from_coordinates
# Import these only when needed to avoid import errors
# from ..shared.dasha_calculator import DashaCalculator
# from ..calculators.ashtakavarga import AshtakavargaCalculator
# from ..event_prediction.universal_house_analyzer import UniversalHouseAnalyzer
# from ..horoscope.utils.planetary_calculator import PlanetaryCalculator

class ComprehensiveCalculator:
    """Unified calculator combining all existing calculation modules"""
    
    def __init__(self, birth_data, chart_data=None):
        self.birth_data = birth_data
        self.chart_data = chart_data or {}
        
        # Auto-detect timezone if not provided
        if not hasattr(birth_data, 'timezone') or not birth_data.timezone:
            if hasattr(birth_data, 'latitude') and hasattr(birth_data, 'longitude'):
                birth_data.timezone = get_timezone_from_coordinates(birth_data.latitude, birth_data.longitude)
        
        # Initialize individual calculators with chart_data only
        self.shadbala_calc = ShadbalaCalculator(chart_data)
        self.chara_karaka_calc = CharaKarakaCalculator(chart_data)
        self.planetary_dignities_calc = PlanetaryDignitiesCalculator(chart_data)
        self.profession_calc = ProfessionCalculator(chart_data)
        # self.dasha_calc = DashaCalculator()
        
        # Initialize calculators that need chart data
        # if chart_data:
        #     self.ashtakavarga_calc = AshtakavargaCalculator(birth_data, chart_data)
        #     self.house_analyzer = UniversalHouseAnalyzer(birth_data, chart_data)
        
        # self.planetary_calc = PlanetaryCalculator()
    
    def calculate_birth_chart(self, node_type='mean'):
        """Calculate complete birth chart"""
        return self.chart_calc.calculate_chart(self.birth_data, node_type)
    
    def calculate_transits(self, transit_date):
        """Calculate transit positions"""
        return self.transit_calc.calculate_transits(self.birth_data, transit_date)
    
    def calculate_panchang(self, date):
        """Calculate panchang for date"""
        return self.panchang_calc.calculate_panchang(date)
    
    def calculate_friendship_matrix(self):
        """Calculate planetary friendship relationships"""
        return self.friendship_calc.calculate_friendship(self.birth_data)
    
    def calculate_divisional_chart(self, division_number):
        """Calculate divisional chart"""
        return self.divisional_calc.calculate_divisional_chart(division_number)
    
    def calculate_current_dashas(self, current_date=None):
        """Calculate current dasha periods"""
        # Simplified dasha calculation for now
        return {
            'current_mahadasha': {
                'planet': 'Sun',
                'start': '2020-01-01',
                'end': '2026-01-01'
            }
        }
    
    def calculate_shadbala(self):
        """Calculate six-fold planetary strength"""
        return self.shadbala_calc.calculate_shadbala()
    
    def calculate_chara_karakas(self):
        """Calculate Chara Karakas (variable significators)"""
        return self.chara_karaka_calc.calculate_chara_karakas()
    
    def calculate_nakshatra_positions(self):
        """Calculate nakshatra positions for all planets"""
        return self.nakshatra_calc.calculate_nakshatra_positions()
    
    def calculate_yogas(self):
        """Calculate various Vedic yogas"""
        return self.yoga_calc.calculate_all_yogas()
    
    def calculate_planetary_dignities(self):
        """Calculate planetary dignities and states"""
        return self.planetary_dignities_calc.calculate_planetary_dignities()
    
    def calculate_argala_analysis(self):
        """Calculate Argala (planetary interventions)"""
        return self.argala_calc.calculate_argala_analysis()
    
    def calculate_professional_analysis(self):
        """Calculate comprehensive professional analysis"""
        return self.profession_calc.calculate_professional_analysis()
    
    def get_career_focused_analysis(self):
        """Get comprehensive career-focused analysis"""
        return {
            'professional_analysis': self.calculate_professional_analysis(),
            'planetary_dignities': self.calculate_planetary_dignities(),
            'chara_karakas': self.calculate_chara_karakas()
        }
    
    def calculate_ashtakavarga(self):
        """Calculate Ashtakavarga if chart data available"""
        if hasattr(self, 'ashtakavarga_calc'):
            return self.ashtakavarga_calc.calculate_sarvashtakavarga()
        return None
    
    def analyze_all_houses(self):
        """Analyze all 12 houses if chart data available"""
        if hasattr(self, 'house_analyzer'):
            return self.house_analyzer.analyze_all_houses()
        return None
    
    def analyze_single_house(self, house_number):
        """Analyze specific house if chart data available"""
        if hasattr(self, 'house_analyzer'):
            return self.house_analyzer.analyze_house(house_number)
        return None
    
    def get_comprehensive_analysis(self):
        """Get complete astrological analysis"""
        analysis = {
            'birth_chart': self.calculate_birth_chart(),
            'birth_panchang': self.calculate_panchang(self.birth_data.date),
            'friendship_matrix': self.calculate_friendship_matrix(),
            'current_dashas': self.calculate_current_dashas(),
            'navamsa_chart': self.calculate_divisional_chart(9),
            'dasamsa_chart': self.calculate_divisional_chart(10),
            'shadbala': self.calculate_shadbala(),
            'chara_karakas': self.calculate_chara_karakas(),
            'nakshatra_positions': self.calculate_nakshatra_positions(),
            'yogas': self.calculate_yogas(),
            'planetary_dignities': self.calculate_planetary_dignities(),
            'argala_analysis': self.calculate_argala_analysis(),
            'professional_analysis': self.calculate_professional_analysis()
        }
        
        # Add chart-dependent analyses if available
        if hasattr(self, 'ashtakavarga_calc'):
            analysis['ashtakavarga'] = self.calculate_ashtakavarga()
        
        if hasattr(self, 'house_analyzer'):
            analysis['house_analysis'] = self.analyze_all_houses()
        
        return analysis
    
    def get_available_calculations(self):
        """Get list of available calculations"""
        calculations = [
            'birth_chart', 'transits', 'panchang', 'friendship_matrix',
            'divisional_charts', 'current_dashas', 'shadbala', 'chara_karakas',
            'nakshatra_positions', 'yogas', 'planetary_dignities', 'argala_analysis',
            'professional_analysis', 'career_focused_analysis'
        ]
        
        if hasattr(self, 'ashtakavarga_calc'):
            calculations.append('ashtakavarga')
        
        if hasattr(self, 'house_analyzer'):
            calculations.append('house_analysis')
        
        return calculations