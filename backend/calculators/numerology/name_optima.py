from typing import Dict, List, Any, Set
from .core import NumerologyCore

class NameOptima:
    """
    Advanced Name Analysis Engine.
    Handles 'System Clash' (Chaldean vs Pythagorean) and Name Corrections.
    """

    # Vowels for Soul Urge calculation
    VOWELS = {'A', 'E', 'I', 'O', 'U'}
    
    # "Royal Star" or Lucky Compound Numbers (Chaldean)
    # 19 (Sun), 23 (Royal Star of the Lion), 24 (Love/Money), 27 (Sceptre), 
    # 32 (Communication), 37 (Good Fortune), 41, 45, 46...
    LUCKY_COMPOUNDS = {1, 3, 5, 6, 10, 14, 15, 19, 21, 23, 24, 27, 32, 37, 41, 45, 46, 50}
    
    # Difficult/Karmic Compound Numbers
    # 12 (Sacrifice), 16 (Shattered Citadel), 18 (Conflict), 22 (Illusion), 
    # 26 (Disaster), 29 (Deception), 38 (Treachery)...
    DIFFICULT_COMPOUNDS = {12, 16, 18, 22, 26, 28, 29, 35, 38, 43, 44, 48}

    def __init__(self):
        self.core = NumerologyCore()

    def analyze_full_name(self, full_name: str, system: str = 'chaldean') -> Dict[str, Any]:
        """
        Breaks down a name into Expression, Soul Urge, and Personality.
        """
        clean_name = self.core._clean_text(full_name)
        
        # 1. Expression Number (Total Sum)
        expression_data = self.core.calculate_name_number(clean_name, system)
        
        # 2. Soul Urge (Vowels) & Personality (Consonants)
        vowel_sum = 0
        consonant_sum = 0
        
        lookup = self.core.chaldean_lookup if system == 'chaldean' else self.core.pythagorean_lookup
        
        for char in clean_name:
            val = lookup.get(char, 0)
            if char in self.VOWELS:
                vowel_sum += val
            else:
                consonant_sum += val
                
        # Reduce them
        soul_urge = self.core.reduce_to_single(vowel_sum)
        personality = self.core.reduce_to_single(consonant_sum)
        
        return {
            "full_name": full_name,
            "system": system,
            "expression": {
                "number": expression_data['single_number'],
                "compound": expression_data['compound_number'],
                "is_master": expression_data['is_master']
            },
            "soul_urge": {
                "number": soul_urge,
                "compound": vowel_sum
            },
            "personality": {
                "number": personality,
                "compound": consonant_sum
            },
            "verdict": self._get_compound_verdict(expression_data['compound_number'])
        }

    def compare_systems(self, full_name: str) -> Dict[str, Any]:
        """
        Runs the 'System Clash' analysis. 
        Compares Chaldean vs Pythagorean results to find alignment or conflict.
        """
        chaldean = self.analyze_full_name(full_name, 'chaldean')
        pythagorean = self.analyze_full_name(full_name, 'pythagorean')
        
        # Check for Alignment
        aligned = chaldean['expression']['number'] == pythagorean['expression']['number']
        
        return {
            "chaldean_summary": chaldean['expression'],
            "pythagorean_summary": pythagorean['expression'],
            "status": "Aligned" if aligned else "Conflicted",
            "analysis": self._generate_comparison_text(chaldean, pythagorean)
        }

    def suggest_corrections(self, full_name: str, target_vibe: str = 'wealth') -> List[Dict[str, Any]]:
        """
        The 'Name Fixer' Engine.
        Tries variations (adding/doubling letters) to hit Lucky Compound Numbers.
        
        Args:
            full_name: "Tarun Yadav"
            target_vibe: 'wealth', 'power', 'peace' (Future implementation for specific filtering)
        """
        base_name = self.core._clean_text(full_name)
        variations = []
        seen = set()
        
        # Strategy 1: Double a letter (e.g., Tarun -> Tarrun)
        for i in range(len(base_name)):
            # Try doubling character at i
            new_name = base_name[:i] + base_name[i] + base_name[i:]
            self._check_and_add_variation(new_name, variations, seen)
            
            # Try adding an 'A' (common Indian remedy)
            new_name_a = base_name[:i] + 'A' + base_name[i:]
            self._check_and_add_variation(new_name_a, variations, seen)

            # Try adding an 'E'
            new_name_e = base_name[:i] + 'E' + base_name[i:]
            self._check_and_add_variation(new_name_e, variations, seen)
            
        # Sort by "Luckiness" (Compound number magnitude usually)
        variations.sort(key=lambda x: x['score'], reverse=True)
        
        return variations[:5]  # Return top 5 suggestions

    def _check_and_add_variation(self, name_variation: str, variations_list: List, seen_set: Set):
        """Helper to validate if a generated name is 'Lucky'."""
        if name_variation in seen_set:
            return
            
        # We generally use Chaldean for corrections as it's vibration-based
        result = self.analyze_full_name(name_variation, 'chaldean')
        compound = result['expression']['compound']
        
        if compound in self.LUCKY_COMPOUNDS:
            seen_set.add(name_variation)
            variations_list.append({
                "original": name_variation, # Cleaned uppercase
                "compound": compound,
                "single": result['expression']['number'],
                "verdict": self._get_compound_verdict(compound),
                "score": compound # Higher compound often implies stronger vibration
            })

    def _get_compound_verdict(self, compound: int) -> dict:
        """Returns detailed verdict for the compound number."""
        if compound == 18:
            return {
                "status": "Challenging",
                "title": "Conflict & Materialism",
                "reason": "1 (Sun) and 8 (Saturn) are enemies in Vedic Astrology. This creates internal conflict between your soul (1) and your karma (8), often leading to health issues or bitter family quarrels."
            }
        if compound == 23:
            return {
                "status": "Lucky",
                "title": "The Royal Star of the Lion",
                "reason": "This is a promise of success, help from superiors, and protection in high places."
            }
        if compound == 16:
            return {
                "status": "Challenging",
                "title": "The Shattered Citadel",
                "reason": "Represents sudden falls from grace and unexpected losses. Requires careful planning."
            }
        if compound == 19:
            return {
                "status": "Lucky",
                "title": "The Prince of Heaven",
                "reason": "Brings success, honor, and recognition. A highly favorable number for achievement."
            }
        
        if compound in self.LUCKY_COMPOUNDS:
            return {"status": "Lucky", "title": "Auspicious Vibration", "reason": "This number brings positive energy and opportunities."}
        if compound in self.DIFFICULT_COMPOUNDS:
            return {"status": "Challenging", "title": "Karmic Debt", "reason": "This number requires extra effort and learning from past mistakes."}
            
        return {"status": "Neutral", "title": "General Influence", "reason": "A standard vibration without extreme peaks or valleys."}

    def _generate_comparison_text(self, ch: Dict, py: Dict) -> str:
        c_num = ch['expression']['number']
        p_num = py['expression']['number']
        
        if c_num == p_num:
            return f"You have a unified vibration of {c_num}. Your path is clear and consistent."
        else:
            return (f"System Clash! Your name vibrates as {c_num} (Ancient) but {p_num} (Modern). "
                    f"You may feel a conflict between your inner destiny ({c_num}) and how the modern world sees you ({p_num}).")