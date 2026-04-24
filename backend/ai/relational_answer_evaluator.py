"""Heuristic evaluator for final relational answers."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from ai.relational_response_contract import RelationalResponseContract
from ai.response_parser import ResponseParser


class RelationalAnswerEvaluator:
    """Score user-facing relational answers for directness, evidence, timing, and framing."""

    EVIDENCE_CUES = (
        "house",
        "lord",
        "dasha",
        "venus",
        "mars",
        "moon",
        "saturn",
        "rahu",
        "ketu",
        "jupiter",
        "nakshatra",
        "kp",
        "argala",
        "ul",
        "a7",
        "bindu",
        "ashtakavarga",
        "sudarshana",
    )

    DIRECT_ANSWER_CUES = (
        "direct answer",
        "quick answer",
        "the chart suggests",
        "the chart shows",
        "yes",
        "no",
        "likely",
        "unlikely",
    )

    TIMING_CUES = (
        "month",
        "months",
        "window",
        "period",
        "timing",
        "between",
        "within",
        "this year",
        "next year",
        "currently",
        "coming months",
    )

    OPTIONAL_BRANCH_CUES = (
        "ashtakavarga",
        "bindu",
        "sudarshana",
        "tri-perspective",
        "lagna/moon/sun",
        "lagna, moon, and sun",
        "lagna moon sun",
        "endurance",
        "one-sided support",
        "current activation",
    )

    AV_NUMERIC_CUES = (
        r"\b\d+\s*sav\b",
        r"\b\d+\s*bav\b",
        r"\b\d+\s*bindu(?:s)?\b",
    )

    NON_ROMANTIC_SPOUSE_TERMS = (
        "marriage compatibility",
        "romantic chemistry",
        "wife",
        "husband",
        "spouse",
    )

    QUESTION_TIMING_PATTERNS = (
        r"\bwhen\b",
        r"\bwill\b",
        r"\bcome back\b",
        r"\breturn\b",
        r"\breconcile\b",
        r"\bleave\b",
        r"\bgo to jail\b",
        r"\bpay\b",
        r"\brepay\b",
    )

    @classmethod
    def evaluate(
        cls,
        *,
        text: str,
        profile: Dict[str, Any],
        question: str,
        evidence_spine: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        contract_ok, contract_errors = RelationalResponseContract.validate(text, profile)
        content, faq = ResponseParser.parse_faq_metadata(text)
        lower = (content or "").lower()
        relation_family = str(profile.get("relation_family") or "")
        event_topic = str(profile.get("event_topic") or "")

        timing_question = any(re.search(pat, question.lower()) for pat in cls.QUESTION_TIMING_PATTERNS)

        checks: Dict[str, bool] = {}
        checks["contract_ok"] = contract_ok
        checks["direct_answer_present"] = any(cue in lower for cue in cls.DIRECT_ANSWER_CUES)
        checks["astrological_evidence_present"] = any(cue in lower for cue in cls.EVIDENCE_CUES)
        checks["timing_clarity_present"] = any(cue in lower for cue in cls.TIMING_CUES)
        checks["non_romantic_spouse_framing_clean"] = True
        if relation_family != "spouse_romantic":
            checks["non_romantic_spouse_framing_clean"] = not any(term in lower for term in cls.NON_ROMANTIC_SPOUSE_TERMS)
        checks["faq_present"] = faq is not None
        checks["uncertainty_present_for_accusation"] = True
        if event_topic in RelationalResponseContract.ACCUSATION_TOPICS:
            checks["uncertainty_present_for_accusation"] = not (
                "missing_safety_uncertainty_cue" in contract_errors or "unsafe_overclaim_language" in contract_errors
            )
        checks["optional_branch_signal_used"] = True
        if cls._optional_branch_signal_should_be_used(evidence_spine):
            checks["optional_branch_signal_used"] = any(cue in lower for cue in cls.OPTIONAL_BRANCH_CUES)
        checks["no_unsupported_av_numbers"] = True
        if cls._av_numeric_signal_missing(evidence_spine):
            checks["no_unsupported_av_numbers"] = not any(re.search(pat, lower) for pat in cls.AV_NUMERIC_CUES)

        failed_checks: List[str] = []
        for name, passed in checks.items():
            if name == "timing_clarity_present" and not timing_question:
                continue
            if not passed:
                failed_checks.append(name)

        score = sum(
            1
            for name, passed in checks.items()
            if passed or (name == "timing_clarity_present" and not timing_question)
        )
        max_score = len(checks) - (0 if timing_question else 1)
        return {
            "passed": len(failed_checks) == 0,
            "score": score,
            "max_score": max_score,
            "checks": checks,
            "timing_question": timing_question,
            "failed_checks": failed_checks,
            "contract_errors": contract_errors,
        }

    @classmethod
    def _optional_branch_signal_should_be_used(cls, evidence_spine: Dict[str, Any] | None) -> bool:
        if not isinstance(evidence_spine, dict):
            return False
        av = evidence_spine.get("ashtakavarga_relational_evidence") or {}
        sx = evidence_spine.get("sudarshana_relational_evidence") or {}
        av_useful = bool(
            av.get("available")
            and (av.get("comparative") or {}).get("support") in {
                "both_supportive",
                "native_supportive_partner_mixed",
                "partner_supportive_native_mixed",
            }
        )
        sx_comp = sx.get("comparative") or {}
        sx_useful = bool(
            sx.get("available")
            and (
                sx_comp.get("both_supportive")
                or sx_comp.get("both_challenging")
                or sx_comp.get("native_current_support") in {"supportive", "challenging"}
                or sx_comp.get("partner_current_support") in {"supportive", "challenging"}
            )
        )
        return av_useful or sx_useful

    @classmethod
    def _av_numeric_signal_missing(cls, evidence_spine: Dict[str, Any] | None) -> bool:
        if not isinstance(evidence_spine, dict):
            return False
        av = evidence_spine.get("ashtakavarga_relational_evidence") or {}
        if not av or not av.get("available"):
            return True
        rows = list(((av.get("native") or {}).get("rows") or [])) + list(((av.get("partner") or {}).get("rows") or []))
        if not rows:
            return True
        return not any(isinstance(row.get("sav"), int) or bool(row.get("bav")) for row in rows)
