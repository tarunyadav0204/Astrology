from datetime import datetime
from typing import Dict, Any
from .core import NumerologyCore

class TimeKeeper:
    """
    The Temporal Engine.
    Calculates dynamic cycles and provides "Narrative Synthesis" of the timeline.
    """

    def __init__(self):
        self.core = NumerologyCore()

    def get_current_cycles(self, dob_str: str, target_date: str = None) -> Dict[str, Any]:
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        # Parse Dates
        dob_year, dob_month, dob_day = map(int, dob_str.split('-'))
        curr_year, curr_month, curr_day = map(int, target_date.split('-'))

        # 1. Personal Year (PY)
        r_month = self.core.reduce_to_single(dob_month)
        r_day = self.core.reduce_to_single(dob_day)
        r_curr_year = self.core.reduce_to_single(curr_year)
        
        py_sum = r_month + r_day + r_curr_year
        personal_year = self.core.reduce_to_single(py_sum)

        # 2. Personal Month (PM)
        pm_sum = personal_year + curr_month
        personal_month = self.core.reduce_to_single(pm_sum)

        # 3. Personal Day (PD)
        pd_sum = personal_month + curr_day
        personal_day = self.core.reduce_to_single(pd_sum)

        # --- NEW: Narrative Synthesis ---
        synthesis = self._generate_synthesis(personal_year, personal_month, personal_day)
        
        # --- NEW: Calculation Logic (The "How") ---
        math_explanation = (
            f"Year: {dob_day}(Day) + {dob_month}(Month) + {curr_year}(Current Year) = {personal_year}. "
            f"Month: {personal_year}(Year) + {curr_month}(Month) = {personal_month}. "
            f"Day: {personal_month}(Month) + {curr_day}(Day) = {personal_day}."
        )

        return {
            "analysis_date": target_date,
            "personal_year": {
                "number": personal_year,
                "meaning": self._get_cycle_meaning(personal_year),
                "keyword": self._get_keyword(personal_year)
            },
            "personal_month": {
                "number": personal_month,
                "meaning": self._get_cycle_meaning(personal_month),
                "keyword": self._get_keyword(personal_month)
            },
            "personal_day": {
                "number": personal_day,
                "meaning": self._get_cycle_meaning(personal_day),
                "keyword": self._get_keyword(personal_day)
            },
            "daily_guidance": synthesis,  # The "Human-like" explanation
            "calculation_logic": math_explanation
        }

    def _get_keyword(self, number: int) -> str:
        """Short themes for sentence construction."""
        keywords = {
            1: "New Beginnings", 2: "Patience", 3: "Self-Expression",
            4: "Hard Work", 5: "Change", 6: "Family Duty",
            7: "Introspection", 8: "Power/Success", 9: "Completion"
        }
        return keywords.get(number, "Transition")

    def _generate_synthesis(self, year, month, day) -> str:
        """Constructs the sentence connecting Year, Month, and Day."""
        y_key = self._get_keyword(year)
        m_key = self._get_keyword(month)
        d_key = self._get_keyword(day)
        
        return (f"Context: You are navigating a year of **{y_key} ({year})** and a month focused on **{m_key} ({month})**. "
                f"However, today specifically brings the vibration of **{d_key} ({day})**. "
                f"Use this specific energy to navigate the larger themes.")

    def get_life_roadmap(self, dob_str: str) -> Dict[str, Any]:
        """Calculate life pinnacles and cycles"""
        dob_year, dob_month, dob_day = map(int, dob_str.split('-'))
        
        # First Pinnacle (Birth to age 36-5 = 31)
        first_pinnacle = self.core.reduce_to_single(dob_month + dob_day)
        
        # Second Pinnacle (Age 32 to 40)
        second_pinnacle = self.core.reduce_to_single(dob_day + dob_year)
        
        # Third Pinnacle (Age 41 to 49)
        third_pinnacle = self.core.reduce_to_single(first_pinnacle + second_pinnacle)
        
        # Fourth Pinnacle (Age 50+)
        fourth_pinnacle = self.core.reduce_to_single(dob_month + dob_year)
        
        return {
            "pinnacles": {
                "first": {"number": first_pinnacle, "age_range": "Birth - 31", "meaning": self._get_cycle_meaning(first_pinnacle)},
                "second": {"number": second_pinnacle, "age_range": "32 - 40", "meaning": self._get_cycle_meaning(second_pinnacle)},
                "third": {"number": third_pinnacle, "age_range": "41 - 49", "meaning": self._get_cycle_meaning(third_pinnacle)},
                "fourth": {"number": fourth_pinnacle, "age_range": "50+", "meaning": self._get_cycle_meaning(fourth_pinnacle)}
            }
        }

    def _get_cycle_meaning(self, number: int) -> str:
        meanings = {
            1: "New Beginnings, Action, Initiative (Start something now)",
            2: "Cooperation, Patience, Relationships (Wait and seed)",
            3: "Creativity, Self-expression, Socializing (Be visible)",
            4: "Hard Work, Foundation, Discipline (Stick to routine)",
            5: "Change, Freedom, Travel, Unexpected Events (Be flexible)",
            6: "Responsibility, Home, Family, Duty (Care for others)",
            7: "Introspection, Spirituality, Research (Go inward)",
            8: "Power, Money, Career, Achievement (Big goals)",
            9: "Completion, Letting Go, Humanitarianism (Finish cycles)"
        }
        return meanings.get(number, "Transition Period")