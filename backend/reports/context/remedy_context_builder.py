from __future__ import annotations

from typing import Any, Dict, List


def build_remedy_context(engine_result: Dict[str, Any], premium_report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "remedies": engine_result.get("recommendation", {}).get("remedies", []),
        "priority_actions": premium_report.get("priority_actions", []),
        "final_summary": premium_report.get("final_summary"),
    }


def select_top_remedies(remedies: List[str], limit: int = 3) -> List[str]:
    return remedies[:limit]


def map_remedies_to_challenges(challenges: List[str], remedies: List[str]) -> List[Dict[str, Any]]:
    mapped = []
    for idx, challenge in enumerate(challenges):
        mapped.append({
            "challenge": challenge,
            "remedy": remedies[idx] if idx < len(remedies) else None,
        })
    return mapped

