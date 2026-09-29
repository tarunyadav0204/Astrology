"""Public application service for partner profiles."""

from __future__ import annotations

from typing import Any, Dict

from .evidence_builder import build_partner_evidence
from .synthesizer import synthesize_partner_profile


def build_partner_profile(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    return synthesize_partner_profile(build_partner_evidence(chart_data))

