"""Shared visible-astrology contract for every Instant answer.

Calculators and graph policies remain technical.  This adapter selects a small
set of evidence-bound planetary reasons that the answer model may translate
into ordinary life language without falling back to either jargon or generic
psychology.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
PLANET_MEANINGS = {
    "Sun": "confidence, visibility, authority and clear direction",
    "Moon": "emotional rhythm, receptivity, care and adaptability",
    "Mars": "drive, courage, urgency, conflict and decisive action",
    "Mercury": "analysis, communication, learning and adaptability",
    "Jupiter": "understanding, growth, judgment, guidance and expansion",
    "Venus": "harmony, relationships, values, creativity and comfort",
    "Saturn": "discipline, responsibility, delay, endurance and structure",
    "Rahu": "amplification, unconventional ambition, appetite and restlessness",
    "Ketu": "detachment, discontinuity, inward focus and specialization",
}
HINDI_NAMES = {
    "Sun": "Surya", "Moon": "Chandra", "Mars": "Mangal", "Mercury": "Budh",
    "Jupiter": "Guru", "Venus": "Shukra", "Saturn": "Shani", "Rahu": "Rahu", "Ketu": "Ketu",
}
ALIASES = {
    "Sun": ("sun", "surya", "सूर्य"), "Moon": ("moon", "chandra", "चंद्र", "चन्द्र"),
    "Mars": ("mars", "mangal", "मंगल"), "Mercury": ("mercury", "budh", "budha", "बुध"),
    "Jupiter": ("jupiter", "guru", "brihaspati", "गुरु", "बृहस्पति"),
    "Venus": ("venus", "shukra", "शुक्र"),
    "Saturn": ("saturn", "shani", "शनि"), "Rahu": ("rahu", "राहु"), "Ketu": ("ketu", "केतु"),
}
_TECHNICAL_RE = re.compile(
    r"(?:\bD(?:1|2|3|4|7|9|10|12|16|20|24|27|30|40|45|60)\b|\b(?:MD|AD|PD)\b|"
    r"\b(?:mahadasha|antardasha|pratyantardasha|sookshma|prana|navamsa|saptamsa|dashamsa|hora)\b|"
    r"\b(?:gandanta|yogi|avayogi|dagdha(?:\s+rashi)?|tithi\s+shunya|moolatrikona|KP)\b|"
    r"\b(?:house|H)\s*\d{1,2}\b|\b\d{1,2}(?:st|nd|rd|th)\s+house\b|\b\d+(?:\.\d+)?\s*degrees?\b)",
    re.IGNORECASE,
)
_TECHNICAL_REQUEST_RE = re.compile(
    r"\b(?:technical|calculation|astrological\s+logic|show\s+evidence|why\s+tara|"
    r"D(?:1|2|3|4|7|9|10|12|16|20|24|27|30|40|45|60)|dasha|mahadasha|antardasha|pratyantardasha|nakshatra|navamsa|saptamsa|"
    r"gandanta|yogi|avayogi|dagdha|tithi\s+shunya|kp|house\s+lord|aspect)\b",
    re.IGNORECASE,
)
_EXEMPT_MODES = frozenset({
    "handoff", "safety_refusal", "factual_chart_lookup", "dedicated_partnership_flow",
    "dedicated_muhurat_flow", "small_talk",
})


def _iter_evidence(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        # Preserve the relationship between a planet and the calculated fact
        # beside it. Walking only scalar leaves turns {planet: Jupiter,
        # condition: ...} into the meaningless source fact "Jupiter".
        row_planet = next(
            (
                str(value.get(key)).strip()
                for key in ("planet", "lord", "carrier", "dasha_lord")
                if isinstance(value.get(key), str)
                and str(value.get(key)).strip().title() in PLANETS
            ),
            "",
        )
        if row_planet:
            row_fact = {
                str(key): child
                for key, child in value.items()
                if isinstance(child, (str, int, float, bool))
                and child not in (None, "")
            }
            if len(row_fact) >= 2:
                yield path, json.dumps(row_fact, ensure_ascii=False, default=str)
        # Graph metadata is implementation detail, not answer-bearing evidence.
        for key, child in value.items():
            token = str(key)
            if token in {"knowledge_graph_policy", "graph_tree", "charts", "calculator_bindings"}:
                continue
            yield from _iter_evidence(child, f"{path}.{token}" if path else token)
    elif isinstance(value, list):
        for index, child in enumerate(value[:16]):
            yield from _iter_evidence(child, f"{path}[{index}]")
    elif isinstance(value, str) and value.strip():
        yield path, value.strip()


def _path_score(path: str, text: str) -> int:
    score = 10
    lower = path.lower()
    for marker, weight in (
        ("answer_evidence_contract", 135), ("requested_window_assessment", 132),
        ("immutable_fact_contract", 130), ("timing_synthesis", 125),
        ("route_synthesis", 100), ("required_visible_facts", 95),
        ("supporting_factors", 85), ("cautions", 82), ("ranked_windows", 78),
        ("primary_drivers", 75), ("why", 72), ("reason", 68),
        ("house_lord_conditions", 65), ("carrier", 62),
    ):
        if marker in lower:
            score = max(score, weight)
    if len(text) > 320:
        score -= 10
    if len(text.strip()) < 12 or text.strip().title() in PLANETS:
        score -= 70
    return score


def _polarity(path: str, text: str) -> str:
    lowered = f"{path} {text}".lower()
    if any(token in lowered for token in ("caution", "pressure", "risk", "delay", "weak", "debilitat", "combust", "obstacle")):
        return "qualifying"
    if any(token in lowered for token in ("support", "strong", "own sign", "exalt", "protect", "favour", "favor")):
        return "supportive"
    return "contextual"


def build_translated_astrology_contract(
    composer_context: Mapping[str, Any] | None,
    *,
    question: str,
    language: str,
    response_style: str | None = None,
) -> dict[str, Any]:
    context = composer_context if isinstance(composer_context, Mapping) else {}
    query_plan = context.get("query_plan") if isinstance(context.get("query_plan"), Mapping) else {}
    answer_contract = context.get("answer_contract") if isinstance(context.get("answer_contract"), Mapping) else {}
    graph_policy = answer_contract.get("knowledge_graph_policy") if isinstance(answer_contract.get("knowledge_graph_policy"), Mapping) else {}
    graph_domain = str(graph_policy.get("domain") or "").strip().lower()
    answer_mode = str(query_plan.get("answer_mode") or "").strip().lower()
    claim_permission = str(graph_policy.get("claim_permission") or "").lower()
    exempt = bool(
        answer_mode in _EXEMPT_MODES
        or any(token in claim_permission for token in ("handoff", "refusal", "boundary"))
    )
    time_scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), Mapping) else {}
    # The progressive retrospective timeline deliberately shows MD/AD/PD
    # boundaries because the user selects among them. That dedicated product
    # flow is the one exception to the ordinary no-jargon main-answer rule.
    selected_style = str(response_style or "").strip().lower()
    if selected_style not in {"simple", "technical"}:
        selected_style = ""
    technical_requested = bool(
        selected_style == "technical"
        or (not selected_style and _TECHNICAL_REQUEST_RE.search(str(question or "")))
        or time_scope.get("retrospective")
    )
    evidence = {
        "verdict": context.get("verdict") or {},
        "evidence": context.get("evidence") or context.get("normalized_evidence") or {},
    }
    candidates: dict[str, dict[str, Any]] = {}
    for path, text in _iter_evidence(evidence):
        for planet in PLANETS:
            if not re.search(rf"\b{re.escape(planet)}\b", text, re.IGNORECASE):
                continue
            score = _path_score(path, text)
            row = {
                "planet": planet,
                "display_name": HINDI_NAMES[planet] if str(language).lower().startswith("hi") else planet,
                "polarity": _polarity(path, text),
                "plain_meaning_range": PLANET_MEANINGS[planet],
                "source_fact": text[:280],
                "evidence_path": path,
                "score": score,
            }
            if planet not in candidates or score > int(candidates[planet].get("score") or 0):
                candidates[planet] = row
    anchor_limit = len(PLANETS) if technical_requested else 4
    anchors = sorted(
        candidates.values(),
        key=lambda row: (-int(row["score"]), PLANETS.index(row["planet"])),
    )[:anchor_limit]
    evidence_body = evidence.get("evidence") if isinstance(evidence.get("evidence"), Mapping) else {}
    remedy_blueprint = (
        evidence_body.get("remedy_blueprint")
        if isinstance(evidence_body.get("remedy_blueprint"), Mapping)
        else {}
    )
    top_remedy = (
        remedy_blueprint.get("top_recommendation")
        if isinstance(remedy_blueprint.get("top_recommendation"), Mapping)
        else {}
    )
    top_remedy_planet = str(top_remedy.get("planet") or "").strip().title()
    if (
        answer_mode == "remedy_action"
        and str(remedy_blueprint.get("selection_mode") or "") == "single_top"
        and top_remedy_planet in PLANETS
    ):
        reason = str(top_remedy.get("astrological_reason") or "").strip()
        anchors = [{
            "planet": top_remedy_planet,
            "display_name": HINDI_NAMES[top_remedy_planet] if str(language).lower().startswith("hi") else top_remedy_planet,
            "polarity": "qualifying",
            "plain_meaning_range": PLANET_MEANINGS[top_remedy_planet],
            "source_fact": reason or f"{top_remedy_planet} is the top calculated remedy driver.",
            "evidence_path": "evidence.remedy_blueprint.top_recommendation.astrological_reason",
        }]
    for row in anchors:
        row.pop("score", None)
    required = bool(anchors and not exempt)
    verdict = context.get("verdict") if isinstance(context.get("verdict"), Mapping) else {}
    verdict_snapshot = {
        key: verdict.get(key)
        for key in ("direction", "confidence", "status", "scope")
        if verdict.get(key) not in (None, "", [], {})
    }
    simple_maximum = len(anchors) if graph_domain == "home_property" else 2
    return {
        "schema_version": "instant-visible-astrology/v1",
        "required": required,
        "exempt": exempt,
        "response_style": selected_style or ("technical" if technical_requested else "simple"),
        "technical_detail_allowed": technical_requested,
        "minimum_planet_reasons": 1 if required else 0,
        # Technical is allowed to name every evidence-bearing planet required
        # by its D1/divisional/KP/dasha/transit explanation. The two-planet
        # ceiling belongs only to the concise Simple rendering.
        "maximum_planet_reasons": len(anchors) if technical_requested else simple_maximum,
        "allowed_planets": [row["planet"] for row in anchors],
        "reason_anchors": anchors,
        "verdict_snapshot": verdict_snapshot,
        "claim_fidelity_rule": (
            "Simple and Technical are two renderings of the same adjudicated answer, not two interpretations. "
            "Preserve the verdict direction, confidence, polarity, conditions, uncertainty and material cautions. "
            "Changing style may change terminology, definitions and explanation depth only. Never upgrade neutral, "
            "mixed, qualified, conditional, fluctuating or cautionary evidence into excellent, unequivocally strong, "
            "certain or unqualified language. Never weaken a supported conclusion, drop a material caution, or add "
            "an ability or outcome absent from the supplied verdict and source facts."
        ),
        "main_answer_rule": (
            "Direct answer -> translated planetary reason -> lived meaning -> one useful action. "
            "A planet name is not permission to add generic folklore; every effect must remain tied to its source_fact."
        ),
        "technical_terms_rule": (
            "TECHNICAL STYLE IS SELECTED. Explain the same verdict with the relevant supplied houses, lords, "
            "nakshatras, divisional charts, dasha levels, KP significators and transits. Define or briefly translate "
            "specialist terms as you use them. Use only details present in the supplied evidence. Do not expose graph "
            "names, ontology versions, internal IDs, scores, JSON, routing rules or hidden calculation machinery. "
            "This style instruction overrides generic requests elsewhere in the prompt to hide specialist terms."
            if technical_requested else
            "SIMPLE STYLE IS SELECTED. Keep chart codes, dasha-level names, house numbers, degrees and specialist "
            "conditions out of the visible answer; translate the evidence into planetary reasons and lived meaning."
        ),
    }


def translated_astrology_prompt_rule(contract: Mapping[str, Any] | None) -> str:
    contract = contract if isinstance(contract, Mapping) else {}
    if not contract.get("required"):
        return (
            "- Do not invent a planetary reason when the supplied evidence does not provide one. "
            + str(contract.get("claim_fidelity_rule") or "")
            + " "
            + str(contract.get("technical_terms_rule") or "")
        )
    planet_count_rule = (
        "Mention only the evidence-bearing planets needed for the supplied technical explanation from "
        if contract.get("technical_detail_allowed") else
        f"Mention only the evidence-bearing planets needed for this route, up to {int(contract.get('maximum_planet_reasons') or 2)}, from "
    )
    return (
        "- VISIBLE ASTROLOGY CONTRACT: " + planet_count_rule +
        f"`answer_contract.visible_astrology.reason_anchors` ({', '.join(contract.get('allowed_planets') or [])}). "
        "For each named planet, immediately translate its supplied source fact into the user's lived experience. "
        "Use the structure: direct answer -> planetary reason -> human meaning -> useful action. "
        "Do not mention a planet absent from the anchors and do not add remembered planet folklore. "
        + str(contract.get("claim_fidelity_rule") or "")
        + " "
        + str(contract.get("technical_terms_rule") or "")
    )


def validate_translated_astrology_answer(answer: str, contract: Mapping[str, Any] | None) -> list[str]:
    contract = contract if isinstance(contract, Mapping) else {}
    if not contract.get("required"):
        return []
    visible = re.split(r"\n\s*NEXT_ACTION_META\s*:", str(answer or ""), maxsplit=1)[0]
    def _mentions(alias: str) -> bool:
        if alias.isascii():
            return bool(re.search(rf"\b{re.escape(alias)}\b", visible, re.IGNORECASE))
        return alias in visible

    mentioned = {
        planet
        for planet, aliases in ALIASES.items()
        if any(_mentions(alias) for alias in aliases)
    }
    allowed = {str(value) for value in contract.get("allowed_planets") or []}
    errors = []
    if not mentioned:
        errors.append("missing translated planetary reason")
    unsupported = sorted(mentioned - allowed)
    if unsupported:
        errors.append(f"unsupported planet reason(s): {', '.join(unsupported)}")
    maximum = int(contract.get("maximum_planet_reasons") or 2)
    if len(mentioned) > maximum:
        errors.append(f"too many planet reasons: {len(mentioned)} (maximum {maximum})")
    if not contract.get("technical_detail_allowed") and _TECHNICAL_RE.search(visible):
        errors.append("technical astrology leaked into the main answer")
    return errors


__all__ = [
    "build_translated_astrology_contract",
    "translated_astrology_prompt_rule",
    "validate_translated_astrology_answer",
]
