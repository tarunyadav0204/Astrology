from __future__ import annotations

from typing import Any, Dict, List

from .base_context_builder import calculate_divisional_chart


def build_chart_image_manifest(chart_style: str = "both") -> List[Dict[str, Any]]:
    slots = [
        {"slot": "d1_north", "chart": "D1", "style": "north"},
        {"slot": "d1_south", "chart": "D1", "style": "south"},
        {"slot": "d9_north", "chart": "D9", "style": "north"},
        {"slot": "d9_south", "chart": "D9", "style": "south"},
        {"slot": "d60_summary", "chart": "D60", "style": "summary"},
    ]
    if chart_style == "north":
        return [slot for slot in slots if slot["style"] in {"north", "summary"}]
    if chart_style == "south":
        return [slot for slot in slots if slot["style"] in {"south", "summary"}]
    return slots


def build_divisional_chart_slot(chart_data: Dict[str, Any], division: int) -> Dict[str, Any]:
    return calculate_divisional_chart(chart_data, division)

