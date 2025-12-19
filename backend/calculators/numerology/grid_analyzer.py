from collections import Counter
from typing import Dict, List, Any

class GridAnalyzer:
    """
    Analyzes the Lo Shu Grid and Vedic Grid patterns.
    Now includes Planetary and Elemental context for missing numbers.
    """

    ARROWS = {
        "Mental Plane": {"nums": {4, 9, 2}, "desc": "Excellent memory and intellectual power"},
        "Emotional Plane": {"nums": {3, 5, 7}, "desc": "High emotional balance and spirituality"},
        "Practical Plane": {"nums": {8, 1, 6}, "desc": "Material success and grounding"},
        "Thought Arrow": {"nums": {4, 3, 8}, "desc": "Strong planning and strategic thinking"},
        "Willpower Arrow": {"nums": {9, 5, 1}, "desc": "Unstoppable determination and execution"},
        "Action Arrow": {"nums": {2, 7, 6}, "desc": "Physical energy and sportsmanship"},
        "Golden Arrow": {"nums": {8, 5, 2}, "desc": "The luckiest arrow for real estate and wealth"},
        "Arrow of Skepticism": {"nums": {4, 5, 6}, "desc": "Suspicious nature but anxiety-prone"}
    }

    def generate_grid(self, dob_str: str) -> Dict[str, Any]:
        clean_dob = dob_str.replace("-", "")
        digits = [int(d) for d in clean_dob if d.isdigit()]
        grid_counts = Counter(digits)
        if 0 in grid_counts: del grid_counts[0]

        return {
            "grid_counts": dict(grid_counts),
            "arrows_of_strength": self._check_arrows(grid_counts),
            "missing_numbers": self._check_missing(grid_counts),
            "repetitive_numbers": self._check_repetitive(grid_counts)
        }

    def _check_arrows(self, grid: Counter) -> List[Dict[str, str]]:
        present_arrows = []
        grid_keys = set(grid.keys())

        for name, data in self.ARROWS.items():
            required_nums = data["nums"]
            if required_nums.issubset(grid_keys):
                present_arrows.append({"name": name, "type": "Strength", "description": data["desc"]})
            elif required_nums.isdisjoint(grid_keys):
                # Friendly re-write for "Weakness"
                friendly_name = name.replace("Arrow of ", "") + " Void"
                present_arrows.append({
                    "name": friendly_name, 
                    "type": "Weakness", 
                    "description": f"Focus on developing {friendly_name.lower()} qualities."
                })
        return present_arrows

    def _check_missing(self, grid: Counter) -> List[Dict[str, str]]:
        missing = []
        # Enhanced interpretations with Planetary Associations
        interpretations = {
            1: {"planet": "Sun", "energy": "Communication", "advice": "Work on building self-confidence and expressing your needs clearly."},
            2: {"planet": "Moon", "energy": "Intuition", "advice": "Trust your gut feelings more. Don't ignore your sensitive side."},
            3: {"planet": "Jupiter", "energy": "Imagination", "advice": "Engage in creative hobbies to unlock your hidden potential."},
            4: {"planet": "Rahu", "energy": "Discipline", "advice": "Create a daily routine. Order brings you peace."},
            5: {"planet": "Mercury", "energy": "Balance", "advice": "Try to be more flexible. Set clear goals to avoid restlessness."},
            6: {"planet": "Venus", "energy": "Luxury & Family", "advice": " spend more quality time with family. Appreciate beauty around you."},
            7: {"planet": "Ketu", "energy": "Faith", "advice": "Develop a spiritual practice or meditation routine."},
            8: {"planet": "Saturn", "energy": "Money Mgmt", "advice": "Be careful with finances. Learn to budget and plan for the long term."},
            9: {"planet": "Mars", "energy": "Ambition", "advice": "Finish what you start. Don't leave projects halfway."}
        }

        for num in range(1, 10):
            if num not in grid:
                data = interpretations.get(num, {})
                missing.append({
                    "number": num,
                    "planet": data.get("planet"),
                    "missing_energy": data.get("energy"),
                    "lesson": data.get("advice")
                })
        return missing

    def _check_repetitive(self, grid: Counter) -> List[Dict[str, str]]:
        repetitive = []
        meanings = {
            1: "You may talk more than you listen.",
            9: "You may be overly idealistic or critical."
        }
        for num, count in grid.items():
            if count >= 3:
                repetitive.append({
                    "number": num,
                    "count": count,
                    "meaning": meanings.get(num, "High intensity in this area.")
                })
        return repetitive