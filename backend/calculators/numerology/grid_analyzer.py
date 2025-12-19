from collections import Counter
from typing import Dict, List, Any

class GridAnalyzer:
    """
    Analyzes the Lo Shu Grid (Magic Square) and Vedic Grid patterns.
    Identifies Arrows of Strength/Weakness and Missing Numbers.
    """

    # ---------------------------------------------------------
    # 1. GRID DEFINITIONS
    # ---------------------------------------------------------
    
    # The Standard Lo Shu positions (3x3 Grid)
    # 4  9  2
    # 3  5  7
    # 8  1  6
    LO_SHU_POSITIONS = {
        4: (0, 0), 9: (0, 1), 2: (0, 2),
        3: (1, 0), 5: (1, 1), 7: (1, 2),
        8: (2, 0), 1: (2, 1), 6: (2, 2)
    }

    # "Arrows" (Yogas) - Patterns of 3 numbers
    ARROWS = {
        # --- PLANES OF SUCCESS (Rows) ---
        "Mental Plane": {"nums": {4, 9, 2}, "desc": "Excellent memory and intellectual power"},
        "Emotional Plane": {"nums": {3, 5, 7}, "desc": "High emotional balance and spirituality"},
        "Practical Plane": {"nums": {8, 1, 6}, "desc": "Material success and grounding"},

        # --- ARROWS OF STRENGTH (Columns) ---
        "Thought Arrow": {"nums": {4, 3, 8}, "desc": "Strong planning and strategic thinking"},
        "Willpower Arrow": {"nums": {9, 5, 1}, "desc": "Unstoppable determination and execution"},
        "Action Arrow": {"nums": {2, 7, 6}, "desc": "Physical energy and sportsmanship"},

        # --- DIAGONAL ARROWS ---
        "Golden Arrow (Determination)": {"nums": {8, 5, 2}, "desc": "The luckiest arrow for real estate and wealth"},
        "Arrow of Skepticism": {"nums": {4, 5, 6}, "desc": "Suspicious nature but anxiety-prone"}
    }

    def generate_grid(self, dob_str: str) -> Dict[str, Any]:
        """
        Generates the full Grid Report from a DOB string.
        
        Args:
            dob_str: "YYYY-MM-DD" (e.g., "1980-04-02")
        """
        # 1. Parse Digits
        # Remove hyphens and convert to list of integers
        clean_dob = dob_str.replace("-", "")
        digits = [int(d) for d in clean_dob if d.isdigit()]
        
        # 2. Count Frequencies (The Grid)
        # {1: 1, 9: 1, 8: 1, 0: 2...}
        grid_counts = Counter(digits)
        
        # Filter out 0 (Numerology typically ignores 0 in the grid itself)
        if 0 in grid_counts:
            del grid_counts[0]

        # 3. Analyze Patterns
        arrows_present = self._check_arrows(grid_counts)
        missing_numbers = self._check_missing(grid_counts)
        repetitive_numbers = self._check_repetitive(grid_counts)

        return {
            "grid_counts": dict(grid_counts),  # Raw data for frontend visualization
            "arrows_of_strength": arrows_present,
            "missing_numbers": missing_numbers,
            "repetitive_numbers": repetitive_numbers
        }

    def _check_arrows(self, grid: Counter) -> List[Dict[str, str]]:
        """Identifies which 3-number arrows are complete."""
        present_arrows = []
        grid_keys = set(grid.keys())

        for name, data in self.ARROWS.items():
            required_nums = data["nums"]
            # Check if all numbers in the arrow exist in the user's grid
            if required_nums.issubset(grid_keys):
                present_arrows.append({
                    "name": name,
                    "type": "Strength",
                    "description": data["desc"]
                })
            # Advanced: Check for "Arrow of Weakness" (if NONE of the numbers exist)
            elif required_nums.isdisjoint(grid_keys):
                present_arrows.append({
                    "name": f"Missing {name}",
                    "type": "Weakness",
                    "description": f"Lack of {data['desc'].lower()}"
                })
        
        return present_arrows

    def _check_missing(self, grid: Counter) -> List[Dict[str, str]]:
        """Identifies numbers 1-9 that are completely absent."""
        missing = []
        # Enhanced interpretations with Planetary Associations
        interpretations = {
            1: {"planet": "Sun", "energy": "Communication", "lesson": "Difficulty initiating projects or lack of confidence"},
            2: {"planet": "Moon", "energy": "Sensitivity", "lesson": "Impatience with details or lack of intuition"},
            3: {"planet": "Jupiter", "energy": "Imagination", "lesson": "Difficulty expressing creativity or lack of focus"},
            4: {"planet": "Rahu", "energy": "Discipline", "lesson": "Lack of order, unconventional thinking needed"},
            5: {"planet": "Mercury", "energy": "Balance", "lesson": "Resistance to change or difficulty communicating"},
            6: {"planet": "Venus", "energy": "Luxury/Home", "lesson": "Lack of family responsibility or material comfort struggles"},
            7: {"planet": "Ketu", "energy": "Spirituality", "lesson": "Disappointment in trust or lack of spiritual faith"},
            8: {"planet": "Saturn", "energy": "Money/Law", "lesson": "Poor money management or lack of financial motivation"},
            9: {"planet": "Mars", "energy": "Humanity", "lesson": "Lack of ambition or care for others"}
        }

        for num in range(1, 10):
            if num not in grid:
                data = interpretations.get(num, {})
                missing.append({
                    "number": num,
                    "planet": data.get("planet"),
                    "missing_energy": data.get("energy"),
                    "lesson": data.get("lesson")
                })
        
        return missing

    def _check_repetitive(self, grid: Counter) -> List[Dict[str, str]]:
        """
        Analyzes numbers that appear too frequently (Hyper-active).
        Usually, 1-2 occurrences are balanced. 3+ is excessive.
        """
        repetitive = []
        
        # Simplified Logic for Excessive Numbers
        for num, count in grid.items():
            if count >= 3:
                desc = self._get_repetition_meaning(num, count)
                repetitive.append({
                    "number": num,
                    "count": count,
                    "meaning": desc
                })
        
        return repetitive

    def _get_repetition_meaning(self, num: int, count: int) -> str:
        """Returns the specific meaning of an over-abundant number."""
        # This can be expanded into a full database later
        meanings = {
            1: "Aggressive, dominating, or difficulty expressing true feelings",
            2: "Over-sensitive, moody, or psychic vulnerability",
            3: "Over-imaginative to the point of hallucination or scattered focus",
            4: "Stubborn, workaholic, or rigid thinking",
            5: "Impulsive, restless, or prone to addictions",
            6: "Over-protective, anxiety about family, or controlling",
            7: "Depressive, withdrawn, or overly skeptical",
            8: "Materialistic, ruthless, or stress-prone",
            9: "Idealistic to a fault, impractical, or disconnected from reality"
        }
        return meanings.get(num, "Excessive energy in this vibration")