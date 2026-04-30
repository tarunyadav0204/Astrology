"""Curated benchmark fixtures for deterministic kundli matching."""

from __future__ import annotations

from typing import Any, Dict, List

from .engine import KundliMatchingEngine


def _planet(longitude: float, house: int | None = None) -> Dict[str, Any]:
    sign_zero = int((longitude % 360.0) / 30.0)
    return {
        "longitude": longitude % 360.0,
        "sign": sign_zero,
        "degree": longitude % 30.0,
        "house": house,
    }


def _chart(
    ascendant: float,
    moon_long: float,
    mars_long: float = 180.0,
    venus_long: float = 45.0,
    jupiter_long: float = 120.0,
    saturn_long: float = 270.0,
    sun_long: float = 15.0,
    mercury_long: float = 80.0,
) -> Dict[str, Any]:
    return {
        "ascendant": ascendant,
        "ayanamsa": 24.0,
        "planets": {
            "Sun": _planet(sun_long),
            "Moon": _planet(moon_long),
            "Mars": _planet(mars_long),
            "Mercury": _planet(mercury_long),
            "Jupiter": _planet(jupiter_long),
            "Venus": _planet(venus_long),
            "Saturn": _planet(saturn_long),
        },
        "houses": [{"sign": int(((ascendant / 30.0) + i) % 12)} for i in range(12)],
    }


def _birth(name: str) -> Dict[str, Any]:
    return {
        "name": name,
        "date": "1990-01-01",
        "time": "10:30",
        "latitude": 17.385,
        "longitude": 78.4867,
        "place": "Hyderabad",
    }


BENCHMARK_CASES: List[Dict[str, Any]] = [
    {
        "id": "same_nak_diff_pada_nadi_exception",
        "rule_profile": "balanced_modern",
        "boy_chart": _chart(0.0, 0.5),
        "girl_chart": _chart(0.0, 4.0),
        "expects": {
            "nadi_exception": True,
            "effective_score_gt_raw": True,
        },
    },
    {
        "id": "bhakoot_friendly_ruler_exception",
        "rule_profile": "balanced_modern",
        "boy_chart": _chart(0.0, 5.0),
        "girl_chart": _chart(0.0, 335.0),
        "expects": {
            "bhakoot_exception": True,
            "critical_issue_removed": "2/12 Bhakoot Dosha",
        },
    },
    {
        "id": "both_manglik_balanced",
        "rule_profile": "balanced_modern",
        "boy_chart": _chart(0.0, 45.0, mars_long=180.0),
        "girl_chart": _chart(30.0, 75.0, mars_long=210.0),
        "expects": {
            "manglik_status": "Compatible",
            "pair_cancellation": True,
        },
    },
    {
        "id": "one_sided_manglik_sensitive",
        "rule_profile": "classical_strict",
        "boy_chart": _chart(0.0, 45.0, mars_long=180.0),
        "girl_chart": _chart(30.0, 15.0, mars_long=165.0, venus_long=15.0, jupiter_long=300.0),
        "expects": {
            "manglik_status": "Sensitive",
        },
    },
]


def run_benchmark_suite(rule_profile: str = "balanced_modern") -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for case in BENCHMARK_CASES:
        engine = KundliMatchingEngine(rule_profile=case.get("rule_profile", rule_profile))
        result = engine.analyze(case["boy_chart"], case["girl_chart"], _birth("Boy"), _birth("Girl"))
        results.append(
            {
                "id": case["id"],
                "rule_profile": case.get("rule_profile", rule_profile),
                "result": result,
                "expects": case["expects"],
            }
        )
    return results
