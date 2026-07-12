from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

from calculators.chart_calculator import ChartCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from ..cache.report_hash import normalize_birth_data


def to_birth_namespace(birth_data: Any) -> SimpleNamespace:
    payload = normalize_birth_data(birth_data)
    payload.setdefault("name", None)
    payload.setdefault("place", "")
    payload.setdefault("timezone", None)
    return SimpleNamespace(**payload)


def calculate_chart_for_birth(birth_data: Any, node_type: str = "mean") -> Dict[str, Any]:
    chart = ChartCalculator({})
    birth_ns = to_birth_namespace(birth_data)
    return chart.calculate_chart(birth_ns, node_type)


def calculate_divisional_chart(chart_data: Dict[str, Any], division: int) -> Dict[str, Any]:
    calculator = DivisionalChartCalculator(chart_data)
    return calculator.calculate_divisional_chart(division)


def build_base_context(birth_a: Any, birth_b: Any) -> Dict[str, Any]:
    chart_a = calculate_chart_for_birth(birth_a)
    chart_b = calculate_chart_for_birth(birth_b)
    return {
        "person_a": normalize_birth_data(birth_a),
        "person_b": normalize_birth_data(birth_b),
        "chart_a": chart_a,
        "chart_b": chart_b,
    }

