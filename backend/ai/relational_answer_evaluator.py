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
        contract_ok, contract_errors = RelationalResponseContract.validate(text, profile, question=question)
        content, faq = ResponseParser.parse_faq_metadata(text)
        lower = (content or "").lower()
        relation_family = str(profile.get("relation_family") or "")
        event_topic = str(profile.get("event_topic") or "")

        timing_question = any(re.search(pat, question.lower()) for pat in cls.QUESTION_TIMING_PATTERNS)
        behavior_question = any(
            cue in question.lower() for cue in (
                "behave",
                "behavior",
                "behaviour",
                "nature",
                "personality",
                "married life",
                "why does she fight",
                "why does he fight",
            )
        )

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
        checks["behavior_sign_texture_present"] = True
        checks["behavior_nakshatra_texture_present"] = True
        if behavior_question and cls._behavior_texture_expected(evidence_spine):
            checks["behavior_sign_texture_present"] = cls._sign_texture_present(lower, evidence_spine)
            checks["behavior_nakshatra_texture_present"] = cls._nakshatra_texture_present(lower, evidence_spine)
        checks["timing_granularity_respected"] = True
        if timing_question:
            checks["timing_granularity_respected"] = cls._timing_granularity_respected(lower, evidence_spine)

        failed_checks: List[str] = []
        for name, passed in checks.items():
            if name in {"timing_clarity_present", "timing_granularity_respected"} and not timing_question:
                continue
            if name in {"behavior_sign_texture_present", "behavior_nakshatra_texture_present"} and not behavior_question:
                continue
            if not passed:
                failed_checks.append(name)

        score = sum(
            1
            for name, passed in checks.items()
            if passed or (name == "timing_clarity_present" and not timing_question)
        )
        max_score = len(checks) - (0 if timing_question else 2) - (0 if behavior_question else 2)
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

    @classmethod
    def _behavior_texture_expected(cls, evidence_spine: Dict[str, Any] | None) -> bool:
        if not isinstance(evidence_spine, dict):
            return False
        rel = evidence_spine.get("relation_specific_evidence") or {}
        return bool(rel.get("sign_flavor_native") or rel.get("sign_flavor_partner") or rel.get("nakshatra_flavor_native") or rel.get("nakshatra_flavor_partner"))

    @classmethod
    def _sign_texture_present(cls, lower: str, evidence_spine: Dict[str, Any] | None) -> bool:
        if not isinstance(evidence_spine, dict):
            return True
        rel = evidence_spine.get("relation_specific_evidence") or {}
        tokens = set()
        for key in ("sign_flavor_native", "sign_flavor_partner"):
            for row in rel.get(key) or []:
                sign = str(row.get("sign") or "").lower()
                flavor = str(row.get("sign_flavor") or "").lower()
                if sign:
                    tokens.add(sign)
                for word in flavor.split(","):
                    word = word.strip()
                    if word:
                        tokens.add(word)
        return any(token and token in lower for token in tokens)

    @classmethod
    def _nakshatra_texture_present(cls, lower: str, evidence_spine: Dict[str, Any] | None) -> bool:
        if not isinstance(evidence_spine, dict):
            return True
        rel = evidence_spine.get("relation_specific_evidence") or {}
        tokens = {"nakshatra"}
        for key in ("nakshatra_flavor_native", "nakshatra_flavor_partner"):
            block = rel.get(key) or {}
            for row in [block.get("moon"), block.get("seventh_lord"), *(block.get("relationship_planets") or [])]:
                if not isinstance(row, dict):
                    continue
                nak = str(row.get("nakshatra") or "").lower()
                flavor = str(row.get("flavor") or "").lower()
                if nak:
                    tokens.add(nak)
                for word in flavor.split(","):
                    word = word.strip()
                    if word:
                        tokens.add(word)
        return any(token and token in lower for token in tokens)

    @classmethod
    def _timing_granularity_respected(cls, lower: str, evidence_spine: Dict[str, Any] | None) -> bool:
        if not isinstance(evidence_spine, dict):
            return True
        strategy = evidence_spine.get("timing_strategy") or {}
        delivery = str(strategy.get("delivery_granularity") or "none")
        if delivery == "day":
            return True
        if delivery == "month":
            return not bool(re.search(r"\b\d{4}-\d{2}-\d{2}\b", lower))
        if delivery in {"year", "none"}:
            if re.search(r"\b\d{4}-\d{2}-\d{2}\b", lower):
                return False
            if any(month in lower for month in (
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december",
            )):
                return False
        return True
