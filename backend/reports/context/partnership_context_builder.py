from __future__ import annotations

from typing import Any, Dict

from .base_context_builder import build_base_context
from .shared_branch_context import (
    build_d60_context,
    build_jaimini_context,
    build_kp_context,
    build_nadi_context,
    build_nakshatra_context,
)
from ..cache.report_hash import normalize_birth_data, normalize_language


def build_partnership_report_context(request: Any) -> Dict[str, Any]:
    base = build_base_context(request.boy_birth_data, request.girl_birth_data)
    boy_chart = base["chart_a"]
    girl_chart = base["chart_b"]
    boy_person = normalize_birth_data(request.boy_birth_data)
    girl_person = normalize_birth_data(request.girl_birth_data)

    boy_jaimini = build_jaimini_context(boy_chart)
    boy_nadi = build_nadi_context(boy_chart)
    boy_nakshatra = build_nakshatra_context(boy_chart)
    boy_d60 = build_d60_context(boy_chart)
    boy_kp = build_kp_context(request.boy_birth_data)

    girl_jaimini = build_jaimini_context(girl_chart)
    girl_nadi = build_nadi_context(girl_chart)
    girl_nakshatra = build_nakshatra_context(girl_chart)
    girl_d60 = build_d60_context(girl_chart)
    girl_kp = build_kp_context(request.girl_birth_data)

    return {
        "report_type": "partnership",
        "language": normalize_language(getattr(request, "language", "english")),
        "chart_style": getattr(request, "chart_style", "both"),
        "person_a": boy_person,
        "person_b": girl_person,
        "boy_chart": boy_chart,
        "girl_chart": girl_chart,
        "branches": {
            "boy": {
                "jaimini": boy_jaimini,
                "nadi": boy_nadi,
                "nakshatra": boy_nakshatra,
                "d60": boy_d60,
                "kp": boy_kp,
            },
            "girl": {
                "jaimini": girl_jaimini,
                "nadi": girl_nadi,
                "nakshatra": girl_nakshatra,
                "d60": girl_d60,
                "kp": girl_kp,
            },
        },
        "summaries": {
            "boy": {
                "jaimini": boy_jaimini["summary"],
                "nadi": boy_nadi["summary"],
                "nakshatra": boy_nakshatra["summary"],
                "d60": boy_d60["summary"],
                "kp": boy_kp["summary"],
            },
            "girl": {
                "jaimini": girl_jaimini["summary"],
                "nadi": girl_nadi["summary"],
                "nakshatra": girl_nakshatra["summary"],
                "d60": girl_d60["summary"],
                "kp": girl_kp["summary"],
            },
        },
    }
