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
        current_dashas = base_context.get('current_dashas') or {}

        # 4. Construct AI Context
        context = {
            "subject_gender": birth_data.get('gender', 'female'),
            "analysis_focus": birth_data.get('analysis_focus', 'first_child'),
            "children_count": birth_data.get('children_count', 0),
            "progeny_analysis": progeny_data,
            "d1_chart": base_context.get('d1_chart'),
            "current_dashas": current_dashas,
            "current_timing_summary": self._summarize_current_dashas(current_dashas, progeny_data),
            "progeny_evidence": progeny_data.get('progeny_evidence', {}),
            
            # Add specific notes for the AI
            "interpretative_guidelines": {
                "sphuta_rule": "Treat fertility sphuta as a supportive polarity check, not a medical test.",
                "d7_rule": "Use D7 Lagna, 5th, 9th, and 2nd together. Jupiter/Venus/Moon support; Saturn/Rahu/Ketu in D7 5th can delay.",
                "timing_rule": "Use current dashas only when the lord connects to: " + ", ".join(progeny_data['timing_indicators']),
                "focus_rule": "If analysis_focus is parenting, do not predict conception timing. If next_child, focus only on the next child. If first_child, focus on the first-child promise and timing windows.",
                "safety_rule": "Do not present fertility as fate, medical diagnosis, or certainty."
            }
        }
        
        return context

    def _summarize_current_dashas(self, current_dashas: Dict, progeny_data: Dict[str, Any]) -> Dict[str, Any]:
        if not current_dashas:
            return {"available": False, "summary": "No current dasha data available."}

        def pick_label(node: Any) -> str:
            if isinstance(node, dict):
                return (
                    node.get("planet")
                    or node.get("lord")
                    or node.get("name")
                    or node.get("label")
                    or "Unknown"
                )
            return str(node) if node is not None else "Unknown"

        mahadasha = current_dashas.get("mahadasha", {})
        antardasha = current_dashas.get("antardasha", {})
        pratyantardasha = current_dashas.get("pratyantardasha", {})
        sookshma = current_dashas.get("sookshma", {})

        active_lords = [
            pick_label(mahadasha),
            pick_label(antardasha),
            pick_label(pratyantardasha),
            pick_label(sookshma),
        ]

        timing_indicators = set(progeny_data.get("timing_indicators", []))
        aligned = [lord for lord in active_lords if lord in timing_indicators]

        return {
            "available": True,
            "mahadasha": pick_label(mahadasha),
            "antardasha": pick_label(antardasha),
            "pratyantardasha": pick_label(pratyantardasha),
            "sookshma": pick_label(sookshma),
            "timing_alignment": "supportive" if aligned else "mixed",
            "matched_lords": aligned,
            "summary": (
                f"Current timing is {pick_label(mahadasha)} / {pick_label(antardasha)}"
                + (f" / {pick_label(pratyantardasha)}" if pick_label(pratyantardasha) != "Unknown" else "")
                + (f" / {pick_label(sookshma)}" if pick_label(sookshma) != "Unknown" else "")
            ),
        }
