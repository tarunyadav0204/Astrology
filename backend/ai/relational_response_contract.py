"""Lightweight validator for relational final-answer shape and safety."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from ai.response_parser import ResponseParser


class RelationalResponseContract:
    """Validate final relational answer shape against deterministic question profile."""

    GENERIC_EVENT_SECTIONS = (
        "overall compatibility",
        "emotional bond",
        "physical chemistry",
        "romantic chemistry",
        "long-term stability",
    )

    ACCUSATION_TOPICS = {
        "trust_infidelity",
        "legal_confinement",
        "business_betrayal",
        "guru_trust_breach",
        "abuse_safety",
    }

    OVERCLAIM_PATTERNS = (
        r"\bguaranteed\b",
        r"\bdefinitely happened\b",
        r"\bthey absolutely cheated\b",
        r"\bwithout doubt\b",
        r"\bproves that\b",
        r"\bwill certainly go to jail\b",
    )

    SAFETY_CUE_PATTERNS = (
        r"\bindicat(?:e|es|ion)\b",
        r"\bsuggest(?:s|ed|ive)?\b",
        r"\brisk\b",
        r"\buncertain(?:ty)?\b",
        r"\bcannot prove\b",
        r"\bnot proof\b",
        r"\bverification\b",
    )

    @classmethod
    def validate(cls, text: str, profile: Dict[str, Any], question: str | None = None) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not text or len(text.strip()) < 40:
            return False, ["response_too_short"]

        content, faq = ResponseParser.parse_faq_metadata(text)
        lower = content.lower()
        event_topic = str(profile.get("event_topic") or "")
        relation_family = str(profile.get("relation_family") or "")
        q = str(question or "").lower()
        behavior_question = any(
            cue in q for cue in (
                "behave",
                "behavior",
                "behaviour",
                "nature",
                "personality",
                "why does she fight",
                "why does he fight",
                "married life",
            )
        )

        if faq is None:
            errors.append("missing_faq_meta")

        if event_topic not in {"general_relationship", "support_guidance"} or behavior_question:
            for heading in cls.GENERIC_EVENT_SECTIONS:
                if heading in lower:
                    errors.append(f"forbidden_generic_section:{heading}")

        if event_topic == "general_relationship" and behavior_question:
            if "nakshatra" not in lower:
                errors.append("missing_behavior_texture_nakshatra")
            if not any(sign in lower for sign in (
                "aries", "taurus", "gemini", "cancer", "leo", "virgo",
                "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
            )):
                errors.append("missing_behavior_texture_sign")

        if event_topic in cls.ACCUSATION_TOPICS:
            if any(re.search(pat, lower) for pat in cls.OVERCLAIM_PATTERNS):
                errors.append("unsafe_overclaim_language")
            if not any(re.search(pat, lower) for pat in cls.SAFETY_CUE_PATTERNS):
                errors.append("missing_safety_uncertainty_cue")

        if relation_family == "spouse_romantic" and faq is not None and faq.get("category") not in {"marriage", "general"}:
            errors.append("unexpected_faq_category_for_romantic")
        if relation_family != "spouse_romantic" and faq is not None and faq.get("category") not in {"general", "other"}:
            errors.append("unexpected_faq_category_for_non_romantic")

        return len(errors) == 0, errors
