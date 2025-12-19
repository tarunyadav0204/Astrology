from typing import Dict, List, Any, Set
from .core import NumerologyCore

class NameOptima:
    """
    Advanced Name Analysis Engine.
    Handles 'System Clash' and returns rich verdicts.
    """
    
    LUCKY_COMPOUNDS = {1, 3, 5, 6, 10, 14, 15, 19, 21, 23, 24, 27, 32, 37, 41, 45, 46, 50}
    DIFFICULT_COMPOUNDS = {12, 16, 18, 22, 26, 28, 29, 35, 38, 43, 44, 48}
    VOWELS = {'A', 'E', 'I', 'O', 'U'}

    def __init__(self):
        self.core = NumerologyCore()

    def analyze_full_name(self, full_name: str, system: str = 'chaldean') -> Dict[str, Any]:
        clean_name = self.core._clean_text(full_name)
        expression_data = self.core.calculate_name_number(clean_name, system)
        
        # Calculate Soul Urge & Personality
        vowel_sum, consonant_sum = 0, 0
        lookup = self.core.chaldean_lookup if system == 'chaldean' else self.core.pythagorean_lookup
        
        for char in clean_name:
            val = lookup.get(char, 0)
            if char in self.VOWELS: vowel_sum += val
            else: consonant_sum += val
                
        return {
            "full_name": full_name,
            "system": system,
            "expression": {
                "number": expression_data['single_number'],
                "compound": expression_data['compound_number']
            },
            "soul_urge": {
                "number": self.core.reduce_to_single(vowel_sum),
                "compound": vowel_sum
            },
            "personality": {
                "number": self.core.reduce_to_single(consonant_sum),
                "compound": consonant_sum
            },
            # Rich verdict object instead of string
            "verdict": self._get_compound_verdict(expression_data['compound_number'])
        }

    def suggest_corrections(self, full_name: str) -> List[Dict[str, Any]]:
        """Brute-force lucky variations."""
        base_name = self.core._clean_text(full_name)
        variations = []
        seen = set()
        
        # Try simple additions
        for i in range(len(base_name) + 1):
            for char in ['A', 'E', 'I', 'S', 'R', 'N']: # Common lucky additions
                new_name = base_name[:i] + char + base_name[i:]
                if new_name not in seen:
                    self._check_and_add(new_name, variations, seen)
                    
        variations.sort(key=lambda x: x['score'], reverse=True)
        return variations[:5]

    def _check_and_add(self, name, variations, seen):
        res = self.analyze_full_name(name, 'chaldean')
        cmp = res['expression']['compound']
        if cmp in self.LUCKY_COMPOUNDS:
            seen.add(name)
            variations.append({
                "original": name,
                "compound": cmp,
                "verdict": self._get_compound_verdict(cmp),
                "score": cmp
            })

    def _get_compound_verdict(self, compound: int) -> dict:
        """Returns detailed object for UI rendering."""
        if compound in self.LUCKY_COMPOUNDS:
            if compound == 23:
                return {"title": "The Royal Star of the Lion", "status": "Lucky", "color": "green", "description": "A promise of success and help from superiors."}
            if compound == 24:
                return {"title": "Love & Abundance", "status": "Lucky", "color": "green", "description": "Associations with rank and wealth; support from women."}
            if compound == 19:
                return {"title": "The Prince of Heaven", "status": "Lucky", "color": "green", "description": "Success, honor, and happiness."}
            return {"title": "Auspicious Vibration", "status": "Lucky", "color": "green", "description": "A very fortunate number for future success."}
            
        if compound in self.DIFFICULT_COMPOUNDS:
            if compound == 18:
                return {"title": "Conflict & Materialism", "status": "Challenging", "color": "red", "description": "Indicates bitter quarrels and family dissension."}
            if compound == 16:
                return {"title": "The Shattered Citadel", "status": "Challenging", "color": "red", "description": "Sudden rise and sudden fall; beware of accidents."}
            return {"title": "Karmic Challenge", "status": "Challenging", "color": "orange", "description": "Requires great caution and prudence."}
            
        return {"title": "Neutral Influence", "status": "Neutral", "color": "gray", "description": "A balanced vibration without major peaks or troughs."}

    def compare_systems(self, full_name: str) -> Dict[str, Any]:
        chaldean = self.analyze_full_name(full_name, 'chaldean')
        pythagorean = self.analyze_full_name(full_name, 'pythagorean')
        
        return {
            "status": "Aligned" if chaldean['expression']['number'] == pythagorean['expression']['number'] else "Conflicted",
            "analysis": f"Chaldean ({chaldean['expression']['compound']}) vs Pythagorean ({pythagorean['expression']['compound']})."
        }