"""Small, question-first routing contract for Verified Chat.

The router deliberately receives no natal chart, transit, dasha, or calculator
payload.  Its output selects the existing Instant answer mode and topic scope;
the following deterministic stage is the only source of astrological facts.
"""

from __future__ import annotations

import json
import asyncio
import os
import re
import time
from typing import Any, Callable, Dict, List, Optional

from chat.instant_chat_pipeline import ANSWER_MODES, TARGET_SUBJECTS
from utils.admin_settings import CHAT_LLM_OPENAI, get_verified_planner_model, get_verified_router_model


_CATEGORY_VALUES = [
    "general", "career", "job", "business", "wealth", "income", "debt",
    "investment", "health", "disease", "mental_wellbeing", "surgery", "accident", "recovery",
    "marriage", "relationship", "love", "family",
    "children", "education", "property", "relocation", "travel", "foreign",
    "litigation", "nakshatra",
]

# This is deliberately a closed registry.  Luna may select from these stable
# identifiers, but can never name or execute an arbitrary calculator.
CAPABILITY_REGISTRY = {
    "parashari.natal_foundation": "D1 placements, house lordships and topic-house evidence.",
    "parashari.dasha_timing": "Current and relevant Vimshottari dasha timing.",
    "parashari.transit_activation": "Current transit activation for the selected topic.",
    "parashari.divisional_confirmation": "Divisional-chart placements. Optional parameters.divisions specifies chart numbers (e.g. [9,10]); otherwise uses topic defaults.",
    "parashari.dignity_and_special_points": "Dignity, strength, Yogi, Avayogi and connected special-point evidence.",
    "parashari.ashtakavarga": "Sarvashtakavarga, Bhinnashtakavarga and advanced Ashtakavarga evidence.",
    "parashari.shadbala": "Calculated Shadbala strength evidence.",
    "parashari.panchadha_maitri": "Panchadha Maitri friendship matrix and planet positions.",
    "jaimini.significators_and_arudhas": "Jaimini Chara Karaka significator evidence for the selected topic.",
    "jaimini.chara_dasha": "Jaimini Chara Dasha sign-period and antardasha timing evidence.",
    "nadi.linkages": "Available Nadi linkage evidence.",
    "nakshatra.topic_links": "Available nakshatra and dispositorship evidence.",
    "kp.cusp_significators": "Available KP cusp and significator evidence.",
}


from chat.calculator_menu import EXTRA_CALCULATORS, CalculatorParameters, run_calculator
LEGACY_CAPABILITIES = tuple(CAPABILITY_REGISTRY)
CAPABILITY_REGISTRY.update(EXTRA_CALCULATORS)


_PARASHARI_EVIDENCE_DENSITY_CONTRACT = """
PARASHARI EVIDENCE DENSITY CONTRACT:
The heading `#### The Parashari View` must be a technical evidence section, not a
one-paragraph summary. When the supplied calculations support them, present the
following as clearly separated bold evidence blocks or short numbered blocks:
1. **Natal promise and mechanism** — relevant topic houses, their lords,
   occupants, aspects, dispositors and explicit D1 connections.
2. **Dasha hierarchy** — name the applicable Mahadasha, Antardasha and available
   lower period(s), their exact dates when supplied, and explain each period's
   delivery mechanism through natal lordship/placement. For past-event questions,
   use the historical MD/AD timeline rather than only a current snapshot.
3. **Strength and delivery quality** — relevant Shadbala, avastha, dignity,
   Panchadha Maitri/friendship, combustion, retrogression or other computed
   condition; state how it modifies delivery rather than merely listing it.
4. **Divisional confirmation** — use the relevant supplied divisional chart(s),
   especially D9 and the topic varga such as D10, D7 or D30. Give the actual
   supporting or conflicting placement and what it confirms.
5. **Special points and constraints** — include Yogi/Avayogi, Badhaka, Maraka,
   Tithi Dagdha, or comparable special-point evidence when calculated and
   relevant. Keep each effect distinct; never collapse it into generic weakness.

Use at least three applicable blocks whenever the packet contains evidence for
them. Do not create placeholder blocks or invent facts when a layer is not
relevant. For career/business questions, explicitly distinguish aptitude,
field/domain, work function, status/visibility, and timing when the evidence
supports those distinctions. A later school heading must not replace this
Parashari explanation.
""".strip()


def redact_verified_internal_transport(text: Any) -> str:
    """Remove internal delivery language if it slips into a user-facing reading.

    The writer is instructed not to discuss packets, branches, or what the
    backend did not send.  This small final guard handles common phrasing
    without changing any astrological claim or date.
    """
    value = str(text or "")
    value = re.sub(
        r"\bthe\s+(?:supplied|provided)\s+([A-Za-z][A-Za-z -]{0,70}?)\s+branch\s+"
        r"(gives|shows|indicates|notes)\b",
        lambda match: f"The {match.group(1).strip()} analysis {match.group(2)}",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\bthe\s+([A-Za-z][A-Za-z -]{0,70}?)\s+branch\b",
        lambda match: f"{match.group(1).strip()} analysis",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\b(?:the\s+)?(?:supplied|provided)\s+(?:data|json|packet|calculations?)\s+"
        r"(says?|shows?|indicates?|notes?)\b",
        lambda match: f"The chart {match.group(1)}",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\b(?:was|were|is|are)\s+not\s+(?:independently\s+)?(?:supplied|provided)\b",
        "is not established in this reading",
        value,
        flags=re.IGNORECASE,
    )
    # This is the final response persisted and returned to every client.
    # Collapsing whitespace here also collapses Markdown section boundaries,
    # paragraphs and ranked choices, even when the writer formatted them correctly.
    return value.strip()


def _compact_visible_calculation_summary(value: Any, limit: int = 260) -> str:
    """Keep a live calculation update readable without cutting a word mid-stream."""
    summary = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(summary) <= limit:
        return summary
    # Prefer a complete sentence that fits.  A word-boundary fallback is still
    # explicit about truncation instead of looking like a broken live stream.
    sentence_ends = [match.end() for match in re.finditer(r"[.!?](?=\s|$)", summary[:limit])]
    if sentence_ends:
        return summary[:sentence_ends[-1]].strip()
    word_end = summary.rfind(" ", 0, limit)
    return f"{summary[:word_end if word_end > 40 else limit].rstrip()}…"


def _json_limit(value: Any, limit: int = 14000) -> Any:
    """Keep the reviewer deterministic-context payload bounded and valid JSON."""
    encoded = json.dumps(value, ensure_ascii=False, default=str)
    if len(encoded) <= limit:
        return value
    return {"truncated": True, "preview": encoded[:limit]}


