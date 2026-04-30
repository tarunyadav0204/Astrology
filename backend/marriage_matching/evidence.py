"""Structured evidence objects for matching explanations and auditing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def evidence_item(
    code: str,
    category: str,
    polarity: str,
    weight: float,
    summary: str,
    facts: Optional[Dict[str, Any]] = None,
    rule_profile: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "code": code,
        "category": category,
        "polarity": polarity,
        "weight": round(float(weight), 2),
        "summary": summary,
        "facts": facts or {},
        "rule_profile": rule_profile,
    }


def bundle_evidence(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    positives = [item for item in items if item["polarity"] == "supportive"]
    cautions = [item for item in items if item["polarity"] == "challenging"]
    neutral = [item for item in items if item["polarity"] == "neutral"]
    return {
        "items": items,
        "counts": {
            "supportive": len(positives),
            "challenging": len(cautions),
            "neutral": len(neutral),
        },
        "supportive": positives,
        "challenging": cautions,
        "neutral": neutral,
    }
