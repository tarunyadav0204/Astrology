from __future__ import annotations

from typing import Any, Dict, List


HOUSE_LABELS = {
    1: "self, vitality, personal direction",
    2: "income, family assets, speech, resources",
    3: "effort, communication, initiative, short moves",
    4: "home, peace, property, emotional base",
    5: "creativity, children, romance, learning",
    6: "workload, conflict, debt, service",
    7: "partnerships, spouse, agreements",
    8: "research, transformation, intimacy",
    9: "fortune, mentors, dharma",
    10: "career, public role, visibility",
    11: "gains, networks, support circles",
    12: "retreat, foreign links, sleep, letting go",
}


def build_house_wise_synthesis(engine_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "houses": [
            {"house": num, "theme": theme, "strength": "mixed"}
            for num, theme in HOUSE_LABELS.items()
        ]
    }


def build_house_summary_rows(engine_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    return build_house_wise_synthesis(engine_result)["houses"]

