"""Backward-compatible wrapper around the v2 kundli matching engine."""
from typing import Dict, Any

from marriage_matching import KundliMatchingEngine

class CompatibilityAnalyzer:
    def __init__(self):
        self.engine = KundliMatchingEngine()
    
    def analyze_compatibility(self, boy_chart: Dict, girl_chart: Dict, boy_birth: Dict, girl_birth: Dict) -> Dict[str, Any]:
        """Return the legacy-compatible payload while using the new engine underneath."""
        full = self.engine.analyze(boy_chart, girl_chart, boy_birth, girl_birth)
        legacy = dict(full["legacy"])
        legacy["api_version"] = "kundli_matching_v2"
        legacy["rule_profile"] = full.get("rule_profile")
        legacy["profiles"] = full.get("profiles")
        legacy["relationship_indicators"] = full.get("relationship_indicators")
        legacy["timing_overlay"] = full.get("timing_overlay")
        legacy["evidence_summary"] = full.get("evidence_summary")
        legacy["evidence_objects"] = full.get("evidence_objects")
        legacy["recommendation"]["timing_note"] = full.get("recommendation", {}).get("timing_note")
        legacy["engine"] = full
        return legacy
