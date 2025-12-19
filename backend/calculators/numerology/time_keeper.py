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
        """Calculates Cosmic Weather with narrative explanation."""
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

        # --- Narrative Synthesis ---
        synthesis = self._generate_synthesis(personal_year, personal_month, personal_day)
        
        # --- Calculation Logic (The "Show Your Work") ---
        math_explanation = (
            f"Year ({personal_year}) = Day {dob_day} + Month {dob_month} + World Year {curr_year}. "
            f"Month ({personal_month}) = Year {personal_year} + Current Month {curr_month}. "
            f"Day ({personal_day}) = Month {personal_month} + Today {curr_day}."
        )

        return {
            "analysis_date": target_date,
            "personal_year": {
                "number": personal_year,
                "meaning": self._get_cycle_meaning(personal_year, "Year"),
                "keyword": self._get_keyword(personal_year)
            },
            "personal_month": {
                "number": personal_month,
                "meaning": self._get_cycle_meaning(personal_month, "Month"),
                "keyword": self._get_keyword(personal_month)
            },
            "personal_day": {
                "number": personal_day,
                "meaning": self._get_cycle_meaning(personal_day, "Day"),
                "keyword": self._get_keyword(personal_day)
            },
            "daily_guidance": synthesis,
            "calculation_logic": math_explanation
        }

    def _get_keyword(self, number: int) -> str:
        keywords = {
            1: "New Beginnings", 2: "Patience & Connection", 3: "Joy & Expression",
            4: "Hard Work", 5: "Change & Freedom", 6: "Family & Duty",
            7: "Rest & Reflection", 8: "Power & Success", 9: "Completion"
        }
        return keywords.get(number, "Transition")

    def _generate_synthesis(self, year, month, day) -> str:
        """Constructs a human-readable advice paragraph."""
        y_key = self._get_keyword(year)
        m_key = self._get_keyword(month)
        d_key = self._get_keyword(day)
        
        return (f"You are navigating a **Year of {y_key} ({year})**, which sets the big picture. "
                f"Currently, the month brings a focus on **{m_key} ({month})**. "
                f"However, specifically for today, the energy shifts to **{d_key} ({day})**. "
                f"Use today's vibe to support your larger yearly goals.")

    def get_life_roadmap(self, dob_str: str) -> Dict[str, Any]:
        """Calculates Life Pinnacles (unchanged logic, just ensuring function exists)."""
        year, month, day = map(int, dob_str.split('-'))
        r_month = self.core.reduce_to_single(month)
        r_day = self.core.reduce_to_single(day)
        r_year = self.core.reduce_to_single(year)
        life_path = self.core.reduce_to_single(r_month + r_day + r_year)
        
        p1 = self.core.reduce_to_single(r_month + r_day)
        p2 = self.core.reduce_to_single(r_day + r_year)
        p3 = self.core.reduce_to_single(p1 + p2)
        p4 = self.core.reduce_to_single(r_month + r_year)

        age_shift_1 = 36 - life_path
        age_shift_2 = age_shift_1 + 9
        age_shift_3 = age_shift_2 + 9

        return {
            "life_path": life_path,
            "timeline": [
                {"phase": "Early Life", "age_range": f"0 - {age_shift_1}", "pinnacle": {"number": p1, "meaning": self._get_pinnacle_meaning(p1)}},
                {"phase": "Mid Life", "age_range": f"{age_shift_1 + 1} - {age_shift_2}", "pinnacle": {"number": p2, "meaning": self._get_pinnacle_meaning(p2)}},
                {"phase": "Maturity", "age_range": f"{age_shift_2 + 1} - {age_shift_3}", "pinnacle": {"number": p3, "meaning": self._get_pinnacle_meaning(p3)}},
                {"phase": "Legacy", "age_range": f"{age_shift_3 + 1}+", "pinnacle": {"number": p4, "meaning": self._get_pinnacle_meaning(p4)}}
            ]
        }

    def _get_cycle_meaning(self, number: int, cycle_type: str) -> str:
        meanings = {
            1: "Action time! Plant seeds for the future. Don't wait.",
            2: "Wait and see. Focus on partnerships and patience.",
            3: "Express yourself! Socialize and be creative.",
            4: "Work hard. Handle details and build foundations.",
            5: "Expect the unexpected. Travel and embrace change.",
            6: "Focus on home, family, and domestic responsibilities.",
            7: "Go within. Meditate, study, and analyze.",
            8: "Focus on business, money, and career success.",
            9: "Clean house. Finish old tasks and prepare for the new."
        }
        return meanings.get(number, "Transition Period")

    def _get_pinnacle_meaning(self, number: int) -> str:
        meanings = {
            1: "Learning to stand on your own feet and lead.",
            2: "Learning cooperation, detail, and diplomacy.",
            3: "Developing your creative voice and artistic expression.",
            4: "Building a secure foundation through hard work.",
            5: "Learning to embrace freedom and adapt to change.",
            6: "Serving family and community with love.",
            7: "Spiritual development and specialization.",
            8: "Achieving authority and commercial success.",
            9: "Service to humanity and letting go of self."
        }
        return meanings.get(number, "A period of mastery.")