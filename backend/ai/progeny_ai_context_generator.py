import sys
import os
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.base_ai_context_generator import BaseAIContextGenerator
from calculators.progeny_analyzer import ProgenyAnalyzer

class ProgenyAIContextGenerator(BaseAIContextGenerator):
    """Context generator specifically for Progeny/Childbirth analysis"""
    
    def build_progeny_context(self, birth_data: Dict) -> Dict[str, Any]:
        # 1. Get Base Context (Planets, D1, Basic details)
        base_context = self.build_base_context(birth_data)
        
        # 2. Get Chart Data from cache
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        
        # 3. Run Progeny Analyzer
        analyzer = ProgenyAnalyzer(chart_data, birth_data)
        progeny_data = analyzer.analyze_progeny()
        
        # 4. Construct AI Context
        context = {
            "subject_gender": birth_data.get('gender', 'female'),
            "progeny_analysis": progeny_data,
            "d1_chart": base_context.get('d1_chart'),
            "current_dashas": base_context.get('current_dashas'),
            
            # Add specific notes for the AI
            "interpretative_guidelines": {
                "sphuta_rule": "If Strength is 'Strong', biological fertility is good. If 'Moderate', suggest health checks.",
                "d7_rule": "Jupiter in D7 Lagna/5th is the best indicator. Saturn/Rahu in D7 5th indicates delay.",
                "timing_rule": "Predict childbirth when Dasha Lord is connected to: " + ", ".join(progeny_data['timing_indicators'])
            }
        }
        
        return context