from __future__ import annotations

from typing import Any, Dict


def build_system_prompt(report_type: str, language: str) -> str:
    return (
        "You are a Vedic astrology report engine. "
        "Return structured, premium, factual guidance in "
        f"{language or 'english'}. "
        f"Report type: {report_type}."
    )


def build_partnership_prompt(context: Dict[str, Any], language: str) -> str:
    return build_system_prompt("partnership", language)


def build_page_instructions(report_type: str) -> Dict[str, Any]:
    return {"report_type": report_type, "page_count": 20}


def build_llm_context_excerpt(context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "person_a": context.get("person_a"),
        "person_b": context.get("person_b"),
        "score_summary": context.get("score_summary"),
    }

