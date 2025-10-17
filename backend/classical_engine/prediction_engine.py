"""
Classical Prediction Engine
Main orchestrator for comprehensive classical Vedic predictions
"""

from datetime import datetime
from typing import Dict, List, Any
from .core_analyzer import CoreClassicalAnalyzer
from .advanced_classical import AdvancedClassicalTechniques

class ClassicalPredictionEngine:
    def __init__(self, birth_data: Dict, current_date: datetime = None):
        self.birth_data = birth_data
        self.current_date = current_date or datetime.now()

        
        # Initialize analyzers
        self.core_analyzer = CoreClassicalAnalyzer(birth_data, current_date)
        self.advanced_techniques = AdvancedClassicalTechniques(birth_data)
        
        self.complete_analysis = {}
        self.debug_log = []
    
    def generate_comprehensive_prediction(self) -> Dict[str, Any]:
        """Generate complete classical prediction with full debugging"""
        
        self.debug_log.append("=== CLASSICAL PREDICTION ENGINE STARTED ===")
        self.debug_log.append(f"Birth Date: {self.birth_data.get('date')}")
        self.debug_log.append(f"Analysis Date: {self.current_date}")
        self.debug_log.append("")
        
        # Step 1: Core Classical Analysis (User's 7-step technique)
        self.debug_log.append("PHASE 1: CORE CLASSICAL ANALYSIS (7-STEP TECHNIQUE)")
        
        # Execute complete 7-step prediction
        core_prediction = self.core_analyzer.generate_complete_prediction()
        self.complete_analysis["core_prediction"] = core_prediction
        self.debug_log.append("✓ Complete 7-step classical prediction generated")
        self.debug_log.append("")
        
        # Step 2: Advanced Classical Techniques
        self.debug_log.append("PHASE 2: ADVANCED CLASSICAL TECHNIQUES")
        
        ashtakavarga = self.advanced_techniques.calculate_ashtakavarga_strength()
        self.complete_analysis["ashtakavarga"] = ashtakavarga
        self.debug_log.append("✓ Ashtakavarga Analysis completed")
        
        yogakaraka = self.advanced_techniques.analyze_yogakaraka_planets()
        self.complete_analysis["yogakaraka"] = yogakaraka
        self.debug_log.append("✓ Yogakaraka Analysis completed")
        
        planetary_war = self.advanced_techniques.analyze_planetary_war()
        self.complete_analysis["planetary_war"] = planetary_war
        self.debug_log.append("✓ Planetary War Analysis completed")
        
        argala = self.advanced_techniques.analyze_argala()
        self.complete_analysis["argala"] = argala
        self.debug_log.append("✓ Argala Analysis completed")
        
        temporal_friendship = self.advanced_techniques.analyze_temporal_friendship()
        self.complete_analysis["temporal_friendship"] = temporal_friendship
        self.debug_log.append("✓ Temporal Friendship Analysis completed")
        
        chara_karakas = self.advanced_techniques.analyze_chara_karakas()
        self.complete_analysis["chara_karakas"] = chara_karakas
        self.debug_log.append("✓ Chara Karaka Analysis completed")
        
        rashi_sandhi = self.advanced_techniques.analyze_rashi_sandhi()
        self.complete_analysis["rashi_sandhi"] = rashi_sandhi
        self.debug_log.append("✓ Rashi Sandhi Analysis completed")
        
        nakshatra_pada = self.advanced_techniques.analyze_nakshatra_pada()
        self.complete_analysis["nakshatra_pada"] = nakshatra_pada
        self.debug_log.append("✓ Nakshatra Pada Analysis completed")
        self.debug_log.append("")
        
        # Step 3: Synthesize Enhanced Prediction
        self.debug_log.append("PHASE 3: ENHANCED PREDICTION SYNTHESIS")
        
        enhanced_prediction = self._synthesize_enhanced_prediction()
        self.complete_analysis["enhanced_prediction"] = enhanced_prediction
        self.debug_log.append("✓ Enhanced Prediction synthesized")
        
        # Step 4: Generate Final Output
        final_result = self._generate_final_output()
        
        # Add core prediction details to final result
        final_result["core_7_step_analysis"] = core_prediction
        
        self.debug_log.append("")
        self.debug_log.append("=== CLASSICAL PREDICTION ENGINE COMPLETED ===")
        
        return final_result
    
    def _synthesize_enhanced_prediction(self) -> Dict[str, Any]:
        """Synthesize core prediction with advanced techniques"""
        core_pred = self.complete_analysis["core_prediction"]
        enhancement_factors = []
        
        # Add advanced technique enhancements
        if self.complete_analysis.get("yogakaraka", {}).get("primary_yogakaraka"):
            yk_planet = self.complete_analysis["yogakaraka"]["primary_yogakaraka"]["planet"]
            enhancement_factors.append(f"{yk_planet} as Yogakaraka provides strong support")
        
        if self.complete_analysis.get("ashtakavarga", {}).get("strongest_houses"):
            strong_houses = self.complete_analysis["ashtakavarga"]["strongest_houses"]
            enhancement_factors.append(f"Houses {strong_houses[:2]} have strong Ashtakavarga support")
        
        # Enhanced prediction text
        enhanced_text = core_pred["step5_prediction"]["prediction_text"]
        if enhancement_factors:
            enhanced_text += f" Additionally, {'. '.join(enhancement_factors[:2])}."
        
        return {
            "prediction_text": enhanced_text,
            "confidence": 0.8,  # Base confidence
            "enhancement_factors": enhancement_factors,
            "classical_strength": 0.7,  # Base strength
            "key_techniques_used": ["7-Step Classical Analysis", "Ashtakavarga", "Yogakaraka"]
        }
    
    def _generate_final_output(self) -> Dict[str, Any]:
        """Generate final structured output"""
        
        enhanced_pred = self.complete_analysis["enhanced_prediction"]
        
        return {
            "prediction": {
                "text": self.complete_analysis["core_prediction"]["step5_prediction"]["prediction_text"],
                "confidence": enhanced_pred["confidence"],
                "time_frame": "Current period",
                "classical_strength": enhanced_pred["classical_strength"],
                "dominant_themes": self.complete_analysis["core_prediction"]["step5_prediction"].get("dominant_themes", [])
            },
            "analysis_summary": {
                "active_dasha_planets": self.complete_analysis["core_prediction"]["step1_dasha_planets"],
                "activated_planets": self.complete_analysis["core_prediction"]["step2_activated_planets"],
                "activated_houses": self.complete_analysis["core_prediction"]["step3_activated_houses"],
                "overall_tendency": self.complete_analysis["core_prediction"]["step5_prediction"]["overall_tendency"],
                "yogakaraka_planet": self.complete_analysis["yogakaraka"]["primary_yogakaraka"]["planet"] if self.complete_analysis.get("yogakaraka", {}).get("primary_yogakaraka") else None,
                "atmakaraka": self.complete_analysis.get("chara_karakas", {}).get("chara_karakas", {}).get("Atmakaraka", {}).get("planet")
            },
            "detailed_analysis": self.complete_analysis,
            "debug_information": {
                "core_debug": self.core_analyzer.debug_info,
                "advanced_debug": self.advanced_techniques.debug_info,
                "execution_log": self.debug_log
            },
            "techniques_applied": [
                "Vimshottari Dasha System",
                "Transit Analysis",
                "House Activation Theory",
                "Shadbala Calculations",
                "Ashtakavarga System",
                "Yogakaraka Analysis",
                "Planetary War Detection",
                "Argala Analysis",
                "Temporal Friendship",
                "Chara Karaka System",
                "Rashi Sandhi Analysis",
                "Nakshatra Pada Analysis"
            ]
        }
    

    
    def get_debug_summary(self) -> Dict[str, Any]:
        """Get comprehensive debug summary for UI"""
        return {
            "execution_steps": len(self.debug_log),
            "techniques_count": 12,
            "analysis_phases": 3,
            "confidence_factors": self.complete_analysis.get("enhanced_prediction", {}).get("enhancement_factors", []),
            "classical_strength": self.complete_analysis.get("enhanced_prediction", {}).get("classical_strength", 0),
            "debug_log": self.debug_log,
            "detailed_breakdowns": {
                "core_analysis": self.core_analyzer.debug_info,
                "advanced_techniques": self.advanced_techniques.debug_info
            }
        }