def _find_named_values(value: Any, names: set[str], found: Dict[str, Any]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in names and lowered not in found and child not in (None, {}, []):
                found[lowered] = child
            _find_named_values(child, names, found)
    elif isinstance(value, list):
        for child in value:
            _find_named_values(child, names, found)


def _capability_payloads(instant_context: Dict[str, Any]) -> Dict[str, Any]:
    """Expose only computed evidence, never model-invented calculator output."""
    evidence = instant_context.get("normalized_evidence") if isinstance(instant_context.get("normalized_evidence"), dict) else {}
    parashari = instant_context.get("instant_parashari") if isinstance(instant_context.get("instant_parashari"), dict) else {}
    named: Dict[str, Any] = {}
    _find_named_values(instant_context, {
        "nadi_evidence", "jaimini", "jaimini_evidence", "kp_evidence", "nakshatra_foundation",
        "divisional_specifics", "divisional_support", "yogi_avayogi", "special_point_evidence",
        "planetary_dignities", "shadbala",
    }, named)
    return {
        "parashari.natal_foundation": _json_limit({"natal_snapshot": instant_context.get("natal_snapshot"), "topic_evidence": evidence.get("topic_confirmation") or parashari.get("natal_promise")}),
        "parashari.dasha_timing": _json_limit({"current_dashas": instant_context.get("current_dashas"), "timing": evidence.get("event_timing_verdict") or evidence.get("current_timing")}),
        "parashari.transit_activation": _json_limit({"current_transits": instant_context.get("current_transits"), "transit": evidence.get("transit_confirmation") or evidence.get("transit_anchor_rows")}),
        "parashari.divisional_confirmation": _json_limit(named.get("divisional_specifics") or named.get("divisional_support")),
        "parashari.dignity_and_special_points": _json_limit({key: value for key, value in named.items() if key in {"yogi_avayogi", "special_point_evidence", "planetary_dignities", "shadbala"}}),
        "jaimini.significators_and_arudhas": _json_limit(named.get("jaimini") or named.get("jaimini_evidence")),
        "nadi.linkages": _json_limit(named.get("nadi_evidence")),
        "nakshatra.topic_links": _json_limit(named.get("nakshatra_foundation")),
        "kp.cusp_significators": _json_limit(named.get("kp_evidence")),
    }


_GENERATION_CONTROL_KEYS = {
    "answer_contract", "response_contract", "claim_contract", "composer_brief",
    "recommended_answer", "required_visible_conclusion", "required_answer_points",
    "forbidden_answer_moves", "follow_up_prompts", "next_action", "caution",
    "instant_v2_answer_contract", "knowledge_graph_policy", "verdict",
    "ranked_windows", "ranking", "answer_rules", "response_rules",
}
_PACKET_NOISE_KEYS = {
    "source", "sources", "methodology", "calculation_method", "calculation_notes",
    "documentation", "citation", "citations", "rule", "rules",
}


def _raw_calculations(value: Any) -> Any:
    """Remove derived-answer controls while preserving calculator results.

    Some Instant data structures contain both source calculations and a
    pre-computed conclusion.  Verified Chat can use the former, but feeding it
    the latter turns Luna into a renderer instead of an analyst.
    """
    if isinstance(value, dict):
        return {
            key: _raw_calculations(child)
            for key, child in value.items()
            if (
                str(key).strip().lower() not in _GENERATION_CONTROL_KEYS
                and str(key).strip().lower() not in _PACKET_NOISE_KEYS
                and not str(key).strip().lower().endswith("_verdict")
                and not str(key).strip().lower().startswith("ranked_")
            )
        }
    if isinstance(value, list):
        return [_raw_calculations(child) for child in value]
    return value


_SIGN_INDEXED_BAV_KEYS = frozenset({
    "bav", "bhinnashtakavarga", "individual_charts", "lagna_bav",
    "bav_by_sign", "bav_signwise", "bav_sign_wise",
})


def _without_sign_indexed_bav(value: Any) -> Any:
    """Remove unsafe raw BAV rows from the baseline seen before the BAV tool.

    Calculator rows use Aries-to-Pisces indexes. A language model can correctly
    reason over those as signs, but it must never be offered them beside a
    house-reading task: it may mistake index zero for House 1. The dedicated
    Ashtakavarga capability supplies a single house-mapped BAV representation.
    """
    if isinstance(value, dict):
        return {
            key: _without_sign_indexed_bav(child)
            for key, child in value.items()
            if str(key).strip().lower().replace("-", "_").replace(" ", "_")
            not in _SIGN_INDEXED_BAV_KEYS
        }
    if isinstance(value, list):
        return [_without_sign_indexed_bav(child) for child in value]
    return value


def build_verified_baseline(instant_context: Dict[str, Any]) -> Dict[str, Any]:
    """Create a raw evidence packet, never an Instant composer packet."""
    intent = instant_context.get("intent_summary") or {}
    parashari = _without_sign_indexed_bav(
        _raw_calculations(instant_context.get("instant_parashari") or {})
    )
    topic = _without_sign_indexed_bav(
        _raw_calculations(instant_context.get("normalized_evidence") or {})
    )

    # Send every calculated Instant fact after removing only renderer controls,
    # conclusions, and documentation noise. The agent decides whether it is
    # sufficient; compacting this baseline would recreate the earlier failure
    # where Luna concluded that a historical timing input did not exist.
    parashari_raw = parashari
    topic_raw = topic
    return {
        "calculation_packet_version": "verified-raw-calculations-v2",
        "daily_calculations": _raw_calculations(instant_context.get("daily_prediction_spine") or {}),
        "question_scope": {
            "category": intent.get("category"),
            "mode": _verified_presentation_mode(instant_context),
            "period_window": intent.get("period_window"),
            "answer_mode": intent.get("answer_mode"),
            "time_relation": intent.get("time_relation"),
            "target_subject": intent.get("target_subject"),
            "focus_houses": intent.get("focus_houses"),
        },
        "natal_calculations": _without_sign_indexed_bav(
            _raw_calculations(instant_context.get("natal_snapshot"))
        ),
        "dasha_calculations": _without_sign_indexed_bav(
            _raw_calculations(instant_context.get("current_dashas"))
        ),
        "transit_calculations": _without_sign_indexed_bav(
            _raw_calculations(instant_context.get("current_transits"))
        ),
        "parashari_calculations": parashari_raw,
        "topic_calculations": topic_raw,
    }


def _historical_vimshottari_timeline(birth_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return the calculated MD/AD timeline without an event conclusion."""
    from shared.dasha_calculator import DashaCalculator

    try:
        calculator = DashaCalculator()
        dashas = calculator.calculate_current_dashas(birth_data, strict=True)
        periods = []
        for maha in dashas.get("maha_dashas") or []:
            if not isinstance(maha, dict) or not maha.get("planet"):
                continue
            maha_row = {
                "mahadasha": str(maha.get("planet")),
                "start": str(maha.get("start"))[:10],
                "end": str(maha.get("end"))[:10],
                "antardashas": [],
            }
            for antar in calculator.list_antardashas(maha):
                if isinstance(antar, dict) and antar.get("planet"):
                    maha_row["antardashas"].append({
                        "antardasha": str(antar.get("planet")),
                        "start": str(antar.get("start"))[:10],
                        "end": str(antar.get("end"))[:10],
                    })
            periods.append(maha_row)
        return {"mahadasha_periods": periods}
    except Exception:
        return {}


def _verified_ashtakavarga_payload(ashtakavarga: Any, chart: Dict[str, Any]) -> Dict[str, Any]:
    """Make the SAV/BAV house mapping explicit for a language-model consumer.

    ``AshtakavargaCalculator`` returns raw points keyed by zodiac sign, where
    zero is Aries. Those values are correct but are unsafe to cite as house
    values unless they are rotated from the actual ascendant. Keeping raw
    sign rows as the only representation let the model read Aries as house 1,
    which shifted every SAV/BAV value for almost every chart.
    """
    sign_names = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    sarva = ashtakavarga.calculate_sarvashtakavarga()
    raw_sav = sarva.get("sarvashtakavarga") if isinstance(sarva, dict) else {}
    individual = sarva.get("individual_charts") if isinstance(sarva, dict) else {}
    try:
        ascendant_sign = int(float(chart.get("ascendant")) // 30) % 12
    except (TypeError, ValueError):
        ascendant_sign = 0

    houses: Dict[str, Dict[str, Any]] = {}
    for house in range(1, 13):
        sign = (ascendant_sign + house - 1) % 12
        bav: Dict[str, int] = {}
        for planet, row in (individual or {}).items():
            bindus = row.get("bindus") if isinstance(row, dict) else {}
            value = bindus.get(sign, bindus.get(str(sign))) if isinstance(bindus, dict) else None
            if value is not None:
                bav[str(planet)] = int(value)
        sav_value = raw_sav.get(str(sign), raw_sav.get(sign)) if isinstance(raw_sav, dict) else None
        houses[str(house)] = {
            "sign_id": sign,
            "sign": sign_names[sign],
            "sav": int(sav_value) if sav_value is not None else None,
            "bav": bav,
        }

    advanced = ashtakavarga.calculate_advanced_ashtakavarga()
    shodhya = advanced.get("shodhya_pinda") if isinstance(advanced, dict) else {}
    advanced_summary = {
        "convention": advanced.get("convention") if isinstance(advanced, dict) else {},
        "natal_kakshya": advanced.get("natal_kakshya") if isinstance(advanced, dict) else {},
        "shodhya_pinda": {
            str(planet): {
                "shodhya_pinda": row.get("shodhya_pinda"),
                "rashi_pinda": row.get("rashi_pinda"),
                "graha_pinda": row.get("graha_pinda"),
            }
            for planet, row in (shodhya or {}).items()
            if isinstance(row, dict)
        },
    }

    return {
        "schema_version": "verified.ashtakavarga.house-mapped.v2",
        "citation_rule": (
            "For any house claim, cite only houses[house_number].sav and "
            "houses[house_number].bav[planet]. Raw BAV sign-order rows are deliberately omitted "
            "and must never be inferred from a sign index."
        ),
        "ascendant_sign_id": ascendant_sign,
        "ascendant_sign": sign_names[ascendant_sign],
        "houses": houses,
        "raw_sign_order": {
            "meaning": "Aries through Pisces; SAV values only, never use positions as house numbers.",
            "signs": sign_names,
            "sav": raw_sav,
        },
        "total_bindus": sarva.get("total_bindus") if isinstance(sarva, dict) else None,
        # Prastara contributor matrices are retained by the calculator but are
        # intentionally not put in this response: they make the tool output
        # exceed its transport cap and previously truncated the exact SAV/BAV
        # values above into an unusable preview string.
        "advanced_summary": advanced_summary,
    }


def _calculate_requested_capabilities(
    birth_data: Dict[str, Any], requested: List[str], baseline: Dict[str, Any], instant_context: Dict[str, Any], parameters=None
) -> Dict[str, Any]:
    """One bounded deterministic augmentation pass for registered IDs only."""
    if not requested:
        return {}
    if parameters:
        parsed_parameters = CalculatorParameters.model_validate(parameters)
        if parsed_parameters.topic:
            instant_context = {**instant_context, 'intent_summary': {
                **(instant_context.get('intent_summary') or {}), 'category': parsed_parameters.topic}}
    extra = {c: run_calculator(c, birth_data, parameters) for c in requested if c in EXTRA_CALCULATORS}
    requested = [c for c in requested if c not in EXTRA_CALCULATORS]
    if not requested:
        return extra
    # Imports stay local so the question router remains small and does not
    # create an import cycle with Instant Chat.
    from types import SimpleNamespace
    from calculators.chart_calculator import ChartCalculator
    from calculators.divisional_chart_calculator import DivisionalChartCalculator
    from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
    from calculators.ashtakavarga import AshtakavargaCalculator
    from calculators.shadbala_calculator import ShadbalaCalculator
    from calculators.yogi_calculator import YogiCalculator
    from calculators.friendship_calculator import FriendshipCalculator
    from calculators.chara_dasha_calculator import CharaDashaCalculator
    from datetime import datetime
    from instant_chat_v2.nakshatra_calculation import build_nakshatra_foundation
    from chat.instant_chat_pipeline import (
        _instant_real_karaka_evidence,
        _instant_real_kp_evidence,
        _instant_real_nadi_evidence,
    )

    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth_data))
    output: Dict[str, Any] = {}
    if "parashari.dignity_and_special_points" in requested:
        output["parashari.dignity_and_special_points"] = _json_limit({
            "dignities": PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities(),
            "yogi_points": YogiCalculator(chart).calculate_yogi_points(birth_data),
        }, 30000)
    if "parashari.ashtakavarga" in requested:
        ashtakavarga = AshtakavargaCalculator(dict(birth_data), chart)
        output["parashari.ashtakavarga"] = _json_limit(
            _verified_ashtakavarga_payload(ashtakavarga, chart), 30000
        )
    if "parashari.shadbala" in requested:
        output["parashari.shadbala"] = _json_limit(
            ShadbalaCalculator(chart, dict(birth_data)).calculate_shadbala(), 30000
        )
    if "parashari.panchadha_maitri" in requested:
        output["parashari.panchadha_maitri"] = _json_limit(
            FriendshipCalculator().calculate_friendship(dict(birth_data)), 20000
        )
    if "parashari.divisional_confirmation" in requested:
        category = str((instant_context.get("intent_summary") or {}).get("category") or "").lower()
        topic_divisions = {
            "marriage": (("D9", 9),),
            "relationship": (("D9", 9),),
            "love": (("D9", 9),),
            "career": (("D10", 10),),
            "job": (("D10", 10),),
            "business": (("D10", 10),),
            "children": (("D7", 7),),
            "property": (("D4", 4),),
        }
        selected_divisions = topic_divisions.get(category, (("D9", 9), ("D10", 10)))
        if parameters:
            requested_parameters = CalculatorParameters.model_validate(parameters)
            if requested_parameters.divisions:
                selected_divisions = [(f'D{n}', n) for n in requested_parameters.divisions]
        divisions = DivisionalChartCalculator(chart)
        output["parashari.divisional_confirmation"] = _json_limit({
            code: divisions.calculate_divisional_chart(number)
            for code, number in selected_divisions
        })
    if "jaimini.significators_and_arudhas" in requested:
        output["jaimini.significators_and_arudhas"] = _json_limit(_instant_real_karaka_evidence(chart))
    if "jaimini.chara_dasha" in requested:
        dob = datetime.strptime(str(birth_data["date"]), "%Y-%m-%d")
        output["jaimini.chara_dasha"] = _json_limit(
            CharaDashaCalculator(dict(chart)).calculate_dasha(dob, focus_date=datetime.now()),
            30000,
        )
    if "nadi.linkages" in requested:
        output["nadi.linkages"] = _json_limit(_instant_real_nadi_evidence(chart))
    if "kp.cusp_significators" in requested:
        output["kp.cusp_significators"] = _json_limit(_instant_real_kp_evidence(birth_data))
    if "nakshatra.topic_links" in requested:
        intent = instant_context.get("intent_summary") if isinstance(instant_context.get("intent_summary"), dict) else {}
        output["nakshatra.topic_links"] = _json_limit(build_nakshatra_foundation(
            chart_data=chart,
            normalized_evidence=instant_context.get("normalized_evidence") or {},
            subtype=intent.get("nakshatra_subtype"),
            target_planet=intent.get("nakshatra_target_planet"),
            topic=intent.get("category") or "general",
            current_transits=instant_context.get("current_transits") or {},
        ))
    # These are already deterministically generated by the selected Instant
    # baseline. Reusing the exact calculated values avoids a second, divergent
    # timing calculation.
    for capability in (
        "parashari.natal_foundation", "parashari.dasha_timing", "parashari.transit_activation",
    ):
        if capability in requested and baseline.get(capability) not in (None, {}, []):
            output[capability] = baseline[capability]
    return {**output, **extra}


def _response_usage(response: Any) -> Dict[str, int]:
    """Normalize Responses API usage without relying on SDK model classes."""
    usage = getattr(response, "usage", None)
    details = getattr(usage, "input_tokens_details", None)
    return {
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "cached_tokens": int(getattr(details, "cached_tokens", 0) or 0),
    }


def _add_usage(total: Dict[str, int], response: Any) -> None:
    for key, value in _response_usage(response).items():
        total[key] = int(total.get(key, 0) or 0) + value


def _function_calls(response: Any) -> List[Any]:
    return [
        item for item in (getattr(response, "output", None) or [])
        if getattr(item, "type", None) == "function_call"
    ]


def _verified_emphasis_instruction() -> str:
    return """IMPORTANT TEXT EMPHASIS (mandatory for Simple and Technical answers):
Use Markdown **bold** throughout the answer to make its important points easy to scan,
not only in headings. Bold the main conclusion in the opening, the leading recommendation
or ranked option, important supported dates or timing windows, the core reason a conclusion
follows, and material cautions or qualifications. In each substantive section, emphasize
one or two short key phrases when there is a clear takeaway. For a brief answer, bold its
central takeaway. Examples of formatting: **the strongest option**, **September to November**,
**progress may require patience**. These are formatting examples, not facts to copy.
Keep connective prose normal weight. Never bold entire paragraphs, every sentence, or
routine planet names merely because they are technical terms. Bold uncertainty together
with the conclusion it qualifies; do not make tentative evidence look certain. Preserve
all existing headings, lists and sentiment spans. Keep sentiment-span contents plain text:
apply bold to other key phrases rather than nesting Markdown inside sentiment spans.
Before sending, check that the answer contains meaningful inline **bold** emphasis in
its opening and major takeaways, rather than leaving the whole body at one visual weight."""


def _verified_sentiment_instruction() -> str:
    return """Sentiment highlighting is an intentional exception to the HTML restriction: wrap short,
evidence-grounded favorable phrases in
<span class="chat-sentiment-positive">...</span> and short cautions, delays, risks, or
conflicts in <span class="chat-sentiment-negative">...</span>. These render green and red
in chat. Use plain text inside each span, tag clauses rather than whole sections, and use a
positive and/or negative tag whenever the deterministic evidence supports it. Never create a
sentiment tag merely to make the answer look balanced. Before finalizing, check the visible
answer: if you state a support/opportunity, it must have at least one positive span; if you
state a caution/delay/risk, it must have at least one negative span. Do not leave eligible
sentiment as untagged plain text."""


def _verified_presentation_mode(instant_context):
    """Exact-day scope wins over stale broad-event presentation metadata."""
    intent = instant_context.get('intent_summary') or {}
    window = intent.get('period_window') or {}
    plan = instant_context.get('query_plan') or {}
    mode = str(intent.get('mode') or 'DEFAULT').upper()
    # A specifically routed event on one date is not an overall daily outlook.
    if mode == 'PREDICT_EVENT_TIMING' and plan.get('forecast_shape') != 'daily_forecast':
        return mode
    if mode == 'PREDICT_DAILY' or str(window.get('kind') or '').lower() == 'day' or plan.get('forecast_shape') == 'daily_forecast':
        return 'PREDICT_DAILY'
    if mode == 'DEFAULT' and intent.get('answer_mode') == 'event_prediction':
        return 'PREDICT_EVENT_TIMING'
    return mode


def _premium_writer_system(
    intent_mode: str,
    language: str,
    native_name: str = "",
    response_style: str = "technical",
) -> str:
    from ai.output_schema import get_response_schema_for_mode
    from ai.parallel_chat.presentation_style import (
        build_simple_final_precedence_block,
        normalize_merge_response_style,
    )

    presentation_style = normalize_merge_response_style(response_style)
    if presentation_style == "simple":
        evidence_density_contract = """SIMPLE EVIDENCE REQUIREMENT:
Inspect the same deterministic evidence required for a Technical answer, including
the natal promise, timing, divisional confirmation, strengths and special points
when relevant. Preserve every supported conclusion, timing window, caution and
uncertainty. Translate the evidence into clear everyday language in the visible
answer; do not expose chart codes, numbered houses, dasha abbreviations, dignity
labels, bindu counts, or method-by-method sections."""
        evidence_depth_instruction = """These are internal evidence requirements. Preserve their
supported conclusions and timing, but translate them into the Simple visible answer rather than
creating a detailed Parashari or other method section."""
        response_start_instruction = "Start the direct answer immediately after this sentence; do not add a Quick Answer heading or technical preamble."
        output_presentation_instruction = (
            "STANDARD SIMPLE OUTPUT CONTRACT:\n"
            + build_simple_final_precedence_block("simple", premium_analysis=True)
        )
        sentiment_instruction = """SIMPLE OUTPUT MARKUP RULE: Use short Markdown `##` section headings
and deliberate `**bold**` emphasis for important phrases and conclusions. Sentiment spans
are the only permitted HTML exception. Do not emit cards, XML,
POS_START/POS_END/NEG_START/NEG_END markers, or any other presentation token. The final
user message supplies the exact Standard Simple layout."""
    else:
        evidence_density_contract = (
            "DAILY EVIDENCE: Explain the requested day's short-period and fast-transit triggers, "
            "connecting each supported factor to practical events. Broad natal factors are background."
            if str(intent_mode).upper() == 'PREDICT_DAILY' else _PARASHARI_EVIDENCE_DENSITY_CONTRACT
        )
        evidence_depth_instruction = """These are evidence requirements for a detailed Parashari
section; do not request a capability only when it is genuinely unrelated to the user's question."""
        response_start_instruction = "Start the Quick Answer immediately after this sentence; do not add any other preamble."
        premium_output_format = get_response_schema_for_mode(intent_mode, premium_analysis=True)
        output_presentation_instruction = f"""Use the following Premium Chat output format exactly. It is a
presentation contract only, not evidence or a requested conclusion. The permitted HTML card
elements in that contract are intentional. Do not add CSS, XML, internal implementation details,
or other HTML.

PREMIUM OUTPUT FORMAT:
{premium_output_format}

{_verified_emphasis_instruction()}"""
        sentiment_instruction = ""
    if str(intent_mode).upper() == 'PREDICT_DAILY':
        from chat.verified_daily import daily_contract
        output_presentation_instruction = daily_contract(presentation_style)
        evidence_density_contract = 'DAILY EVIDENCE REQUIREMENT: Panchang and Navatara are mandatory; connect all relevant day-specific facts to their practical meaning.'
        evidence_depth_instruction = 'Keep the complete daily breadth; specialist evidence is optional according to relevance.'
        response_start_instruction = 'Start the direct daily answer immediately after the greeting, with the requested date.'
    from chat.verified_event_timing import EVENT_TIMING_MODES, event_timing_contract
    if str(intent_mode).upper() in EVENT_TIMING_MODES:
        output_presentation_instruction = event_timing_contract(presentation_style)
        evidence_density_contract = 'EVENT EVIDENCE: Explain event promise, activation, realization and obstacles with concrete reasons.'
        evidence_depth_instruction = 'Use the approved event-focused Dive Deep sections only where relevant.'
        response_start_instruction = 'Start the direct event answer immediately after the greeting, with the strongest supported outcome and timing.'
    sentiment_instruction += "\n\n" + _verified_sentiment_instruction() + "\n\n" + _verified_emphasis_instruction()
    calculation_depth_requirement = (
        'For a daily reading, inspect the mandatory daily foundations and request additional systems only when relevant. '
        'Do not require a divisional, Shadbala or Ashtakavarga report for every ordinary day.'
        if str(intent_mode).upper() == 'PREDICT_DAILY' else """For any non-trivial chart reading, do not stop after the Instant baseline. Before the final
answer, inspect `parashari.divisional_confirmation` and
`parashari.dignity_and_special_points` when they return evidence. For timing, career, business,
marriage, health, or other consequential questions, also inspect the relevant available
`parashari.shadbala`, `parashari.panchadha_maitri`, and `parashari.ashtakavarga` calculations.
"""
    )
    if str(intent_mode).upper() in EVENT_TIMING_MODES:
        calculation_depth_requirement = 'Inspect the event evidence checklist in the approved contract. Choose additional systems by relevance; do not force every strength or specialist report.'
    display_name = str(native_name or "").strip()[:80]
    greeting_subject = f"the chart of {display_name}" if display_name else "the user's chart"
    return (
        f"""You are Verified Chat, a rigorous Vedic astrology assistant. Analyze only the
raw deterministic calculator results supplied through tools and reach your own conclusion.
Use the systems relevant to the question: Parashari, divisional charts, Jaimini, Nadi,
Nakshatra, KP, Ashtakavarga, Shadbala and Panchadha Maitri. Resolve agreement and conflict
honestly. Do not invent chart facts.

After the Instant baseline, you may request these deterministic calculators exactly by their
registered capability ID. Request as many relevant calculators as needed, including several in one round.
The deterministic baseline is a starting point, not a restriction on which systems to examine.
Every menu description states required parameters; supply them in parameters. Never guess missing
dates, houses, event type or location. If a calculation cannot run, state the limitation rather than inventing its result.
Use exact date ranges for timing and house numbers 1–12; sign numbers are 1=Aries through 12=Pisces.
For topic-aware tools, parameters.topic can override the inferred topic for that calculation;
parameters.divisions can explicitly choose divisional charts instead of the inferred defaults.
Choose what the question needs; do not request a calculator merely to
mention its system:
{json.dumps(CAPABILITY_REGISTRY, ensure_ascii=False)}

After inspecting the Instant baseline or any calculator output, call report_calculation before
requesting further evidence or writing the answer. Its title and summary are shown live to the
user, so write both in {language}. State one or two concrete computed facts from that result,
such as a placement, period, strength, or exact timing window. Never describe model selection,
prompting, packets, or tools; never publish a generic process update.

{calculation_depth_requirement}
{evidence_depth_instruction}

Ashtakavarga rule: raw SAV rows are in zodiac-sign order, not house order. For a statement
about House N, use only the house-mapped `houses[N]` record supplied by
parashari.ashtakavarga. Cite its sign together with the number. Raw BAV rows are not supplied
at all: for every BAV statement, cite only `houses[N].bav[planet]`. Never infer a BAV house
value by indexing an Aries-to-Pisces row with a house number.

Jaimini rule: Never write a Jaimini analysis section, timing statement, or limitation about
Jaimini timing unless you have first called jaimini.chara_dasha and inspected its result. Chara
Karakas and Arudhas may support that analysis, but never substitute for Chara Dasha. Do not say
that Chara Dasha was unavailable, absent, or not supplied: it is a registered calculator.

Never tell the user that supplied data, a packet, or calculations are missing or incomplete.
If the calculated evidence cannot establish a conclusion, state the uncertainty plainly without
discussing internal transport or missing inputs. Internal gaps are recorded separately.

EVIDENCE PROVENANCE FIREWALL (mandatory): Never tell the user how the reading obtained,
transported, selected, received, lacked, or verified its evidence. Do not describe what an
analysis method, source, calculation, or other branch did or did not have available. This is a
semantic rule, not a banned-word list: ordinary words such as "provided" remain fine when they
refer to the user's real-life situation, rather than the evidence source. State astrological
limits directly. For example, say "the Sudarshana analysis indicates..." and "the reading
supports this wider period; finer sub-period dates remain uncertain," never "the supplied
Sudarshana branch gives..." or "a schedule was not independently supplied."

PERSONAL CONSULTATION OPENING (mandatory): Before the response format, write exactly one
short, warm greeting sentence in {language} that thanks the user for consulting AstroRoshni
about {greeting_subject}. Translate this naturally; never emit the English instruction verbatim.
It must be plain text, not a heading or card, and it must not introduce Tara, AI, a model, tools,
or an analysis process. Use the native's name at most once. {response_start_instruction}

DELIVERY LINE-BREAK RULE (all response styles): Every visible heading, card label, list item,
and explanatory paragraph must be on its own line. Put a blank line between sections. Never put
the body of a section on the same line as a Markdown heading or card label.

{evidence_density_contract}

{sentiment_instruction}

{output_presentation_instruction}"""
    )


def build_verified_conversation_context(history: List[Dict[str, Any]], intent: Dict[str, Any]) -> Dict[str, Any]:
    """Keep follow-up context separate from deterministic chart evidence."""
    turns = []
    for row in (history or [])[-6:]:
        if not isinstance(row, dict):
            continue
        question = re.sub(r"\s+", " ", str(row.get("question") or "")).strip()[:500]
        answer = re.sub(r"<[^>]+>", " ", str(row.get("response") or ""))
        answer = re.sub(r"\s+", " ", answer).strip()[:1200]
        if question or answer:
            turns.append({"question": question, "answer": answer})
    facts = intent.get("_session_extracted_context") if isinstance(intent, dict) else {}
    return {
        "recent_question_answer_pairs": turns,
        "confirmed_session_facts": facts if isinstance(facts, dict) else {},
        "rule": "Conversation context explains references and confirmed user facts. It is not astrological evidence and cannot override deterministic calculations.",
    }


def _verified_final_writer_instruction(response_style: str, intent_mode: str = "") -> str:
    """Put the visible-response contract in the final writer turn itself.

    Calculator turns need detailed analysis instructions, but they should not
    be allowed to bury the layout request before Luna writes the answer.
    """
    from ai.parallel_chat.presentation_style import normalize_merge_response_style

    from chat.verified_event_timing import EVENT_TIMING_MODES, event_timing_contract
    if str(intent_mode).upper() in EVENT_TIMING_MODES:
        return ('Write the final event timing answer now.\n\n'
                + event_timing_contract(normalize_merge_response_style(response_style))
                + '\n' + _verified_emphasis_instruction() + '\n' + _verified_sentiment_instruction())
    if str(intent_mode).upper() == 'PREDICT_DAILY':
        from chat.verified_daily import daily_contract
        return ('Write the final daily answer now, using the requested date and calculated daily evidence.\n\n'
                + daily_contract(normalize_merge_response_style(response_style)) + '\n' + _verified_emphasis_instruction()
                + '\n' + _verified_sentiment_instruction())
    if normalize_merge_response_style(response_style) != "simple":
        return "Write the final answer now using the deterministic evidence already supplied.\n\n" + _verified_emphasis_instruction()
    return """Write the final answer now using the deterministic evidence already supplied.

This is a Standard Simple response. Output only the user-facing answer. Use short Markdown
level-2 headings (`## Heading`) to create visible sections. Every heading must be on its own
line, followed by a blank line and its body. Sentiment spans described below are the only
permitted HTML exception. Do not use other HTML, cards, XML, POS/NEG markers,
implementation language, or any other Markdown structure besides `##` headings and optional
short `**bold**` emphasis for important phrases and conclusions.

Use this exact readable layout. Keep every heading and every paragraph on separate lines, with
a blank line between sections:

Thank the user for consulting AstroRoshni about their chart.

[Direct answer paragraph]

## [A short question-specific section label]
[The first detailed explanation or ranked choices. Put each rank, its title, and its explanation on separate lines.]

## [A short question-specific section label]
[The main astrological reasons in clear everyday language.]

## [Important qualification or caution]
[The qualification and its practical implication.]

## Timing
[Include this section only when timing is relevant.]

## Final verdict
[A direct practical recommendation.]

For a broad question, include at least four of these distinct content sections. Choose labels
that answer the actual question (for example, Best-fit fields, Why this direction fits, Important
qualification, Timing, or Final verdict). Do not join sections into one paragraph. Preserve the
same substantive depth and all relevant conclusions, dates, cautions, and practical implications
that a Standard Simple answer would contain.

DEPTH REQUIREMENT: For a broad decision, career, education, relationship, wealth, or health
reading, write a detailed answer of roughly 2,500 to 4,000 English characters when the evidence
supports that depth. Give each ranked option a short explanation, give the reasoning section at
least two substantial paragraphs, and give both the qualification and final verdict their own
substantive paragraph. Do not shorten the answer merely because the language is Simple.""" + "\n\n" + _verified_sentiment_instruction() + "\n\n" + _verified_emphasis_instruction()


async def run_verified_calculator_agent(
    *,
    question: str,
    language: str,
    birth_data: Dict[str, Any],
    instant_context: Dict[str, Any],
    history: List[Dict[str, Any]],
    model_name: str,
    timeout_s: float,
    response_style: str = "technical",
    stream_callback: Optional[Callable[[str, str], None]] = None,
    calculation_callback: Optional[Callable[[List[Dict[str, str]]], None]] = None,
) -> Dict[str, Any]:
    """Run the bounded Verified Chat calculator loop through Responses tools.

    Round one always supplies the selected Instant baseline. Luna may then ask
    for further named deterministic calculations until it has enough evidence.
    Each turn transports only the newest function outputs through the Responses
    chain; the final answer-only turn may stream to the client.
    """
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI SDK is required for Verified Chat") from exc

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    started = time.perf_counter()
    timeout_s = max(15.0, min(180.0, float(timeout_s)))
    baseline = build_verified_baseline(instant_context)
    conversation_context = build_verified_conversation_context(
        history,
        {
            **(instant_context.get("intent_summary") if isinstance(instant_context.get("intent_summary"), dict) else {}),
            "_session_extracted_context": instant_context.get("session_extracted_context"),
        },
    )
    baseline["historical_timing_evidence"] = {
        "vimshottari_md_ad_timeline": _historical_vimshottari_timeline(birth_data),
    }
    baseline_payloads = _capability_payloads(instant_context)
    try:
        max_calculator_rounds = int(os.getenv("VERIFIED_CHAT_MAX_CALCULATOR_ROUNDS", "8"))
    except (TypeError, ValueError):
        max_calculator_rounds = 8
    max_calculator_rounds = max(1, min(16, max_calculator_rounds))
    tool_events: List[Dict[str, Any]] = []
    information_rounds: List[Dict[str, Any]] = []
    model_calculations: List[Dict[str, str]] = []
    calculated: Dict[str, Any] = {}
    unavailable: List[Dict[str, str]] = []
    usage: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0}

    def trace() -> List[Dict[str, str]]:
        return list(model_calculations)

    async def publish_trace() -> None:
        if calculation_callback is not None:
            await asyncio.to_thread(calculation_callback, trace())

    tools = [
        {
            "type": "function",
            "name": "get_instant_baseline",
            "description": "Get the raw deterministic Instant baseline: natal chart, Vimshottari timing, transits, and topic evidence. Call this before assessing the answer.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_deterministic_evidence",
            "description": "Get one additional deterministic astrology calculation. Select only a registered capability ID after inspecting the Instant baseline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "capability_id": {
                        "type": "string",
                        "enum": list(CAPABILITY_REGISTRY),
                        "description": "The registered calculator to run.",
                    },
                    "parameters": {"anyOf": [CalculatorParameters.model_json_schema(), {"type": "null"}]},
                },
                "required": ["capability_id", "parameters"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "report_calculation",
                "description": "Publish one concise user-visible finding after inspecting a deterministic tool result. This is not the final answer. summary must be a single complete sentence, no newlines, no more than 220 characters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "enum": ["instant_baseline", *list(CAPABILITY_REGISTRY)]},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["source", "title", "summary"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ]
    # OpenAI strict tools require all nested properties, with nullable optionals.
    from chat.conflict_contract import strictify_schema
    tools = strictify_schema(tools)
    intent_mode = _verified_presentation_mode(instant_context)
    instructions = _premium_writer_system(
        intent_mode,
        language,
        native_name=str(birth_data.get("name") or ""),
        response_style=response_style,
    )
    from ai.gemini_chat_analyzer import resolve_openai_reasoning_effort
    effort = resolve_openai_reasoning_effort(model_name, "none")
    reasoning_kwargs = {"reasoning": {"effort": effort}} if effort else {}
    output_limit = 16384 if model_name.startswith("gpt-4") else 65536
    sent_chars = len(question) + len(instructions)
    client = AsyncOpenAI(api_key=api_key, timeout=timeout_s)

    async def create(**kwargs: Any) -> Any:
        remaining = max(1.0, timeout_s - (time.perf_counter() - started))
        return await asyncio.wait_for(client.responses.create(**kwargs), timeout=remaining)

    async def send_tool_outputs(response_id: str, outputs: List[Dict[str, str]], *, tool_choice: Any = "auto") -> Any:
        response = await create(
            model=model_name,
            instructions=instructions,
            previous_response_id=response_id,
            input=outputs,
            tools=tools,
            tool_choice=tool_choice,
            **reasoning_kwargs,
            max_output_tokens=output_limit,
        )
        _add_usage(usage, response)
        return response

    first = await create(
        model=model_name,
        instructions=instructions,
        input=(
            f"Answer the user's question in {language}. First inspect the deterministic Instant baseline, "
            f"then decide which additional calculators are necessary.\n\nQuestion: {question}\n\n"
            f"Conversation context (not chart evidence): {json.dumps(conversation_context, ensure_ascii=False, default=str)}"
        ),
        tools=tools,
        tool_choice={"type": "function", "name": "get_instant_baseline"},
        **reasoning_kwargs,
        max_output_tokens=4096,
    )
    _add_usage(usage, first)
    baseline_calls = _function_calls(first)
    if not baseline_calls:
        raise RuntimeError("verified_agent_did_not_request_baseline")
    if intent_mode == 'PREDICT_DAILY':
        from chat.verified_daily import daily_inputs
        from chat.calculator_menu import run_calculator
        try:
            daily_parameters, location_basis = daily_inputs(birth_data, instant_context)
            baseline['daily_location_basis'] = location_basis
            baseline['daily_required_calculations'] = {}
            for capability in ('election.navatara', 'election.panchang'):
                try:
                    result = await asyncio.to_thread(run_calculator, capability, birth_data, daily_parameters)
                    success = True
                    calculated[capability] = result
                    calculated[capability + ':' + json.dumps(daily_parameters, sort_keys=True)] = result
                except Exception:
                    result = {'error': 'calculation_unavailable', 'capability_id': capability}
                    success = False
                    unavailable.append({'code':'calculation_unavailable','capability_id':capability})
                baseline['daily_required_calculations'][capability] = result
                tool_events.append({'round':0,'tool':capability,'success':success})
                information_rounds.append({'round':0,'kind':'mandatory_daily_calculation','calculator':capability,
                    'requested':daily_parameters,'requested_by':'daily_contract','provided':result,'success':success})
        except ValueError:
            baseline['daily_required_calculations'] = {'clarification_required':'Ask for the requested date or location/timezone before a daily prediction.'}
    baseline_outputs = []
    for call in baseline_calls:
        tool_events.append({"round": 1, "tool": "get_instant_baseline", "success": True})
        baseline_outputs.append({
            "type": "function_call_output",
            "call_id": str(getattr(call, "call_id", "")),
            "output": json.dumps(baseline, ensure_ascii=False, default=str),
        })
        information_rounds.append({"round": 0, "kind": "baseline", "calculator": "get_instant_baseline",
            "requested": {}, "provided": json.loads(baseline_outputs[-1]["output"]), "success": True})
        sent_chars += len(baseline_outputs[-1]["output"])
    await publish_trace()

    async def calculate_tool_calls(calls: List[Any], calculator_round: int) -> List[Dict[str, str]]:
        nonlocal sent_chars
        outputs: List[Dict[str, str]] = []
        for call in calls:
            raw_args = str(getattr(call, "arguments", "") or "{}")
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {}
            capability = str(args.get("capability_id") or "")
            call_id = str(getattr(call, "call_id", ""))
            tool_name = str(getattr(call, "name", "") or "")
            if tool_name == "report_calculation":
                source = str(args.get("source") or "")
                title = _compact_visible_calculation_summary(args.get("title"), limit=90)
                summary = _compact_visible_calculation_summary(args.get("summary"), limit=260)
                if source in {"instant_baseline", *CAPABILITY_REGISTRY} and title and summary:
                    update_id = f"verified-calculation-{source}"
                    model_calculations[:] = [row for row in model_calculations if row.get("id") != update_id]
                    model_calculations.append({"id": update_id, "title": title, "detail": summary})
                    result = {"accepted": True}
                else:
                    result = {"accepted": False, "error": "invalid_calculation_update"}
                outputs.append({
                    "type": "function_call_output", "call_id": call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                })
                information_rounds.append({
                    "round": calculator_round, "kind": "progress_update",
                    "tool": "report_calculation", "requested": args,
                    "provided": result, "success": bool(result.get("accepted")),
                })
                continue
            if capability not in CAPABILITY_REGISTRY:
                result: Dict[str, Any] = {"error": "unavailable_calculator", "capability_id": capability}
                unavailable.append({"code": "unavailable_calculator", "capability_id": capability})
                tool_events.append({"round": calculator_round, "tool": capability or "invalid", "success": False})
            else:
                cache_key = capability + ":" + json.dumps(args.get("parameters") or {}, sort_keys=True)
                if cache_key not in calculated:
                    try:
                        result_map = await asyncio.to_thread(_calculate_requested_capabilities,
                            birth_data, [capability], baseline_payloads, instant_context, args.get("parameters"))
                        calculated[cache_key] = result_map.get(capability)
                    except Exception:
                        calculated[cache_key] = {"error": "invalid_or_unavailable_calculation", "requirements": CAPABILITY_REGISTRY[capability]}
                calculated[capability] = calculated.get(cache_key)
                result = calculated.get(capability)
                if result in (None, {}, []) or (isinstance(result, dict) and result.get("error")):
                    calculated.pop(cache_key, None)
                    result = {"error": "calculation_unavailable", "capability_id": capability}
                    unavailable.append({"code": "calculation_unavailable", "capability_id": capability})
                    tool_events.append({"round": calculator_round, "tool": capability, "success": False})
                else:
                    tool_events.append({"round": calculator_round, "tool": capability, "success": True})
            outputs.append({
                "type": "function_call_output", "call_id": call_id,
                "output": json.dumps(result, ensure_ascii=False, default=str),
            })
            information_rounds.append({"round": calculator_round, "kind": "calculation", "calculator": capability,
                "requested": args, "provided": json.loads(outputs[-1]["output"]),
                "success": not (isinstance(result, dict) and result.get("error"))})
            sent_chars += len(outputs[-1]["output"])
        await publish_trace()
        return outputs

    prior_response_id = str(getattr(first, "id", ""))
    pending_outputs = baseline_outputs
    calculator_rounds_used = 0
    for calculator_round in range(1, max_calculator_rounds + 1):
        decision = await send_tool_outputs(prior_response_id, pending_outputs)
        prior_response_id = str(getattr(decision, "id", ""))
        requested_calls = _function_calls(decision)
        if not requested_calls:
            pending_outputs = []
            break
        calculator_rounds_used = calculator_round
        pending_outputs = await calculate_tool_calls(requested_calls, calculator_round)

    final_input = list(pending_outputs or [])
    # Make the format request the final user-level instruction. Earlier
    # calculator/tool turns are intentionally detailed; without this turn,
    # their analysis requirements can drown out the Simple response shape.
    final_input.append({
        "type": "message",
        "role": "user",
        "content": [{
            "type": "input_text",
            "text": _verified_final_writer_instruction(response_style, intent_mode),
        }],
    })
    # This final turn writes only the response. If the round ceiling is reached,
    # its last calculator outputs are still supplied before tool use is disabled.
    remaining = max(1.0, timeout_s - (time.perf_counter() - started))
    stream = client.responses.stream(
        model=model_name,
        instructions=instructions,
        previous_response_id=prior_response_id,
        input=final_input,
        tools=tools,
        tool_choice="none",
        **reasoning_kwargs,
        max_output_tokens=output_limit,
    )
    parts: List[str] = []
    published = ""
    async with stream as events:
        async def consume() -> Any:
            nonlocal published
            async for event in events:
                if getattr(event, "type", None) != "response.output_text.delta":
                    continue
                delta = str(getattr(event, "delta", "") or "")
                if not delta:
                    continue
                parts.append(delta)
                full = "".join(parts)
                if stream_callback and (not published or len(full) - len(published) >= 48):
                    await asyncio.to_thread(stream_callback, full[len(published):], full)
                    published = full
            return await events.get_final_response()
        final_response = await asyncio.wait_for(consume(), timeout=remaining)
    _add_usage(usage, final_response)
    text = "".join(parts).strip() or str(getattr(final_response, "output_text", "") or "").strip()
    if stream_callback and text and text != published:
        await asyncio.to_thread(stream_callback, text[len(published):], text)
    if not text:
        raise RuntimeError("verified_agent_blank_final_answer")
    usage["non_cached_input_tokens"] = max(0, usage["input_tokens"] - usage["cached_tokens"])
    usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
    return {
        "success": True,
        "response": text,
        "chat_llm_model": model_name,
        "chat_llm_provider": CHAT_LLM_OPENAI,
        "token_usage": usage,
        "elapsed_s": max(0.0, time.perf_counter() - started),
        "prompt_chars": sent_chars,
        "information_rounds": {"type": "verified", "max_rounds": max_calculator_rounds, "events": information_rounds},
        "packet_validation": {
            "missing_capabilities": [],
            "calculated_capabilities": [c for c in calculated if c in CAPABILITY_REGISTRY],
            "unavailable_requirements": unavailable,
            "tool_events": tool_events,
            "calculation_trace": trace(),
            "calculator_rounds_used": calculator_rounds_used,
            "tool_round_limit": max_calculator_rounds,
        },
    }


async def build_verified_generation_request(
    analyzer: Any, *, question: str, language: str, birth_data: Dict[str, Any], instant_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Plan evidence, then prepare one independent Luna analysis call.

    The planning call may select deterministic calculators but may never make
    an astrological conclusion. The final Luna call remains the sole analyst.
    """
    baseline = build_verified_baseline(instant_context)
    baseline_available = {
        "natal_calculations": bool(baseline.get("natal_calculations")),
        "vimshottari_current_or_historical": bool(
            baseline.get("dasha_calculations")
            or ((baseline.get("parashari_calculations") or {}).get("historical_event_dasha_scan"))
        ),
        "transit_calculations": bool(
            baseline.get("transit_calculations")
            or ((baseline.get("parashari_calculations") or {}).get("major_transits"))
        ),
        "topic_calculations": bool(baseline.get("topic_calculations")),
    }
    planner_prompt = {
        "task": "Choose the deterministic evidence needed to answer the user's astrology question accurately. Do not answer the user, rank outcomes, or write analysis.",
        "question": question,
        "language": language,
        "baseline_available": baseline_available,
        "available_calculators": CAPABILITY_REGISTRY,
        "rules": [
            "Choose only IDs from available_calculators.",
            "For timing questions, explicitly assess dasha, transit activation, relevant divisional confirmation, Ashtakavarga, and Chara Dasha relevance.",
            "For a Jaimini timing claim, Chara Karakas alone are insufficient; request jaimini.chara_dasha when Jaimini timing is relevant.",
            "For a quantitative Ashtakavarga claim, request parashari.ashtakavarga.",
            "Return internal gaps in unavailable_requirements; do not ask the user a question.",
        ],
        "response_schema": {
            "required_capabilities": ["registered capability IDs"],
            "unavailable_requirements": ["data/calculation required but not in the registry"],
            "reason": "short",
        },
    }
    planner_started = time.perf_counter()
    planner = await analyzer.generate_text_from_prompt(
        json.dumps(planner_prompt, ensure_ascii=False),
        premium_analysis=False,
        model_name_override=get_verified_planner_model(),
        provider_override=CHAT_LLM_OPENAI,
        openai_reasoning_effort="none",
        llm_log_tag="verified_chat_evidence_planner",
        request_timeout_s=20.0,
        system_prompt="You are a deterministic evidence planner. Return JSON only; never answer the user.",
    )
    if not planner.get("success"):
        raise RuntimeError(str(planner.get("error") or "verified_evidence_planner_failed"))
    planner_decision = _json_object(str(planner.get("response") or ""))
    planner_requested = [
        str(capability) for capability in planner_decision.get("required_capabilities") or []
        if str(capability) in CAPABILITY_REGISTRY
    ]
    unavailable_requirements = [
        str(value)[:300] for value in planner_decision.get("unavailable_requirements") or []
        if str(value).strip()
    ][:12]
    historical_scan = (
        (baseline.get("parashari_calculations") or {}).get("historical_event_dasha_scan")
        if isinstance(baseline.get("parashari_calculations"), dict)
        else {}
    )
    if isinstance(baseline.get("parashari_calculations"), dict):
        baseline["parashari_calculations"].pop("historical_event_dasha_scan", None)
    capability_payloads = _capability_payloads(instant_context)
    # All existing supported systems are calculated before Luna sees the
    # packet.  This preserves a single fast writer call while ensuring that a
    # system cannot disappear merely because an earlier model did not ask for
    # it.
    supplemental_capabilities = [
        capability for capability in LEGACY_CAPABILITIES
        if capability not in {
            "parashari.natal_foundation",
            "parashari.dasha_timing",
            "parashari.transit_activation",
        }
    ]
    additional = _calculate_requested_capabilities(
        birth_data, supplemental_capabilities, capability_payloads, instant_context
    )
    expected_capabilities = list(LEGACY_CAPABILITIES)
    available_baseline = {
        "parashari.natal_foundation",
        "parashari.dasha_timing",
        "parashari.transit_activation",
    }
    missing_capabilities = [
        capability for capability in expected_capabilities
        if capability not in available_baseline and additional.get(capability) in (None, {}, [])
    ]
    raw_packet = {
        "packet_version": "verified-chat-raw-v2",
        "birth_summary": instant_context.get("birth_summary"),
        # This section is deliberately first. A retrospective route has no
        # current-period snapshot by design; its MD/AD timeline and calculated
        # past event candidates are the timing evidence for Luna to assess.
        "historical_timing_evidence": _raw_calculations({
            "vimshottari_md_ad_timeline": _historical_vimshottari_timeline(birth_data),
            "calculated_past_event_candidates": historical_scan,
        }),
        # Cross-system results come before the larger Instant-derived packet.
        # If an emergency payload limit is ever reached, a system must not
        # vanish merely because Parashari data happened to serialize first.
        "additional_calculations": _raw_calculations(additional),
        "baseline_calculations": baseline,
    }
    from ai.output_schema import get_response_schema_for_mode

    intent_mode = _verified_presentation_mode(instant_context)
    premium_output_format = get_response_schema_for_mode(
        intent_mode,
        premium_analysis=True,
    )
    writer_system = f"""You are Verified Chat, a rigorous Vedic astrology assistant. Analyze the supplied raw deterministic calculations yourself and reach your own conclusion. The packet contains no approved answer or ranking. For a past-timing question, use historical_timing_evidence; an empty current-period snapshot does not mean that historical dasha data is unavailable. Weigh Parashari, divisional, Jaimini, Nadi, Nakshatra, KP and Ashtakavarga evidence where it is relevant; do not mechanically force every system into the response. Resolve agreement and conflict honestly. Do not invent chart facts beyond the packet.

Never tell the user that the supplied data, packet, or calculations are missing or incomplete. If the calculated evidence cannot establish a conclusion, state the conclusion's uncertainty plainly without discussing the transport or missing internal inputs. Packet completeness is audited separately.

PERSONAL CONSULTATION OPENING (mandatory): Before the Premium output format, write exactly one
short, warm greeting sentence in {language} that thanks the user for consulting AstroRoshni
about the chart of {str(birth_data.get("name") or "the native")[:80]}. Translate this naturally;
never emit the English instruction verbatim. It must be plain text, not a heading or card, and
must not introduce Tara, AI, a model, tools, or an analysis process. Start the Quick Answer
immediately after this sentence; do not add any other preamble.

{_PARASHARI_EVIDENCE_DENSITY_CONTRACT}

Ashtakavarga rule: `raw_sign_order` contains SAV only and is zodiac-sign ordered. For every
BAV claim about House N, use only `additional_calculations.parashari.ashtakavarga.houses[N].bav[planet]`.
Raw BAV sign rows are intentionally absent; never reconstruct or infer a house BAV from sign indexes.

Use the following Premium Chat output format exactly. It is a presentation contract only: do not treat it as evidence or a requested conclusion. The permitted HTML card elements in that contract are intentional. Do not add CSS, XML, internal implementation details, or other HTML.

PREMIUM OUTPUT FORMAT:
{premium_output_format}

{_verified_emphasis_instruction()}"""
    writer_prompt = f"""Answer the user's question in {language}.

Question: {question}

Raw deterministic calculation packet:
{json.dumps(_json_limit(raw_packet, 250000), ensure_ascii=False, default=str)}"""
    return {
        "system_prompt": writer_system,
        "user_prompt": writer_prompt,
        "review": {
            "strategy": "complete_raw_packet",
            "calculated_capabilities": expected_capabilities,
            "planner_requested_capabilities": planner_requested,
            "planner_reason": str(planner_decision.get("reason") or ""),
        },
        "review_usage": {
            "model": planner.get("chat_llm_model") or get_verified_planner_model(),
            "provider": planner.get("chat_llm_provider") or CHAT_LLM_OPENAI,
            "token_usage": planner.get("token_usage") or {},
            "prompt_chars": len(json.dumps(planner_prompt, ensure_ascii=False)),
            "response_chars": len(str(planner.get("response") or "")),
            "elapsed_s": max(0.0, time.perf_counter() - planner_started),
        },
        "packet_validation": {
            "missing_capabilities": missing_capabilities,
            "calculated_capabilities": expected_capabilities,
            "planner_requested_capabilities": planner_requested,
            "unavailable_requirements": unavailable_requirements,
        },
        "global_context_version": "verified-chat-v2",
        "user_context_version": "natal-v1",
    }


def _json_object(raw: str) -> Dict[str, Any]:
    text = str(raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except Exception:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            value = json.loads(match.group(0))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}


def _mode_to_intent_mode(answer_mode: str) -> str:
    return {
        "event_prediction": "PREDICT_EVENT_TIMING",
        "timing_window": "PREDICT_PERIOD_OUTLOOK",
        "potential_capacity": "ANALYZE_TOPIC_POTENTIAL",
        "location_recommendation": "RECOMMEND_LOCATION",
        "remedy_action": "RECOMMEND_REMEDY_FOR_PROBLEM",
    }.get(answer_mode, "ANALYZE_TOPIC")


async def classify_verified_question(
    analyzer: Any,
    *,
    question: str,
    history: List[Dict[str, Any]],
    language: str,
    query_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    from utils.query_context import resolve_query_now
    now_local = resolve_query_now(query_context)
    recent = [
        {"question": str(row.get("question") or "")[:600],
         "response": re.sub(r"<[^>]+>", " ", str(row.get("response") or ""))[:600]}
        for row in (history or [])[-2:]
        if isinstance(row, dict) and str(row.get("question") or "").strip()
    ]
    prompt = f"""
Classify one astrology chat question. Do not answer it and do not use astrology knowledge to infer chart facts.
Return JSON only.

Choose one answer_mode from: {json.dumps(ANSWER_MODES)}.
Choose one category from: {json.dumps(_CATEGORY_VALUES)}.
Choose target_subject_key from: {json.dumps(sorted(TARGET_SUBJECTS))}.

route_action is answer, clarify, handoff, ack, or out_of_scope. Use clarify only for a material missing fact.
Use handoff for two-person compatibility. Use ack for greetings, thanks, or no question.
Use out_of_scope for a question that is not about astrology or the user's chart (for example,
asking what AI/model you are, general knowledge, writing, coding, or translation). Put one
short boundary in user_message in the user's language: say this chat answers astrology questions.
`answer_mode` must always be one of the listed values, even when route_action is ack, handoff,
or out_of_scope. Use topic_reading as the harmless placeholder answer_mode for those actions.
Never classify a question about resignation, an offer, joining, career timing, marriage timing,
or any other life-event timing as out_of_scope merely because it is phrased as a follow-up.
If its earlier subject is genuinely unavailable from RECENT CONVERSATION, use route_action clarify
and ask one short question that identifies the life event; keep answer_mode topic_reading.
Clarification replies such as "both together", "yes", or "the first one" must be interpreted with
RECENT CONVERSATION, including the assistant's clarification. Do not ask what "both" means when
its two referents are already present. Resume the original event and retain its timeframe.
Only genuinely unrelated life areas are compound. Different stages, reasons, strongest windows,
increased responsibility and formal recognition for ONE promotion are ONE integrated event request.
For example, "Will I get promoted in the next 12 months? Tell me the strongest timing windows,
whether increased responsibility will come before formal promotion, and the astrological reasons"
MUST use event_prediction, category career, route_action answer. Never ask the user to choose
between promotion timing, responsibilities, windows or astrological reasons for this same event.
For compound questions use answer_mode compound_plan and route_action clarify. A question that asks both
for an overall reading and its timing in the SAME life area is one integrated question, not compound:
answer it. For example, "How will my wealth be overall and when will I earn the maximum?" must use
route_action answer, category wealth, and a timing-capable answer mode. Never return route_action clarify
with an empty user_message.
Event routing: whether or when a specific milestone occurs (promotion, marriage, job offer, joining,
relocation or property purchase) uses event_prediction, including questions bounded to a month/year.
Do not classify these as an overall period outlook merely because a timeframe is given.
Daily routing: an overall outlook for today, tomorrow, yesterday, or one specified calendar day
uses answer_mode timing_window and forecast_scope daily. This is not a life-event timeline.
Resolve its target_date as YYYY-MM-DD using USER LOCAL NOW below. Use the latest question's scope,
not a career or other subject from previous questions. A specific event asked about on a date
is still event timing, not automatically an overall daily reading.
For other questions set forecast_scope other and target_date null.
Set needs_transits true for daily readings and when present/future timing materially matters.
Set time_relation to past for a request to identify an event that already happened
(for example, "when was I married?"); current for a present situation; future for
a future outlook; otherwise none.

Health routing is special: questions about an illness, symptom, injury, surgery, treatment,
rehabilitation, or recovery must never use event_prediction. A current recovery/prognosis
question such as "will I recover fine after surgery?" uses topic_reading and time_relation
current. If the user explicitly asks for the recovery pace or a near-term recovery period, use
timing_window with a bounded current/future horizon. Never route health to a lifespan or
life-event timeline.

RECENT CONVERSATION: {json.dumps(recent, ensure_ascii=False)}
USER LANGUAGE: {language}
USER LOCAL NOW: {now_local.isoformat()}
QUESTION: {question}

Schema:
{{"answer_mode":"...","category":"...","target_subject_key":"self","route_action":"answer","needs_transits":false,"time_relation":"past|current|future|none","forecast_scope":"daily|other","target_date":null,"user_message":""}}
""".strip()
    out = await analyzer.generate_text_from_prompt(
        prompt,
        premium_analysis=False,
        model_name_override=get_verified_router_model(),
        provider_override=CHAT_LLM_OPENAI,
        openai_reasoning_effort="none",
        llm_log_tag="verified_chat_router",
        request_timeout_s=20.0,
        system_prompt="You are a compact routing classifier. Return JSON only. Never generate HTML.",
    )
    if not out.get("success"):
        raise RuntimeError(str(out.get("error") or "verified_router_failed"))
    parsed = _json_object(str(out.get("response") or ""))
    action = str(parsed.get("route_action") or "answer").strip().lower()
    if action not in {"answer", "clarify", "handoff", "ack", "out_of_scope"}:
        action = "answer"
    answer_mode = str(parsed.get("answer_mode") or "topic_reading").strip()
    if answer_mode not in ANSWER_MODES:
        # The classifier occasionally mirrors route_action into answer_mode
        # (for example, answer_mode="out_of_scope"). Route actions are still
        # useful and must never turn a user-visible boundary reply into a 500.
        # Fall back to a benign mode because this field is ignored for those
        # non-analysis routes; the same fallback also keeps malformed answer
        # routes recoverable instead of failing the entire chat request.
        answer_mode = "topic_reading"
    category = str(parsed.get("category") or "general").strip().lower()
    if category not in _CATEGORY_VALUES:
        category = "general"
    target = str(parsed.get("target_subject_key") or "self").strip().lower()
    if target not in TARGET_SUBJECTS:
        target = "self"
    clarification_question = str(parsed.get("user_message") or "").strip()
    # A blank clarification is never actionable.  Treat it as a normal answer
    # request so a transient router mistake cannot complete the chat with an
    # empty assistant bubble.
    if action == "clarify" and not clarification_question:
        action = "answer"
        if answer_mode == "compound_plan":
            answer_mode = "topic_reading"
    time_relation = str(parsed.get("time_relation") or "none").strip().lower()
    if time_relation not in {"past", "current", "future", "none"}:
        time_relation = "none"
    health_categories = {"health", "disease", "mental_wellbeing", "surgery", "accident", "recovery"}
    if category in health_categories and answer_mode == "event_prediction":
        # Event prediction expands into the lifespan-event output contract. A health recovery
        # question needs a clinical-safety-constrained health reading, or a bounded outlook when
        # the user actually asks for pace/timing; it must never receive a life-event timeline.
        answer_mode = "topic_reading" if time_relation in {"current", "none"} else "timing_window"
    daily = str(parsed.get("forecast_scope") or "").lower() == "daily"
    period_window = None
    if daily:
        from datetime import date
        try:
            target_date = date.fromisoformat(str(parsed.get("target_date") or "")).isoformat()
            period_window = {"kind": "day", "start": target_date, "end": target_date}
        except ValueError:
            action = "clarify"
            clarification_question = clarification_question or "Which date would you like the daily reading for?"
        answer_mode = "timing_window"
    return {
        "period_window": period_window,
        "query_context": query_context or {},
        "status": "CLARIFY" if action == "clarify" else "READY",
        "mode": "PREDICT_DAILY" if daily else _mode_to_intent_mode(answer_mode),
        "answer_mode": answer_mode,
        "category": category,
        "target_subject_key": target,
        "target_subject_keys": [target],
        "needs_transits": bool(parsed.get("needs_transits")),
        "time_relation": time_relation,
        "route_action": action,
        "clarification_question": clarification_question,
        "router_source": "verified_luna_question_router",
        "_llm_usage_stage": {
            "provider": out.get("chat_llm_provider"),
            "model": out.get("chat_llm_model"),
            "token_usage": out.get("token_usage") or {},
        },
    }
