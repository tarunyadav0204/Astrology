from __future__ import annotations

import google.generativeai as genai
import json
import os
import re
import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from ai.evidence_planner_schema import normalize_evidence_plan
from ai.output_schema import resolve_output_language_policy
from daily.daily_micro_intents import classify_daily_micro_intent
from utils.query_context import normalize_query_context, resolve_query_now

logger = logging.getLogger(__name__)

def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


_MONTH_NAME_TO_NUM = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_MONTH_TOKEN_RE = r"(?:january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec)"
_CHART_INSIGHT_PLACEHOLDER_RE = re.compile(
    r"\[(?:sign|planet|house|nakshatra|degree|real insight|message|placeholder|.*language.*?)\]",
    re.IGNORECASE,
)


def _ordinal_suffix(value: int) -> str:
    if 10 <= value % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")


# Canonical divisional bundles per intent category (keep in sync with IntentRouter._get_default_divisional_charts).
_DEFAULT_DIVISIONAL_CHARTS_BY_CATEGORY: dict[str, list[str]] = {
    "marriage": ["D1", "D9", "D7"],
    "career": ["D1", "D9", "D10", "Karkamsa"],
    "job": ["D1", "D9", "D10", "Karkamsa"],
    "promotion": ["D1", "D9", "D10", "Karkamsa"],
    "business": ["D1", "D9", "D10", "Karkamsa"],
    "soul": ["D1", "D9", "D20", "Swamsa"],
    "spirituality": ["D1", "D9", "D20", "Swamsa"],
    "purpose": ["D1", "D9", "Karkamsa", "Swamsa"],
    "dharma": ["D1", "D9", "Karkamsa", "Swamsa"],
    "health": ["D1", "D9", "D30"],
    "disease": ["D1", "D9", "D30"],
    "children": ["D1", "D7", "D9"],
    "child": ["D1", "D7", "D9"],
    "pregnancy": ["D1", "D7", "D9"],
    "siblings": ["D1", "D3", "D9"],
    "property": ["D1", "D4", "D9", "D12"],
    "home": ["D1", "D4", "D9"],
    "mother": ["D1", "D4", "D9", "D12"],
    "father": ["D1", "D9", "D10", "D12"],
    "education": ["D1", "D9", "D24"],
    "learning": ["D1", "D9", "D24"],
    "vehicles": ["D1", "D4", "D16"],
    "travel": ["D1", "D3", "D9"],
    "foreign": ["D1", "D9", "D12"],
    "visa": ["D1", "D9", "D12"],
    "wealth": ["D1", "D9", "D10"],
    "money": ["D1", "D9", "D10"],
    "finance": ["D1", "D9", "D10"],
    "love": ["D1", "D7", "D9"],
    "relationship": ["D1", "D7", "D9"],
    "partner": ["D1", "D7", "D9"],
    "timing": ["D1", "D9"],
    "general": ["D1", "D9"],
    "son": ["D1", "D7", "D9"],
    "daughter": ["D1", "D7", "D9"],
    "spouse": ["D1", "D7", "D9"],
    "family": ["D1", "D9", "D12"],
}


_CHART_FOCUS_SYNONYMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("D1", ("d1",)),
    ("LAGNA", ("lagna", "ascendant", "rising sign", "asc")),
    ("D3", ("d3", "drekkana", "dreshkana", "drekkana")),
    ("D4", ("d4", "chaturthamsa", "chaturthamsha")),
    ("D7", ("d7", "saptamsa", "saptamsha")),
    ("D9", ("d9", "navamsa", "navamsha", "navansh", "navamsh")),
    ("D10", ("d10", "dashamsa", "dashamsha", "dasamsa", "dasamsha")),
    ("D12", ("d12", "dwadasamsa", "dwadashamsha")),
    ("D16", ("d16", "shodasamsa", "shodashamsha")),
    ("D20", ("d20", "vimsamsa", "vimshamsa")),
    ("D24", ("d24", "chaturvimsamsa", "siddhamsa", "siddhamsha")),
    ("D27", ("d27", "nakshatramsa", "bhamsa", "bhamsha")),
    ("D30", ("d30", "trimsamsa", "trimshamsha")),
    ("D40", ("d40", "khavedamsa", "khavedamsha")),
    ("D45", ("d45", "akshavedamsa", "akshavedamsha")),
    ("D60", ("d60", "shashtiamsa", "shashtiamsha")),
    ("Karkamsa", ("karkamsa",)),
    ("Swamsa", ("swamsa",)),
)

_CHART_FOCUS_CUES = (
    "analyze",
    "analyse",
    "reading",
    "read",
    "interpret",
    "tell me about",
    "focus on",
    "deep dive",
    "explain",
    "how is my",
    "what does my",
    "review",
)

def get_default_divisional_charts_for_category(category: str) -> list[str]:
    """Return the canonical divisional chart list for a router category (D1 baseline + topic charts)."""
    return list(_DEFAULT_DIVISIONAL_CHARTS_BY_CATEGORY.get((category or "general").strip().lower(), ["D1", "D9"]))


def _normalize_chart_focus_code(code: str) -> str:
    token = (code or "").strip()
    if not token:
        return ""
    if token == "LAGNA":
        return "D1"
    return _canonical_divisional_token(token)


def extract_chart_focus_from_question(user_question: str) -> Dict[str, Any] | None:
    """
    Detect only highly explicit chart-scoped asks such as "analyze my lagna",
    "read my D10", or "interpret my navamsha".

    Broad natural-language inference should come from the LLM intent router, not this
    deterministic fallback.
    """
    q = (user_question or "").strip()
    if not q:
        return None
    low = q.lower()

    matched_code = ""
    matched_phrase = ""
    candidates: list[tuple[str, str]] = []
    for code, phrases in _CHART_FOCUS_SYNONYMS:
        for phrase in phrases:
            candidates.append((code, phrase))
    candidates.sort(key=lambda item: len(item[1]), reverse=True)

    for code, phrase in candidates:
        if not phrase:
            continue
        pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
        if re.search(pattern, low):
                matched_code = code
                matched_phrase = phrase
                break
    if matched_code:
        pass

    if not matched_code:
        return None

    explicit = any(cue in low for cue in _CHART_FOCUS_CUES)
    if not explicit:
        short_patterns = (
            low.startswith(matched_phrase),
            low.endswith(matched_phrase),
            low in {matched_phrase, f"my {matched_phrase}", f"{matched_phrase} analysis"},
            bool(re.search(rf"\b{re.escape(matched_phrase)}\b", low) and len(low.split()) <= 8),
        )
        explicit = any(short_patterns)
    if not explicit:
        return None

    primary = _normalize_chart_focus_code(matched_code)
    label = "Lagna" if matched_code == "LAGNA" else primary
    return {
        "kind": "chart_specific",
        "primary": primary,
        "label": label,
        "explicit": True,
        "phrase": matched_phrase,
        "requested": [primary] if primary else [],
    }


def _canonical_divisional_token(c: str) -> str:
    """Normalize router chart codes: Dx uppercase; Jaimini names match chat_context_builder (`Karkamsa`, `Swamsa`)."""
    t = (c or "").strip()
    if not t:
        return ""
    low = t.lower()
    if low == "karkamsa":
        return "Karkamsa"
    if low == "swamsa":
        return "Swamsa"
    m = re.match(r"^d(\d+)$", low)
    if m:
        return "D" + m.group(1)
    return t


def _normalize_chart_focus_payload(focus: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(focus, dict):
        return None
    primary = _normalize_chart_focus_code(str(focus.get("primary") or ""))
    if not primary:
        return None
    label_raw = str(focus.get("label") or "").strip()
    label = label_raw or ("Lagna" if primary == "D1" else primary)
    kind = str(focus.get("kind") or "").strip() or "chart_specific"
    if kind != "chart_specific":
        return None
    requested = focus.get("requested")
    if isinstance(requested, list) and requested:
        normalized_requested = []
        seen: set[str] = set()
        for item in requested:
            token = _normalize_chart_focus_code(str(item or ""))
            if token and token not in seen:
                seen.add(token)
                normalized_requested.append(token)
    else:
        normalized_requested = [primary]
    return {
        "kind": "chart_specific",
        "primary": primary,
        "label": label,
        "explicit": bool(focus.get("explicit", True)),
        "phrase": str(focus.get("phrase") or "").strip(),
        "requested": normalized_requested,
    }


def merge_divisional_charts_with_category_defaults(
    result: Dict,
    user_question: str = "",
) -> None:
    """
    After the model returns divisional_charts, ensure the list includes every chart required for
    `category` (additive merge — extra charts from the model are kept). Fixes omissions like D24 for education.
    Also forces topic divisionals for lifespan timing when category is weak (timing/general).
    """
    required = get_default_divisional_charts_for_category(str(result.get("category") or "general"))
    raw = result.get("divisional_charts")
    if not isinstance(raw, list):
        result["divisional_charts"] = list(required)
        raw = result["divisional_charts"]
    seen: set[str] = set()
    out: list[str] = []
    for c in raw:
        if isinstance(c, str) and c.strip():
            u = _canonical_divisional_token(c)
            if u and u not in seen:
                seen.add(u)
                out.append(u)
    for r in required:
        cr = _canonical_divisional_token(r)
        if cr and cr not in seen:
            out.append(cr)
            seen.add(cr)
    result["divisional_charts"] = out
    try:
        from chat.lifespan_timing_evidence import force_divisional_codes_for_lifespan

        result["divisional_charts"] = force_divisional_codes_for_lifespan(
            mode=result.get("mode"),
            category=result.get("category"),
            question=str(user_question or ""),
            existing=result.get("divisional_charts"),
        )
    except Exception:
        pass


def _build_usage_stage(
    *,
    stage: str,
    llm_model: str | None,
    prompt_chars: int,
    response_chars: int,
    token_usage: Dict[str, Any] | None,
    success: bool,
    elapsed_ms: float | None = None,
) -> Dict[str, Any]:
    tu = token_usage or {}
    row: Dict[str, Any] = {
        "stage": stage,
        "llm_model": llm_model or "",
        "input_chars": int(prompt_chars or 0),
        "output_chars": int(response_chars or 0),
        "input_tokens": int(tu.get("input_tokens") or 0),
        "output_tokens": int(tu.get("output_tokens") or 0),
        "cached_tokens": int(tu.get("cached_tokens") or 0),
        "non_cached_input_tokens": int(
            tu.get("non_cached_input_tokens")
            or max(0, int(tu.get("input_tokens") or 0) - int(tu.get("cached_tokens") or 0))
        ),
        "success": bool(success),
    }
    if elapsed_ms is not None:
        row["elapsed_ms"] = round(float(elapsed_ms), 1)
    return row


def _is_transient_intent_error(exc: Exception) -> bool:
    text = str(exc or "").lower()
    markers = [
        "504",
        "deadline",
        "timeout",
        "timed out",
        "cancelled",
        "canceled",
        "prefill",
        "failed to close the streaming context",
        "thread is cancelled before we get prefill results",
        "unavailable",
        "internal",
    ]
    return any(marker in text for marker in markers)


def _usage_totals_from_stages(stages: list[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "input_chars": sum(int(s.get("input_chars") or 0) for s in stages),
        "output_chars": sum(int(s.get("output_chars") or 0) for s in stages),
        "input_tokens": sum(int(s.get("input_tokens") or 0) for s in stages),
        "output_tokens": sum(int(s.get("output_tokens") or 0) for s in stages),
        "cached_tokens": sum(int(s.get("cached_tokens") or 0) for s in stages),
        "non_cached_input_tokens": sum(int(s.get("non_cached_input_tokens") or 0) for s in stages),
        "elapsed_ms_sum": round(sum(float(s.get("elapsed_ms") or 0) for s in stages), 1),
    }


def apply_chart_focus_guards(result: Dict[str, Any], user_question: str) -> None:
    """
    Attach deterministic chart-focus metadata and ensure explicitly requested divisionals
    are available downstream even when the router category is broad/general.
    """
    focus = _normalize_chart_focus_payload(result.get("chart_focus"))
    if not focus:
        focus = extract_chart_focus_from_question(user_question)
    if not focus:
        return
    primary = _normalize_chart_focus_code(str(focus.get("primary") or ""))
    result["chart_focus"] = focus
    result.setdefault("extracted_context", {})
    if isinstance(result["extracted_context"], dict):
        result["extracted_context"]["chart_focus"] = {
            "primary": focus.get("primary"),
            "label": focus.get("label"),
        }
    if not primary or primary == "D1":
        return
    raw = result.get("divisional_charts")
    charts = raw if isinstance(raw, list) else []
    canonical = [_canonical_divisional_token(c) for c in charts if isinstance(c, str) and c.strip()]
    if primary not in canonical:
        canonical.append(primary)
    result["divisional_charts"] = canonical


def _extract_specific_date_from_question(user_question: str, *, now: datetime) -> str | None:
    """Parse relative / explicit calendar phrases from English text.

    Not used for intent routing (forcing ``PREDICT_DAILY``); kept for tests and optional tooling.
    """
    q = (user_question or "").strip()
    if not q:
        return None
    low = q.lower()

    if "day after tomorrow" in low:
        return (now + timedelta(days=2)).strftime("%Y-%m-%d")
    if "tomorrow" in low:
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    if "today" in low:
        return now.strftime("%Y-%m-%d")

    m = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", q)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime("%Y-%m-%d")
        except ValueError:
            return None

    month_re = r"(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec)"
    pat1 = re.search(rf"\b{month_re}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(20\d{{2}}))?\b", low)
    if pat1:
        mon = _MONTH_NAME_TO_NUM.get(pat1.group(1))
        day = int(pat1.group(2))
        year = int(pat1.group(3)) if pat1.group(3) else now.year
        try:
            return datetime(year, mon, day).strftime("%Y-%m-%d")
        except ValueError:
            return None

    pat2 = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{month_re}(?:,?\s+(20\d{{2}}))?\b", low)
    if pat2:
        day = int(pat2.group(1))
        mon = _MONTH_NAME_TO_NUM.get(pat2.group(2))
        year = int(pat2.group(3)) if pat2.group(3) else now.year
        try:
            return datetime(year, mon, day).strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def _extract_month_window_from_question(user_question: str, *, now: datetime) -> dict[str, Any] | None:
    q = (user_question or "").strip()
    if not q:
        return None
    low = q.lower()
    month_re = r"(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec)"
    # Month-year only. Avoid matching when an exact day is also present.
    pat = re.search(rf"\b{month_re}(?:\s+|,\s*)(20\d{{2}})\b", low)
    if not pat:
        return None
    month_token = str(pat.group(1) or "").strip().lower()
    year = int(pat.group(2))
    month_num = _MONTH_NAME_TO_NUM.get(month_token)
    if not month_num:
        return None
    # Skip if the matched month-year is part of an exact-day expression already handled elsewhere.
    before = low[: pat.start()]
    if re.search(r"\b\d{1,2}(?:st|nd|rd|th)?\s*$", before):
        return None
    month_name = datetime(year, month_num, 1).strftime("%B")
    return {
        "year": year,
        "month": month_name,
        "timeframe": f"{month_name} {year}",
    }


def _question_has_date_range(user_question: str) -> bool:
    """
    Detect explicit calendar ranges so the router cannot collapse "19 Jun to 25 Jun"
    into a single-day daily prediction.
    """
    low = re.sub(r"\s+", " ", str(user_question or "").strip().lower())
    if not low:
        return False

    day_month = rf"\d{{1,2}}(?:st|nd|rd|th)?\s*{_MONTH_TOKEN_RE}"
    month_day = rf"{_MONTH_TOKEN_RE}\s*\d{{1,2}}(?:st|nd|rd|th)?"
    iso_date = r"20\d{2}-\d{2}-\d{2}"
    date_expr = rf"(?:{iso_date}|{day_month}|{month_day})"

    return bool(
        re.search(rf"\bbetween\s+{date_expr}\s+(?:and|to|till|until|through|-|–|—)\s+{date_expr}\b", low)
        or re.search(rf"\bfrom\s+{date_expr}\s+(?:to|till|until|through|-|–|—)\s+{date_expr}\b", low)
        or re.search(rf"\b{date_expr}\s*(?:to|till|until|through|-|–|—)\s*{date_expr}\b", low)
    )


def _normalize_specific_date(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _daily_intent_confirmed(result: Dict[str, Any]) -> bool:
    """
    Daily mode is an explicit router contract, not a side effect of any date in the payload.

    The LLM must confirm that the user asked for one exact/relative day and explain the date basis.
    """
    extracted = result.get("extracted_context") if isinstance(result.get("extracted_context"), dict) else {}
    basis = str(
        extracted.get("specific_date_basis")
        or result.get("specific_date_basis")
        or ""
    ).strip()
    confirmed = result.get("daily_intent_confirmed")
    if isinstance(confirmed, str):
        confirmed = confirmed.strip().lower() in {"true", "yes", "1"}
    return bool(confirmed) and basis in {"explicit_user_day", "relative_user_day"}


def apply_transit_timing_guards(result: Dict, user_question: str, *, current_year: int, now: datetime | None = None) -> None:
    """
    Post-process router output: career/education (and related) questions that ask *when* or *whether*
    (will I / which year / job vs study) must request transits so the backend builds transit windows.
    """
    q = (user_question or "").strip().lower()
    cat = (result.get("category") or "general").strip().lower()
    now_dt = (now or datetime.now()).replace(hour=12, minute=0, second=0, microsecond=0)
    extracted_context = result.get("extracted_context") if isinstance(result.get("extracted_context"), dict) else {}
    month_window = _extract_month_window_from_question(user_question, now=now_dt)
    has_date_range = _question_has_date_range(user_question)
    llm_date = _normalize_specific_date(extracted_context.get("specific_date")) if extracted_context else None
    # Only a confirmed one-day intent may force exact-day mode. A model may include today's date
    # as ambient context for current distress/timing questions; that must not become daily mode.
    exact_date = llm_date
    daily_confirmed = _daily_intent_confirmed(result)

    if has_date_range:
        result["mode"] = "PREDICT_PERIOD_OUTLOOK"
        result["context_type"] = "birth"
        result["analysis_type"] = "PERIOD_OUTLOOK"
        result["needs_transits"] = True
        result["daily_intent_confirmed"] = False
        result.setdefault("extracted_context", {})
        if isinstance(result["extracted_context"], dict):
            result["extracted_context"].pop("specific_date", None)
            result["extracted_context"]["specific_date_basis"] = "not_date_bound"
            result["extracted_context"].setdefault("timeframe", "date range from user question")
        result.pop("dasha_as_of", None)
        exact_date = None
        daily_confirmed = False

    if month_window and not exact_date:
        result["mode"] = "PREDICT_PERIOD_OUTLOOK"
        result["context_type"] = "birth"
        result["analysis_type"] = "PERIOD_OUTLOOK"
        result["needs_transits"] = True
        result.setdefault("extracted_context", {})
        if isinstance(result["extracted_context"], dict):
            result["extracted_context"]["timeframe"] = month_window["timeframe"]
            result["extracted_context"].pop("specific_date", None)
        result["transit_request"] = {
            "startYear": month_window["year"],
            "endYear": month_window["year"],
            "yearMonthMap": {str(month_window["year"]): [month_window["month"]]},
        }
        result.pop("dasha_as_of", None)

    if exact_date and daily_confirmed:
        dt = datetime.strptime(exact_date, "%Y-%m-%d")
        month_name = dt.strftime("%B")
        result["mode"] = "PREDICT_DAILY"
        result["context_type"] = "birth"
        result["analysis_type"] = "DAILY_PREDICTION"
        result["needs_transits"] = True
        result["dasha_as_of"] = exact_date
        result.setdefault("extracted_context", {})
        if isinstance(result["extracted_context"], dict):
            result["extracted_context"]["specific_date"] = exact_date
        result["transit_request"] = {
            "startYear": dt.year,
            "endYear": dt.year,
            "yearMonthMap": {str(dt.year): [month_name]},
        }
    elif exact_date and not daily_confirmed:
        if isinstance(result.get("extracted_context"), dict):
            result["extracted_context"].pop("specific_date", None)
        if str(result.get("mode") or "").upper() == "PREDICT_DAILY":
            result["mode"] = "PREDICT_PERIOD_OUTLOOK"
            result["context_type"] = "birth"
            result["analysis_type"] = "PERIOD_OUTLOOK"
            result["needs_transits"] = True
            result.pop("dasha_as_of", None)

    careerish = cat in frozenset({"education", "career", "job", "promotion", "business"})
    if not careerish:
        return
    timing_ask = any(
        phrase in q
        for phrase in (
            "when ",
            " when",
            "when?",
            "will i",
            "which year",
            "what year",
            "first job",
            "after i ",
            "after graduation",
            "timing",
            "which month",
            "what month",
            " or job",
            "job or",
            "masters or",
            "degree or",
            "study or",
            "kab ",
        )
    )
    if timing_ask:
        result["needs_transits"] = True


def apply_daily_micro_intent_guards(result: Dict[str, Any], user_question: str) -> None:
    mode = str(result.get("mode") or "").upper()
    if mode != "PREDICT_DAILY":
        return
    result.setdefault("extracted_context", {})
    if not isinstance(result["extracted_context"], dict):
        result["extracted_context"] = {}
    result["extracted_context"]["daily_micro_intent"] = classify_daily_micro_intent(
        user_question,
        category=str(result.get("category") or "general"),
    )


_WEAK_INTENT_CATEGORIES = frozenset({"general", "timing", ""})


def _normalize_question_for_intent(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _refine_life_event_category(user_question: str, result: Dict[str, Any]) -> None:
    """When category is generic, infer marriage/job/child/etc. from life-event timing phrasing."""
    cat = str(result.get("category") or "").strip().lower()
    if cat not in _WEAK_INTENT_CATEGORIES:
        return
    q = _normalize_question_for_intent(user_question)
    if not q:
        return

    def _set(cat_out: str, aspect: str | None = None) -> None:
        result["category"] = cat_out
        if aspect:
            result.setdefault("extracted_context", {})
            if isinstance(result.get("extracted_context"), dict):
                result["extracted_context"].setdefault("aspect", aspect)

    # Reconciliation / return (before generic "love")
    if any(
        k in q
        for k in (
            "come back",
            "comeback",
            "will he come",
            "will she come",
            "will they come",
            "get back together",
            "back together",
            "reconcile",
            "patch up",
            "return to me",
            "lover back",
            " ex ",
            " ex?",
            " ex.",
            "my ex",
            "leave me and",
        )
    ):
        _set("relationship", "reconciliation")
        return

    if any(k in q for k in ("shaadi", "vivah", "married", "marriage", "wedding", "get married", "marry him", "marry her", "marry me")):
        _set("marriage", "marriage")
        return
    if " marry" in q or q.startswith("marry ") or "marry?" in q:
        _set("marriage", "marriage")
        return

    if any(k in q for k in ("pregnant", "pregnancy", "conceive", "conception", "expecting a baby", "expecting baby")):
        _set("pregnancy", "pregnancy")
        return
    if any(k in q for k in ("have a baby", "have baby", "get a child", "get child", "have a child", "have child", "give birth", "baby boy", "baby girl")):
        _set("child", "children")
        return
    if any(k in q for k in (" son ", " daughter ", " my son", " my daughter", " kids ", " kid ", "children", "baccha", "bachcha", "bacha")):
        _set("child", "children")
        return

    if any(k in q for k in ("get a job", "get job", "new job", "first job", "naukri", "rozgar", "employment", "get hired", "job offer")):
        _set("job", "job")
        return
    if any(k in q for k in ("promotion", "salary hike", "pay raise", "raise at work")):
        _set("promotion", "promotion")
        return
    if any(k in q for k in ("career", "profession", "professional life")):
        _set("career", "career")
        return

    if any(k in q for k in ("wealth", "become rich", "get rich", "financially", "windfall", "inherit")):
        _set("wealth", "wealth")
        return
    if any(k in q for k in (" money ", " money?", "make money", "earn money", "financial ")):
        _set("money", "money")
        return

    if any(k in q for k in ("health", "recover", "disease", "illness", "sick ", " surgery")):
        _set("health", "health")
        return

    if any(k in q for k in ("buy a house", "buy house", "buy a home", "buy home", "property", "real estate")):
        _set("property", "property")
        return

    if any(k in q for k in ("visa", " abroad", "move abroad", "settle abroad")):
        _set("visa", "visa")
        return
    if "travel" in q or " trip " in q:
        _set("travel", "travel")
        return

    if any(k in q for k in ("fall in love", "find love", " soulmate", " meet someone", "get a partner")):
        _set("love", "love")
        return


def _normalize_lifespan_timing_mode(result: Dict[str, Any]) -> None:
    mode_u = str(result.get("mode") or "").strip().upper()
    if mode_u == "PREDICT_EVENT_TIMING":
        result["mode"] = "LIFESPAN_EVENT_TIMING"


def _is_unlocked_life_termination_research_question(question: str) -> bool:
    """
    Restricted death/life-termination mode selector.

    The normal death guard blocks these questions unless an admin-configured
    unlock phrase is present. When the phrase is present, keep routing explicit
    so the answer uses the dedicated confluence protocol rather than generic
    event timing.
    """
    if not question or not isinstance(question, str):
        return False
    try:
        from ai.death_query_guard import is_death_override_unlocked, matches_death_patterns

        return bool(is_death_override_unlocked(question) and matches_death_patterns(question))
    except Exception:
        return False


def _force_life_termination_research_mode(result: Dict[str, Any], *, current_year: int) -> None:
    result["mode"] = "LIFE_TERMINATION_RESEARCH"
    result["context_type"] = "birth"
    result["category"] = "health"
    result["needs_transits"] = True
    charts = result.get("divisional_charts")
    if not isinstance(charts, list):
        charts = []
    for code in ("D1", "D3", "D8", "D9", "D30"):
        if code not in charts:
            charts.append(code)
    result["divisional_charts"] = charts
    result["extracted_context"] = result.get("extracted_context") if isinstance(result.get("extracted_context"), dict) else {}
    result["extracted_context"]["aspect"] = result["extracted_context"].get("aspect") or "classical longevity and life-termination research"
    result["extracted_context"]["specific_date"] = None
    result["extracted_context"]["specific_date_basis"] = "not_date_bound"
    end_year = current_year + 80
    result["transit_request"] = {
        "startYear": current_year,
        "endYear": end_year,
        "yearMonthMap": {
            str(y): ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            for y in range(current_year, end_year + 1)
        },
    }


class IntentRouter:
    """
    Classifies user queries into various analysis modes for the astrology chat AI.
    Uses Gemini Flash for ultra-fast (<1s) classification.
    """
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        from utils.admin_settings import get_setting
        self._gen_config = genai.GenerationConfig(temperature=0, top_p=0.95, top_k=40)
        self._model_cache = {}
        # Intent routing must stay fast and deterministic; avoid Pro models here.
        model_name = (get_setting("gemini_intent_model") or "models/gemini-2.5-flash-lite").strip()
        if "pro" in model_name.lower():
            model_name = "models/gemini-2.5-flash-lite"
        try:
            self.model = genai.GenerativeModel(model_name, generation_config=self._gen_config)
        except Exception as e:
            fallback_fast = "models/gemini-2.0-flash-lite-001"
            logger.warning("intent router model %s not available (%s), trying default", model_name, e)
            self.model = genai.GenerativeModel(fallback_fast, generation_config=self._gen_config)

    def _get_model(self):
        """Resolve intent model from admin settings (no restart needed), but keep it non-Pro."""
        from utils.admin_settings import get_setting
        name = (get_setting("gemini_intent_model") or "models/gemini-2.5-flash-lite").strip()
        if "pro" in name.lower():
            name = "models/gemini-2.5-flash-lite"
        if name in self._model_cache:
            return self._model_cache[name]
        try:
            self._model_cache[name] = genai.GenerativeModel(name, generation_config=self._gen_config)
            return self._model_cache[name]
        except Exception as e:
            logger.warning("intent router model %s not available (%s), using fallback", name, e)
            return self.model

    def _get_instant_model(self):
        """Resolve the fast instant/speech router model without changing standard chat routing."""
        from utils.admin_settings import get_setting

        name = (
            get_setting("gemini_instant_intent_model")
            or get_setting("gemini_intent_model")
            or "models/gemini-3.1-flash-lite"
        ).strip()
        if "pro" in name.lower():
            name = "models/gemini-3.1-flash-lite"
        if "2.0-flash-lite" in name.lower():
            name = "models/gemini-3.1-flash-lite"
        if name in self._model_cache:
            return self._model_cache[name]
        try:
            self._model_cache[name] = genai.GenerativeModel(name, generation_config=self._gen_config)
            return self._model_cache[name]
        except Exception as e:
            fallback_fast = "models/gemini-3.1-flash-lite"
            logger.warning("instant intent router model %s not available (%s), using %s", name, e, fallback_fast)
            self._model_cache[fallback_fast] = genai.GenerativeModel(fallback_fast, generation_config=self._gen_config)
            return self._model_cache[fallback_fast]

    def _chart_insight_message_is_valid(self, message: Any) -> bool:
        if not isinstance(message, str):
            return False
        text = message.strip()
        if not text:
            return False
        if _CHART_INSIGHT_PLACEHOLDER_RE.search(text):
            return False
        lowered = text.lower()
        blocked_snippets = (
            "real insight in inferred",
            "current question language",
            "replace bracketed text",
            "generic house meaning",
            "specific insight about this native",
        )
        return not any(snippet in lowered for snippet in blocked_snippets)

    def _build_fallback_chart_insights(self, d1_chart: Dict[str, Any] | None) -> list[Dict[str, Any]]:
        if not isinstance(d1_chart, dict):
            return []

        planets = d1_chart.get("planets")
        if not isinstance(planets, dict):
            return []

        ascendant_info = d1_chart.get("ascendant_info") or d1_chart.get("ascendant") or {}
        asc_sign_name = ""
        if isinstance(ascendant_info, dict):
            asc_sign_name = str(
                ascendant_info.get("sign_name")
                or ascendant_info.get("sign")
                or ascendant_info.get("formatted")
                or ""
            ).strip()

        house_to_planets: dict[int, list[str]] = {}
        for planet_name, pdata in planets.items():
            if not isinstance(pdata, dict):
                continue
            try:
                house = int(pdata.get("house"))
            except (TypeError, ValueError):
                continue
            if not 1 <= house <= 12:
                continue
            display_name = str(planet_name).strip()
            if not display_name:
                continue
            house_to_planets.setdefault(house, []).append(display_name)

        insights: list[Dict[str, Any]] = []
        if asc_sign_name:
            insights.append(
                {
                    "house_number": 1,
                    "message": f"The Ascendant is in {asc_sign_name}, shaping how this person naturally approaches life and presents themselves.",
                    "highlight_type": "ascendant",
                }
            )

        for house in range(1, 13):
            occupants = house_to_planets.get(house, [])
            if not occupants:
                continue
            joined = ", ".join(occupants[:3])
            plural = "s" if len(occupants) > 1 else ""
            verb = "are" if len(occupants) > 1 else "is"
            insights.append(
                {
                    "house_number": house,
                    "message": f"{joined} {verb} placed in the {house}{_ordinal_suffix(house)} house, making this area of life more prominent in the chart.",
                    "highlight_type": "planets",
                }
            )
            if len(insights) >= 6:
                break

        return insights[:6]

    def _finalize_router_result(
        self,
        result: Dict[str, Any],
        *,
        user_question: str,
        current_year: int,
        current_month: str,
        resolved_now: datetime,
        normalized_query_context: Dict[str, Any] | None,
        include_chart_insights: bool,
        d1_chart: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if 'status' not in result:
            result['status'] = 'READY'
        if 'mode' not in result or result['mode'] is None:
            result['mode'] = 'PREDICT_EVENTS_FOR_PERIOD' if any(w in user_question.lower() for w in ['all events', 'events', 'timeline']) else 'ANALYZE_PERSONALITY'
        _normalize_lifespan_timing_mode(result)
        if _is_unlocked_life_termination_research_question(user_question):
            _force_life_termination_research_mode(result, current_year=current_year)
        if 'context_type' not in result:
            result['context_type'] = 'birth'
        if 'category' not in result or result['category'] is None:
            result['category'] = 'general'
        _refine_life_event_category(user_question, result)
        if 'extracted_context' not in result or not isinstance(result.get('extracted_context'), dict):
            result['extracted_context'] = {}
        if 'needs_transits' not in result:
            qlow = user_question.lower()
            result['needs_transits'] = result['context_type'] in ['birth', 'annual'] and any(
                word in qlow
                for word in [
                    'when',
                    'timing',
                    'period',
                    'year',
                    '2025',
                    '2026',
                    '2027',
                    'will i',
                    'which year',
                    'first job',
                ]
            )
        if 'divisional_charts' not in result or not isinstance(result.get('divisional_charts'), list):
            result['divisional_charts'] = self._get_default_divisional_charts(result.get('category', 'general'))
        merge_divisional_charts_with_category_defaults(result, user_question=user_question)
        apply_chart_focus_guards(result, user_question)

        if include_chart_insights:
            raw_insights = result.get('chart_insights')
            if isinstance(raw_insights, list) and raw_insights:
                valid = []
                for item in raw_insights:
                    if not isinstance(item, dict):
                        continue
                    house_number = item.get('house_number')
                    message = item.get('message')
                    if not house_number or not self._chart_insight_message_is_valid(message):
                        continue
                    valid.append(item)
                result['chart_insights'] = valid or self._build_fallback_chart_insights(d1_chart)
            else:
                result['chart_insights'] = self._build_fallback_chart_insights(d1_chart)
        else:
            result['chart_insights'] = []

        apply_transit_timing_guards(
            result,
            user_question,
            current_year=current_year,
            now=resolved_now.replace(tzinfo=None) if getattr(resolved_now, "tzinfo", None) else resolved_now,
        )
        apply_daily_micro_intent_guards(result, user_question)
        if normalized_query_context:
            result["query_context"] = normalized_query_context
        result["evidence_plan"] = normalize_evidence_plan(
            result.get("evidence_plan"),
            question=user_question,
        )

        if result.get('needs_transits') and 'transit_request' not in result:
            result['transit_request'] = {
                "startYear": current_year,
                "endYear": current_year + 2,
                "yearMonthMap": {
                    str(y): ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                    for y in range(current_year, current_year + 3)
                }
            }
        return result

    def _build_fallback_intent_result(
        self,
        *,
        user_question: str,
        current_year: int,
        current_month: str,
        resolved_now: datetime,
        normalized_query_context: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        is_timing_question = any(w in user_question.lower() for w in ['when', 'time', 'date', 'year', 'month', 'will i', 'should i'])

        if _is_unlocked_life_termination_research_question(user_question):
            result = {
                "status": "READY",
                "extracted_context": {},
                "mode": "LIFE_TERMINATION_RESEARCH",
                "context_type": "birth",
                "category": "health",
                "needs_transits": True,
                "divisional_charts": ["D1", "D3", "D8", "D9", "D30"],
                "chart_insights": [],
            }
            _force_life_termination_research_mode(result, current_year=current_year)
            if normalized_query_context:
                result["query_context"] = normalized_query_context
            result["evidence_plan"] = normalize_evidence_plan(None, question=user_question)
            apply_chart_focus_guards(result, user_question)
            return result

        if is_timing_question:
            result = {
                "status": "READY", "extracted_context": {}, "mode": "LIFESPAN_EVENT_TIMING", "context_type": "birth", "category": "timing", "needs_transits": True,
                "divisional_charts": ["D1", "D9"],
                "chart_insights": [],
                "transit_request": {
                    "startYear": current_year, "endYear": current_year + 2,
                    "yearMonthMap": {str(y): ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"] for y in range(current_year, current_year + 3)}
                }
            }
            _refine_life_event_category(user_question, result)
            result["divisional_charts"] = self._get_default_divisional_charts(result.get("category", "general"))
            merge_divisional_charts_with_category_defaults(result, user_question=user_question)
            if normalized_query_context:
                result["query_context"] = normalized_query_context
            result["evidence_plan"] = normalize_evidence_plan(None, question=user_question)
            apply_chart_focus_guards(result, user_question)
            return result
        result = {
            "status": "READY", "extracted_context": {}, "mode": "ANALYZE_PERSONALITY", "context_type": "birth", "category": "general", "needs_transits": False,
            "divisional_charts": ["D1", "D9"],
            "chart_insights": [],
        }
        if normalized_query_context:
            result["query_context"] = normalized_query_context
        result["evidence_plan"] = normalize_evidence_plan(None, question=user_question)
        apply_chart_focus_guards(result, user_question)
        return result

    def _build_instant_history_text(self, chat_history: list | None) -> str:
        history = chat_history or []
        if not history:
            return ""
        lines = [
            "\nRecent conversation (ONLY if directly relevant to the current message):",
        ]
        for msg in history[-2:]:
            q = str(msg.get("question", "")).strip()
            a = str(msg.get("response", "")).strip()
            if q:
                lines.append(f"User: {q[:220]}")
            if a:
                lines.append(f"Assistant: {a[:260]}")
        return "\n".join(lines)

    def _build_compact_instant_router_prompt(
        self,
        *,
        user_question: str,
        history_text: str,
        app_language: str,
        current_date: str,
        current_year: int,
        current_month: str,
        clarification_limit_text: str,
        force_ready_instruction: str,
        force_clarify_instruction: str,
    ) -> str:
        return f"""
You are AstroRoshni's multilingual semantic intent router for instant/speech astrology chat.
Return ONLY valid JSON. Do not explain. Do not generate chart insights or birth-detail requests.

App language fallback: {app_language}
Today: {current_date}; current year: {current_year}; current month: {current_month}

{clarification_limit_text}
{force_ready_instruction}
{force_clarify_instruction}
{history_text}

Current question: "{user_question}"

Task:
1. Semantically understand the user's question in any language/script.
2. Decide READY vs CLARIFY. Clarify only when the core topic/event is genuinely unclear, the user asks multiple unrelated life areas, or a reference like "this/that" cannot be resolved from recent history. Do not clarify for one clear domain with multiple facets, follow-up challenges, or natural messy phrasing.
3. Select the astrology mode, answer mode, subject, category, timeframe/date, chart focus, transit need, and compact divisional chart list.

Modes:
- PREDICT_DAILY: one exact day, today, tomorrow, or a named date.
- PREDICT_PERIOD_OUTLOOK: a period/window like this year, next 3 months, second half of 2028.
- LIFESPAN_EVENT_TIMING: when/if one specific event happens.
- LIFE_TERMINATION_RESEARCH: only with the configured unlock phrase and explicit death/longevity-end timing.
- ANALYZE_PERSONALITY: nature, traits, temperament, self-understanding.
- ANALYZE_TOPIC_POTENTIAL: "how is my career/marriage/health/money/relationship" style readings.
- RECOMMEND_REMEDY_FOR_PROBLEM: remedy/upay/action for a specific problem.

Answer modes:
- explanation_mechanism: how/why a previous chart claim was made.
- trait_nature: personality, behavior, speech, temperament.
- relationship_person: spouse/partner/child/relative/person characteristics.
- timing_window: outlook for a named period/window.
- event_prediction: when/if one specific event happens.
- potential_capacity: suitability, promise, aptitude, capacity.
- comparison_choice: choosing between options.
- problem_diagnosis: why something is blocked, delayed, unstable, difficult.
- remedy_action: remedy/upay/fix/action.
- topic_reading: focused reading when no other answer mode fits.

Categories:
career, job, promotion, business, love, relationship, marriage, partner, wealth, money, finance, health, disease, property, home, child, pregnancy, education, learning, travel, visa, foreign, gain, wish, general, son, daughter, mother, father, spouse, siblings, children, family, soul, spirituality, purpose, dharma, vehicles, timing.
For "when will I..." choose the life area category, not generic timing, when identifiable.

Target subjects:
self, spouse, wife, husband, partner, child, first_child, second_child, third_child, mother, father, sibling, brother, sister, younger_brother, younger_sister, younger_sibling, elder_brother, elder_sister, elder_sibling, maternal_uncle, uncle.
Use self only when the question is about the native directly. If the user asks about "my wife", "my husband", "spouse", "partner", child, parent, or sibling, use that person as target_subject_key.

Date/time rules:
- Use current date only to resolve relative dates; never set specific_date just because today is available.
- Date ranges/periods are not daily; put them in extracted_context.timeframe.
- specific_date_basis: explicit_user_day, relative_user_day, or not_date_bound.
- context_type is annual only for whole-year forecast style asks; otherwise birth.
- needs_transits true for daily, timing, and period outlook questions.

Divisional charts:
Always keep small. D1/D9 default. Add D10 career/job/business, D7 relationship/children/pregnancy, D30 health/disease, D24 education, D4 property/home, D12 parents/family, Karkamsa/Swamsa soul/purpose.

Evidence planner:
- Build an `evidence_plan` that describes what data agents must collect; do not write astrology rule combinations as text.
- Use enum values only.
- Split compound questions into multiple `question_parts`.
- Add one `evidence_needs` item per data need, not per sentence.
- For "When will I get married?", use event_timing + future_dasha_event_windows + transit_event_windows + natal_topic_foundation with event_profile marriage.
- For "When will my Mercury dasha start and how will my career be?", use two parts: factual_chart_lookup for dasha_timeline_lookup and topic_outlook for career evidence.
- Always include safety.blocked_content_checks for death_prediction and fetal_sex_determination.

Calibration:
- "How is my relationship with my wife?" -> READY, ANALYZE_TOPIC_POTENTIAL, category relationship or marriage, answer_mode topic_reading, target_subject_key wife, needs_transits false.
- "How will my health be this year?" -> READY, PREDICT_PERIOD_OUTLOOK, category health, answer_mode timing_window, target_subject_key self, context_type annual, needs_transits true, timeframe this year.
- "How will my career be in the second half of 2028?" -> READY, PREDICT_PERIOD_OUTLOOK, category career, answer_mode timing_window, target_subject_key self, needs_transits true, timeframe second half of 2028.

Return exactly this JSON shape:
{{
  "status": "CLARIFY" or "READY",
  "clarification_question": "same language/script as user, only when CLARIFY",
  "chart_insights": [],
  "mode": "PREDICT_DAILY" or "PREDICT_PERIOD_OUTLOOK" or "LIFESPAN_EVENT_TIMING" or "LIFE_TERMINATION_RESEARCH" or "ANALYZE_TOPIC_POTENTIAL" or "ANALYZE_PERSONALITY" or "RECOMMEND_REMEDY_FOR_PROBLEM",
  "chart_focus": {{"kind":"chart_specific","primary":"D9","label":"Navamsha","explicit":true,"phrase":"navamsha","requested":["D9"]}} or null,
  "answer_mode": "explanation_mechanism" or "trait_nature" or "relationship_person" or "timing_window" or "event_prediction" or "potential_capacity" or "comparison_choice" or "problem_diagnosis" or "remedy_action" or "topic_reading",
  "target_subject_key": "one allowed target subject",
  "needs_year_clarification": false,
  "daily_intent_confirmed": true or false,
  "extracted_context": {{"timeframe":"", "aspect":"", "specific_date": null, "specific_date_basis":"not_date_bound"}},
  "context_type": "birth" or "annual",
  "category": "general",
  "year": "year only when annual is clearly asked",
  "needs_transits": true or false,
  "divisional_charts": ["D1","D9"],
  "transit_request": null,
  "evidence_plan": {{
    "schema_version": "evidence_plan.v1",
    "question_parts": [
      {{"part_id":"p1","text":"part text","intent_families":["event_timing"],"life_domain":"marriage","event_profile":"marriage","subject":"self","timeframe":{{"kind":"open_future"}},"confidence":"high"}}
    ],
    "evidence_needs": [
      {{"need_id":"n1","kind":"natal_topic_foundation","system":"parashari","topic":"marriage","supports_parts":["p1"],"params":{{"event_profile":"marriage","required_charts":["D1","D9"]}},"priority":"required"}}
    ],
    "safety": {{
      "blocked_content_checks": [
        {{"check_id":"death_prediction","action_if_detected":"refuse_and_redirect"}},
        {{"check_id":"fetal_sex_determination","action_if_detected":"refuse_and_redirect"}}
      ],
      "answer_safety_checks": ["no_fatalism","no_guaranteed_prediction","no_unsupported_exact_date"]
    }},
    "answer_plan": {{"style":"speech_concise","must_answer_parts":["p1"],"answer_order":["p1"]}}
  }}
}}
""".strip()

    async def classify_instant_intent(
        self,
        user_question: str,
        chat_history: list = None,
        clarification_count: int = 0,
        max_clarifications: int | None = None,
        language: str = 'english',
        force_ready: bool = False,
        force_clarify: bool = False,
        query_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        import time

        intent_start = time.time()

        resolved_now = resolve_query_now(query_context)
        normalized_query_context = normalize_query_context(query_context)
        current_year = resolved_now.year
        current_month = resolved_now.strftime('%B')
        current_date = resolved_now.strftime('%Y-%m-%d')
        d1_chart = None

        history_text = self._build_instant_history_text(chat_history)
        _lang = str(language or "english").strip() or "english"
        language_policy = resolve_output_language_policy(_lang, user_question)
        app_language = language_policy.get("app_language", _lang)

        clarification_limit_text = ""
        if max_clarifications is not None and clarification_count >= max_clarifications:
            clarification_limit_text = """
You have already reached the clarification limit for this conversation.
You must now return status "READY" and proceed without asking another clarification.
"""

        force_ready_instruction = ""
        if force_ready:
            force_ready_instruction = """
You must return status "READY".
Do not ask any clarification.
If the question is vague, make a reasonable assumption and proceed.
"""

        force_clarify_instruction = ""
        if force_clarify:
            force_clarify_instruction = """
You must return status "CLARIFY".
Ask exactly one short clarification question to narrow the user's topic.
Do not ask for birth details.
"""

        prompt = f"""
You are the lightweight intent router for an astrology chat. Keep this fast and minimal.

Your job:
- classify the user's current question
- decide if clarification is needed
- identify if it is a daily / exact-date / timing / personality / topic-potential / remedy style question
- classify the universal answer mode needed by the response generator
- identify the target subject/person being asked about
- extract an exact `specific_date` in YYYY-MM-DD when the user is asking about one exact day

Do NOT generate chart insights.
Do NOT explain your reasoning.
Do NOT ask for birth details.
Do NOT add formatting, bullets, or extra prose outside JSON.

Language rule:
- If you return `clarification_question`, write it in the same language/script style as the current user question.
- If unclear, fall back to app language "{app_language}".

Current date context:
- Today: {current_date}
- Current year: {current_year}
- Current month: {current_month}

{clarification_limit_text}
{force_ready_instruction}
{force_clarify_instruction}
{history_text}

Current question: "{user_question}"

Rules:
- Use `PREDICT_DAILY` for today/tomorrow/exact-day questions.
- Use `PREDICT_PERIOD_OUTLOOK` for "next 3 months", "this year", "coming months" style outlooks.
- Use `LIFESPAN_EVENT_TIMING` for simple "when will X happen?" timing questions.
- Use `LIFE_TERMINATION_RESEARCH` only when the configured death/longevity unlock phrase is present and the user explicitly asks death/life-termination/lifespan-end timing. This is not normal health mode.
- Use `ANALYZE_PERSONALITY` for personality/self-understanding questions.
- Use `ANALYZE_TOPIC_POTENTIAL` for "how is my career/love/money/health" style questions.
- Use `RECOMMEND_REMEDY_FOR_PROBLEM` for remedy requests tied to a specific problem.
- IMPORTANT: clarification is ALLOWED in instant mode. Do NOT default to READY when the ask is genuinely unclear.
- Return `CLARIFY` only when the user has not made the core topic specific enough to answer well in one instant reply, or when the message explicitly contains separate unrelated asks.
- Good reasons to `CLARIFY`:
  - the message explicitly mixes unrelated life areas as separate asks, like "career, marriage, and money" or "first tell career, then marriage"
  - the user says something broad like "tell me about my life", "what is coming", "analyze my chart", "what do you see" without a clear focus
  - the user asks for timing or prediction but the event/topic itself is unclear
  - the user asks "which is better?" or "what about this?" but the reference is ambiguous from recent chat
- IMPORTANT FOLLOW-UP RULE:
  - if the user is challenging, questioning, or asking you to justify a previous claim, do NOT clarify
  - examples: "you said...", "how exactly?", "why do you think that?", "what relation does X have with Y?", "on what basis?"
  - these should return `READY` and be treated as a follow-up explanation, usually keeping the same category as the immediately relevant recent exchange
- Do NOT `CLARIFY` for straightforward single-topic questions like:
  - "How is my career this month?"
  - "Will today go well?"
  - "When will I get married?"
  - "How is my relationship with my husband?"
  - "How is my marriage life and relationship with my husband?"
  - "Will I get promotion and salary hike this year?"
  - "How is my career growth and income in 2026?"
  - "When will I get married and what will my spouse be like?"
  - "You said Rahu activates my 10th house. How?"
  - "Why do you think that about my behavior?"
- Related facets inside one domain are ONE question, not multiple questions. Examples: job + salary + promotion = career; marriage + spouse + husband/wife + relationship = relationship/marriage; health + stress + work pressure = health/stress.
- If the user message bundles explicit multiple unrelated asks, prefer `CLARIFY` unless clarification has already been used.
- If asking about an exact day, relative day, or specific date-bound event, return `extracted_context.specific_date` in YYYY-MM-DD.
- Resolve "today", "tomorrow", and "day after tomorrow" from the current date context above.
- Daily mode is opt-in: set `daily_intent_confirmed=true` only when the user is truly asking about one exact day.
- Date ranges are NOT daily, even when they contain exact dates. For "between 19 Jun and 25 Jun", "from 19 Jun to 25 Jun", or "19 Jun-25 Jun", do NOT set `PREDICT_DAILY`, do NOT set `specific_date`, set `daily_intent_confirmed=false`, and use `PREDICT_PERIOD_OUTLOOK` or event timing for the whole range.
- Set `extracted_context.specific_date_basis` to:
  - "explicit_user_day" when the user named a specific date/day
  - "relative_user_day" when the user asked today/tomorrow/day-after-tomorrow
  - "not_date_bound" for ongoing problems, current-life distress, broad timing questions, or period questions
- Do NOT set `specific_date` just because today's date is available in context. Current distress is not daily intent.
- Non-exhaustive calibration examples (use the principle, do not force-fit only these examples):
  - "Since this year started my life is disturbed, when will things improve?" -> NOT daily; use PREDICT_PERIOD_OUTLOOK or LIFESPAN_EVENT_TIMING
  - "Meri life disturbed hai, kab tak thik hoga?" -> NOT daily; use timing/problem analysis
  - "Will I travel between 19 Jun and 25 Jun?" -> NOT daily; use PREDICT_PERIOD_OUTLOOK for the full range
  - "Aaj ka din kaisa rahega?" -> daily with relative_user_day
  - "27 May 2026 kaisa rahega?" -> daily with explicit_user_day
- Set `needs_transits=true` for daily, timing, and period outlook questions. Otherwise false unless clearly timing-sensitive.
- `context_type` is usually `birth`; use `annual` only for whole-year forecast style questions.
- Keep `divisional_charts` small but sensible. D1 and D9 are enough for most instant routing. Add D10 for career/work, D7 for relationships/children, D30 for health/disease, D24 for education, D4 for property/home.
- When you do return `CLARIFY`, ask only one short narrowing question and give 2-4 quick options when helpful.

UNIVERSAL ANSWER MODE:
- `explanation_mechanism`: user asks how/why a previous chart claim was made
- `trait_nature`: behavior, temperament, nature, personality, speech style
- `relationship_person`: nature/characteristics of spouse/partner/child/relative/person
- `timing_window`: overall outlook for a named period such as this month, this year, next 6 months
- `event_prediction`: when/if one specific life event will happen
- `potential_capacity`: suitability, promise, capacity, aptitude
- `comparison_choice`: choice between two or more options
- `problem_diagnosis`: why something is blocked, unstable, delayed, difficult, or leaking
- `remedy_action`: what to do, remedy, upay, fix, action
- `topic_reading`: focused reading when no other answer mode fits

EVIDENCE PLAN:
- Return `evidence_plan` as the data-collection plan for backend agents.
- Use enum values only.
- Split compound questions into multiple `question_parts`.
- Planner chooses evidence needs; agents own detailed astrology rule combinations.
- Always include blocked content checks for `death_prediction` and `fetal_sex_determination`.
- For direct dasha/date questions, add evidence need kind `dasha_timeline_lookup` with params like {{"planet":"Mercury","level":"mahadasha","operation":"find_start_end"}}.
- For event timing like marriage, add `natal_topic_foundation`, `future_dasha_event_windows`, and `transit_event_windows` with `event_profile":"marriage"`.

TARGET SUBJECT:
- Use `self` for the native unless the user clearly asks about spouse, child, sibling, parent, etc.
- Allowed values: self, spouse, wife, husband, partner, child, first_child, second_child, third_child, mother, father, sibling, brother, sister, younger_brother, younger_sister, younger_sibling, elder_brother, elder_sister, elder_sibling, maternal_uncle, uncle.

CATEGORY for "when will I…" life-event questions (CRITICAL):
- Never use `category: "timing"` as a substitute for the life area. `timing` is only when there is no identifiable topic (e.g. "when will it happen?" with no subject).
- Pick the most specific `category` from the allowed list: job, career, marriage, love, relationship, child, pregnancy, wealth, money, health, property, visa, travel, etc.
- Examples: "When will I get a job?" -> job; "When will I get married?" / "Shaadi kab?" -> marriage; "When will I have a baby?" -> child or pregnancy; "When will my ex come back?" -> relationship; "Kab naukri milegi?" -> job.

Return ONLY this JSON shape:
{{
  "status": "CLARIFY" or "READY",
  "clarification_question": "short question only when status=CLARIFY",
  "chart_insights": [],
  "mode": "PREDICT_DAILY" or "PREDICT_PERIOD_OUTLOOK" or "LIFESPAN_EVENT_TIMING" or "LIFE_TERMINATION_RESEARCH" or "ANALYZE_TOPIC_POTENTIAL" or "ANALYZE_PERSONALITY" or "RECOMMEND_REMEDY_FOR_PROBLEM",
  "chart_focus": {{"kind":"chart_specific","primary":"D9","label":"Navamsha","explicit":true,"phrase":"navamsha","requested":["D9"]}} or null,
  "answer_mode": "explanation_mechanism" or "trait_nature" or "relationship_person" or "timing_window" or "event_prediction" or "potential_capacity" or "comparison_choice" or "problem_diagnosis" or "remedy_action" or "topic_reading",
  "target_subject_key": "self" or "spouse" or "wife" or "husband" or "partner" or "child" or "first_child" or "second_child" or "third_child" or "mother" or "father" or "sibling" or "brother" or "sister" or "younger_brother" or "younger_sister" or "younger_sibling" or "elder_brother" or "elder_sister" or "elder_sibling" or "maternal_uncle" or "uncle",
  "needs_year_clarification": false,
  "daily_intent_confirmed": true or false,
  "extracted_context": {{"timeframe":"...", "aspect":"...", "specific_date":"YYYY-MM-DD only when daily_intent_confirmed=true", "specific_date_basis":"explicit_user_day or relative_user_day or not_date_bound"}},
  "context_type": "birth" or "annual",
  "category": "career" or "job" or "promotion" or "business" or "love" or "relationship" or "marriage" or "partner" or "wealth" or "money" or "finance" or "health" or "disease" or "property" or "home" or "child" or "pregnancy" or "education" or "learning" or "travel" or "visa" or "foreign" or "gain" or "wish" or "general" or "son" or "daughter" or "mother" or "father" or "spouse" or "siblings" or "children" or "family" or "soul" or "spirituality" or "purpose" or "dharma" or "vehicles" or "timing",
  "year": "year only when annual is clearly asked",
  "needs_transits": true or false,
  "divisional_charts": ["D1","D9"],
  "transit_request": {{"startYear": 2026, "endYear": 2026, "yearMonthMap": {{"2026":["January"]}}}},
  "evidence_plan": {{
    "schema_version":"evidence_plan.v1",
    "question_parts":[{{"part_id":"p1","text":"...","intent_families":["topic_outlook"],"life_domain":"general","event_profile":null,"subject":"self","timeframe":{{"kind":"none"}},"confidence":"high"}}],
    "evidence_needs":[{{"need_id":"n1","kind":"natal_topic_foundation","system":"parashari","topic":"general","supports_parts":["p1"],"params":{{}},"priority":"required"}}],
    "safety":{{"blocked_content_checks":[{{"check_id":"death_prediction","action_if_detected":"refuse_and_redirect"}},{{"check_id":"fetal_sex_determination","action_if_detected":"refuse_and_redirect"}}],"answer_safety_checks":["no_fatalism","no_guaranteed_prediction","no_unsupported_exact_date"]}},
    "answer_plan":{{"style":"speech_concise","must_answer_parts":["p1"],"answer_order":["p1"]}}
  }}
}}
"""

        compact_prompt_enabled = _env_flag("INSTANT_INTENT_ROUTER_COMPACT_PROMPT", True)
        if compact_prompt_enabled:
            prompt = self._build_compact_instant_router_prompt(
                user_question=user_question,
                history_text=history_text,
                app_language=app_language,
                current_date=current_date,
                current_year=current_year,
                current_month=current_month,
                clarification_limit_text=clarification_limit_text,
                force_ready_instruction=force_ready_instruction,
                force_clarify_instruction=force_clarify_instruction,
            )

        model = self._get_instant_model()
        model_name = model._model_name if hasattr(model, '_model_name') else 'Unknown'
        logger.info(
            "SPEECH_PERF instant_intent_router_request model=%s prompt_chars=%s compact_prompt=%s",
            model_name,
            len(prompt),
            compact_prompt_enabled,
        )
        token_usage: Dict[str, Any] = {}
        response_chars = 0

        try:
            response = None
            gemini_start = time.time()
            last_error: Exception | None = None
            first_request_timeout = _env_float("INSTANT_INTENT_ROUTER_TIMEOUT_S", 8.0)
            retry_request_timeout = _env_float("INSTANT_INTENT_ROUTER_RETRY_TIMEOUT_S", 10.0)
            first_wall_timeout = max(first_request_timeout + 2.0, _env_float("INSTANT_INTENT_ROUTER_WALL_TIMEOUT_S", 10.0))
            retry_wall_timeout = max(retry_request_timeout + 2.0, _env_float("INSTANT_INTENT_ROUTER_RETRY_WALL_TIMEOUT_S", 12.0))
            for attempt in range(2):
                try:
                    per_request_timeout = first_request_timeout if attempt == 0 else retry_request_timeout
                    wall_timeout = first_wall_timeout if attempt == 0 else retry_wall_timeout
                    attempt_started = time.time()
                    logger.info(
                        "SPEECH_PERF instant_intent_router_attempt attempt=%s model=%s request_timeout_s=%.1f wall_timeout_s=%.1f",
                        attempt + 1,
                        model_name,
                        per_request_timeout,
                        wall_timeout,
                    )
                    response = await asyncio.wait_for(
                        model.generate_content_async(
                            prompt,
                            request_options={"timeout": per_request_timeout},
                        ),
                        timeout=wall_timeout,
                    )
                    logger.info(
                        "SPEECH_PERF instant_intent_router_attempt_done attempt=%s elapsed_ms=%.1f",
                        attempt + 1,
                        (time.time() - attempt_started) * 1000.0,
                    )
                    break
                except Exception as attempt_exc:
                    last_error = attempt_exc
                    if attempt == 0 and _is_transient_intent_error(attempt_exc):
                        logger.warning(
                            "SPEECH_PERF instant_intent_router_retry attempt=%s elapsed_ms=%.1f error=%s",
                            attempt + 1,
                            (time.time() - attempt_started) * 1000.0,
                            str(attempt_exc)[:180],
                        )
                        await asyncio.sleep(0.35 + random.uniform(0.05, 0.2))
                        continue
                    raise
            if response is None and last_error is not None:
                raise last_error
            gemini_time = time.time() - gemini_start
            cleaned = response.text.replace('```json', '').replace('```', '').strip()
            response_chars = len(cleaned)
            try:
                usage_meta = getattr(response, "usage_metadata", None)
                if usage_meta is not None:
                    token_usage = {
                        "input_tokens": int(getattr(usage_meta, "prompt_token_count", 0) or 0),
                        "output_tokens": int(getattr(usage_meta, "candidates_token_count", 0) or 0),
                        "cached_tokens": int(getattr(usage_meta, "cached_content_token_count", 0) or 0),
                        "total_tokens": int(getattr(usage_meta, "total_token_count", 0) or 0),
                    }
                    token_usage["non_cached_input_tokens"] = max(
                        0,
                        int(token_usage.get("input_tokens") or 0)
                        - int(token_usage.get("cached_tokens") or 0),
                    )
            except Exception:
                pass
            result = json.loads(cleaned)
            total_time = time.time() - intent_start
            logger.info(
                "SPEECH_PERF instant_intent_router_response status=%s mode=%s category=%s llm_s=%.2f total_s=%.2f response_chars=%s tokens_in=%s tokens_out=%s",
                result.get("status"),
                result.get("mode"),
                result.get("category"),
                gemini_time,
                total_time,
                response_chars,
                token_usage.get("input_tokens"),
                token_usage.get("output_tokens"),
            )
            final = self._finalize_router_result(
                result,
                user_question=user_question,
                current_year=current_year,
                current_month=current_month,
                resolved_now=resolved_now,
                normalized_query_context=normalized_query_context,
                include_chart_insights=False,
                d1_chart=d1_chart,
            )
            final["_llm_usage_stage"] = _build_usage_stage(
                stage="instant_intent_router",
                llm_model=model_name,
                prompt_chars=len(prompt),
                response_chars=response_chars,
                token_usage=token_usage,
                success=True,
                elapsed_ms=gemini_time * 1000.0,
            )
            return final
        except Exception as e:
            total_time = time.time() - intent_start
            logger.exception(
                "instant_intent_classification_failed total_s=%.3f error=%s",
                total_time,
                e,
            )
            fallback = self._build_fallback_intent_result(
                user_question=user_question,
                current_year=current_year,
                current_month=current_month,
                resolved_now=resolved_now,
                normalized_query_context=normalized_query_context,
            )
            fallback["_llm_usage_stage"] = _build_usage_stage(
                stage="instant_intent_router",
                llm_model=model_name,
                prompt_chars=len(prompt),
                response_chars=response_chars,
                token_usage=token_usage,
                success=False,
                elapsed_ms=(time.time() - intent_start) * 1000.0,
            )
            return fallback
        
    async def classify_intent(self, user_question: str, chat_history: list = None, user_facts: dict = None, clarification_count: int = 0, language: str = 'english', force_ready: bool = False, d1_chart: dict = None, force_clarify: bool = False, query_context: Dict[str, Any] | None = None) -> Dict[str, str]:
        """
        Returns: {'status': 'CLARIFY' | 'READY', 'mode': 'PREDICT_DAILY' | 'ANALYZE_PERSONALITY' | ..., 'category': 'job'|'love'|..., 'needs_transits': bool, 'transit_request': {...}, 'extracted_context': {...}, 'context_type': 'birth' | 'annual'}
        """
        chat_history = chat_history or []
        user_facts = user_facts or {}
        import time
        from datetime import datetime
        
        intent_start = time.time()
        resolved_now = resolve_query_now(query_context)
        normalized_query_context = normalize_query_context(query_context)
        current_year = resolved_now.year
        current_month = resolved_now.strftime('%B')
        current_date = resolved_now.strftime('%Y-%m-%d')
        
        # Build conversation context
        history_text = ""
        if chat_history:
            history_text = "\n\nPrevious conversation (FOR CONTEXT ONLY):\n"
            history_text += "⚠️ RELEVANCE RULE: ONLY refer to this history if the current question is a follow-up or directly linked to these past messages. If the user has shifted to a new topic, IGNORE the specifics of the history below.\n"
            for msg in chat_history[-3:]:
                history_text += f"Q: {msg.get('question', '')}\nA: {msg.get('response', '')}\n"
        
        # Build user facts context
        facts_text = ""
        if user_facts:
            facts_text = "\n\nKNOWN USER BACKGROUND:\n"
            facts_text += "⚠️ RELEVANCE RULE: ONLY use these facts if they are directly relevant to the current question's life area. Do NOT mention unrelated situational context from the background.\n"
            for category, items in user_facts.items():
                fact_str = ", ".join(items) if isinstance(items, list) else str(items)
                facts_text += f"- {category.upper()}: {fact_str}\n"
            facts_text += "\nIMPORTANT: Do NOT ask for information already present in the user background.\n"
        
        # Add clarification limit enforcement
        clarification_limit_text = ""
        multi_question_instruction = ""
        if clarification_count < 1:
            multi_question_instruction = r"""
MULTI-QUESTION IN ONE MESSAGE (WHEN status WOULD BE "CLARIFY"):
Clarify only when the user's current message explicitly packs SEVERAL distinct, unrelated questions into one. Strong signals include two or more question marks, numbered asks like "1. ... 2. ...", phrases like "another question" / "few questions" / "I have two questions", or clearly separate unrelated topics joined with ";" / "also".
- Do NOT invent multiple questions from one integrated question.
- Related facets inside one domain are ONE question, not multiple questions. Examples:
  - marriage + spouse + husband/wife + relationship = one relationship/marriage question
  - career + job + promotion + salary/income = one career/earnings question
  - health + stress + work pressure = one health/stress question
  - timing + description of the same event/person = one timing question
- If the user asks one coherent question with related facets, return READY and classify the dominant domain.

If the message truly has several unrelated asks, then:
- Your "clarification_question" MUST still do your normal narrowing (which area, timeframe, etc.).
- In the SAME language as the clarification (Hindi Devanagari for Hindi/Hinglish users per rules above), add ONE short polite sentence asking them to ask **one question at a time** so the reading can stay focused and detailed. Keep tone warm—not scolding.
- If you already included that idea, do not repeat it.

"""

        if clarification_count >= 1:
            clarification_limit_text = f"""

🚨🚨🚨 CRITICAL: CLARIFICATION LIMIT REACHED 🚨🚨🚨

You have ALREADY asked {clarification_count} clarification question(s).
The conversation history above shows your previous clarification question.
The current user message is their ANSWER to your clarification.

You are ABSOLUTELY FORBIDDEN from asking another clarification question.

You MUST:
1. Return status: "READY" 
2. Extract the category/timeframe from the user's answer
3. Set appropriate mode, needs_transits, and transit_request based on the COMBINED context of:
   - The original question (in conversation history)
   - The user's clarification answer (current question)

DO NOT generate a "clarification_question" field.
PROCEED WITH ANALYSIS NOW.
"""
        
        _lang = str(language or "english").strip() or "english"
        language_policy = resolve_output_language_policy(_lang, user_question)
        app_language = language_policy.get("app_language", _lang)
        language_instruction = f"""🚨 CRITICAL LANGUAGE RULE — THE LLM MUST INFER CURRENT QUESTION LANGUAGE:

The app-selected language is "{app_language}", but this is only UI context. Do not blindly follow it.

You must infer the language of CURRENT QUESTION yourself and use that same language and natural script for every user-visible JSON string:
1) If status is "CLARIFY": "clarification_question" MUST be in the language of CURRENT QUESTION.
2) If status is "READY": do not generate UI preview insight text; the backend computes those separately.

Examples:
- English question -> English strings.
- Hindi Devanagari question -> Hindi strings in Devanagari.
- Hinglish / Roman Hindi question -> respond in Roman Hindi (same script style as question), not Devanagari conversion.
- Tamil question -> Tamil strings.
- Telugu/Gujarati/Marathi/Bengali/French/German/Russian/Chinese/etc. question -> same language and script.

Only if CURRENT QUESTION is too short or language-ambiguous, use app-selected language "{app_language}" as fallback.
JSON keys stay English; only end-user string values change language.
"""

        force_ready_instruction = ""
        if force_ready:
            force_ready_instruction = f"""
🚨🚨🚨 ABSOLUTE OVERRIDE - CLARIFICATION FORBIDDEN 🚨🚨🚨

You are ABSOLUTELY REQUIRED to return status: "READY".
You are ABSOLUTELY FORBIDDEN from returning status: "CLARIFY".
You MUST NOT generate a clarification_question.

The clarification limit has been reached OR this is a partnership analysis.
PROCEED WITH ANALYSIS IMMEDIATELY.

If the question seems vague, make reasonable assumptions and proceed.
Set appropriate mode, category, and divisional_charts based on the question context.
"""

        force_clarify_instruction = ""
        if force_clarify:
            force_clarify_instruction = """
🚨🚨🚨 ABSOLUTE OVERRIDE - RETURN CLARIFICATION 🚨🚨🚨

You are ABSOLUTELY REQUIRED to return status: "CLARIFY".
You are ABSOLUTELY FORBIDDEN from returning status: "READY".

You MUST generate exactly ONE concise "clarification_question" that asks the user to pick one topic/question first.
The choices MUST come only from topics/questions explicitly present in the user's current message.
Do NOT invent generic life-area choices like career, relationships, or health unless those are actually in the user's message.
Keep it warm and polite. Do not ask for birth details.
The clarification_question MUST follow the language rule and use the inferred CURRENT QUESTION language/script.
"""

        clarification_format_instruction = """
CLARIFICATION FORMAT RULE (FOR USER-FRIENDLY QUICK REPLIES):
- When status is "CLARIFY" and you are presenting multiple choices, format the clarification so users can reply with a single letter.
- Use wording like: "Type A for ..., Type B for ..., Type C for ...".
- IMPORTANT: Do NOT hardcode exactly 3 options. Use only the number naturally needed (usually 2-5).
- Use Type A / Type B options only after you have decided CLARIFY is genuinely needed. Never create Type A / Type B choices by splitting a single coherent question into imaginary sub-questions.
- The options MUST be based on topics the user actually mentioned. Never offer unrelated defaults such as career, relationships, or health for an unusual single-topic question.
- If only 2 choices are needed, provide only A-B. If 4 are needed, provide A-D, etc.
- End with a short fallback like: "or type your topic in your own words."
- Keep the full clarification in the inferred CURRENT QUESTION language/script.
"""

        prompt = f"""
        You are a clarification assistant for an astrology chatbot. Your job is to determine if a question is too vague and needs clarification, and to classify the user's intent.
        
        🚨 ABSOLUTE PROHIBITION - NEVER ASK FOR BIRTH DETAILS:
        - The user's complete birth chart data is ALREADY PROVIDED in the D1_CHART_DATA below
        - You have access to ALL planetary positions, houses, and signs
        - NEVER ask for birth date, time, place, or any birth information
        - If a question seems to need birth details, use the provided chart data to answer
        - Do NOT ask generic life-area clarification for a single understandable question
        - If a single question asks about one identifiable theme, including spiritual guidance, identity, life purpose, remedies, family, or relationships, classify it to the closest category and return READY
        - Ask clarification only when the user's message is truly broad (for example "tell me about my life") or explicitly bundles multiple unrelated questions
        - Never invent generic choices like career, relationships, or health unless those are actually the competing topics in the user's message
        
        {force_ready_instruction}
        {force_clarify_instruction}
        {clarification_format_instruction}
        {language_instruction}

        CURRENT DATE CONTEXT:
        - Today's Date: {current_date}
        - Current Year: {current_year}
        - Current Month: {current_month}
        
        IMPORTANT: When user asks about "next 3 months", "next 6 months", or relative time periods, calculate from TODAY'S DATE ({current_date}).
        Example: If today is 2024-12-20 and user asks "next 3 months", that means January-March 2025, NOT 2024.
        {history_text}
        {facts_text}
        {clarification_limit_text}
        {multi_question_instruction}
        
        Current question: "{user_question}"
        
        CRITICAL FOLLOW-UP DETECTION:
        1. If the PREVIOUS assistant message was a FULL ANSWER (not a clarification question), and the current user message is:
           - A correction ("that's wrong", "incorrect", "planet position is wrong")
           - A follow-up ("tell me more", "what about...", "and...")
           - A clarification request ("what do you mean", "explain")
           - A short response referring to previous context ("yes", "no", "okay", single words)
           Then: Return status: "READY" immediately WITHOUT asking clarification. This is a continuation of the previous conversation.
        
        2. If the PREVIOUS assistant message was a clarification question asking which area to focus on, and the current user message is answering that (e.g., "career", "about my career", "health"), then:
           - Extract the area from the user's response
           - Return status: "READY" with the extracted category
           - Combine the original question context with the user's clarification response
        
        DIVISIONAL CHART DETECTION:
        Set `divisional_charts` to the **exact list** for the chosen `category` below (include **Karkamsa** / **Swamsa** when listed — they are required for those topics). You may **add** extra divisionals if clearly useful, but you must **never omit** any chart from the category's list. **D1** is always the radix; **D9 (Navamsa)** is the standard harmonic companion unless a row below specifies otherwise.

        Quick legend (what each divisional is for): D3 siblings/courage; D4 property/comforts/land; D7 partnerships/marriage; D9 overall strength & spouse nature; D10 career/status; D12 parents & foreign residence; D16 vehicles; D20 devotion/spiritual depth; D24 higher education & scholastic depth; D30 health & disease; **Karkamsa** = soul-purpose / career-spirit line from Chara Karakas; **Swamsa** = Atmakaraka in Navamsa (soul's path).

        CATEGORY → REQUIRED divisional_charts (copy exactly):
        - marriage, partner, spouse → ["D1", "D9", "D7"]
        - love, relationship → ["D1", "D7", "D9"]
        - career, job, promotion, business, wealth, money, finance → ["D1", "D9", "D10", "Karkamsa"]
        - soul, spirituality → ["D1", "D9", "D20", "Swamsa"]
        - purpose, dharma → ["D1", "D9", "Karkamsa", "Swamsa"]
        - health → ["D1", "D9", "D30"]
        - disease → ["D1", "D9", "D30"]
        - children, child, pregnancy, son, daughter → ["D1", "D7", "D9"]
        - siblings → ["D1", "D3", "D9"]
        - property (land, buildings, ancestral assets) → ["D1", "D4", "D9", "D12"]
        - home (living space, domestic comfort — not investment land) → ["D1", "D4", "D9"]
        - mother → ["D1", "D4", "D9", "D12"]
        - father → ["D1", "D9", "D10", "D12"]
        - education, learning → ["D1", "D9", "D24"]
        - vehicles → ["D1", "D4", "D16"]
        - travel → ["D1", "D3", "D9"]
        - foreign, visa → ["D1", "D9", "D12"]
        - family → ["D1", "D9", "D12"]
        - timing (generic timing without a clearer life-area) → ["D1", "D9"]
        - general, gain, wish (or unclear topic) → ["D1", "D9"]

        Examples tying question wording to lists:
        - "When will I get married?" → category marriage → ["D1", "D9", "D7"]
        - "How is my career / promotion?" → category career or promotion → ["D1", "D9", "D10", "Karkamsa"]
        - "Tell me about my siblings" → category siblings → ["D1", "D3", "D9"]
        - "Property / land / home purchase?" → category property → ["D1", "D4", "D9", "D12"]
        - "Health / illness?" → category health or disease → ["D1", "D9", "D30"]

        🚨 EDUCATION / HIGHER STUDY (category "education" or "learning"):
        - **D24 (Chaturvimshamsha / Siddhamsha)** = higher education, Masters/PhD, depth of study — **mandatory** in the list above. **D10** = job title / career status — **not** a substitute for D24.
        - If the user mixes **Masters vs job** in one question, set category to **education** (or **learning**) and **add** "D10" so charts become at least **["D1","D9","D24","D10"]** (education + career angle). Do not drop D24 in favor of only D10.
        
        CONTEXT_TYPE:
        1. "annual": For YEARLY forecasts, specific calendar years (e.g. "How is my 2026?", "What does next year hold?", "How is my career in 2026?")
        2. "birth": For general life analysis, personality, "When will..." timing questions, DAILY/SPECIFIC DATE questions (e.g. "When will I get married?", "What are my strengths?", "What events on Feb 2nd?", "How is today?", "What about this month?")

        🚨 CRITICAL CONTEXT_TYPE DISTINCTION:
        - Questions about SPECIFIC DAYS, DATES, or SHORT PERIODS (today, this week, this month) → ALWAYS use "birth" context_type.
        - Questions about ENTIRE YEARS or ANNUAL FORECASTS → use "annual" context_type.

        SPECIFIC DATE EXTRACTION:
        - If the user is asking about an exact day, relative day, or clearly date-bound daily event, you MUST return `extracted_context.specific_date` in normalized `YYYY-MM-DD` format.
        - Examples:
          - "How is today?" → use TODAY'S DATE from the current date context above.
          - "How is tomorrow?" → resolve relative to TODAY'S DATE from the current date context above.
          - "What will happen on 12th Sep 2028?" → `2028-09-12`
        - If the question is not about one exact day, leave `extracted_context.specific_date` empty or omit it.

        DAILY INTENT CONFIRMATION:
        - Daily mode is opt-in. Set `daily_intent_confirmed=true` only when the user's actual question is about one exact/relative day.
        - Date ranges are NOT daily, even when they contain exact dates. For "between 19 Jun and 25 Jun", "from 19 Jun to 25 Jun", or "19 Jun-25 Jun", do NOT set `PREDICT_DAILY`, do NOT set `specific_date`, set `daily_intent_confirmed=false`, and use `PREDICT_PERIOD_OUTLOOK` or event timing for the whole range.
        - Set `extracted_context.specific_date_basis` to:
          - "explicit_user_day" when the user named a specific date/day
          - "relative_user_day" when the user asked today/tomorrow/day-after-tomorrow
          - "not_date_bound" for ongoing problems, current-life distress, broad timing questions, annual/period questions, or remedy/problem questions
        - Do NOT set `specific_date` merely because Today's Date is in the prompt. Today is context, not user intent.
        - Non-exhaustive calibration examples (use the principle, do not force-fit only these examples):
          - "Since this year started my life is disturbed, when will things improve?" → NOT daily; use PREDICT_PERIOD_OUTLOOK or LIFESPAN_EVENT_TIMING
          - "Meri life disturbed hai, kab tak thik hoga?" → NOT daily; use timing/problem analysis
          - "Will I travel between 19 Jun and 25 Jun?" → NOT daily; use PREDICT_PERIOD_OUTLOOK for the full range
          - "Aaj ka din kaisa rahega?" → daily with relative_user_day
          - "27 May 2026 kaisa rahega?" → daily with explicit_user_day

        TRANSIT DETECTION:
        - "When will..." questions → needs_transits: true
        - "What period is good for..." → needs_transits: true
        - "How is 2025/next year..." → needs_transits: true
        - Career questions about promotions/hikes → needs_transits: true
        - Personality/yoga/general questions → needs_transits: false

        CRITICAL: For ANY context_type requiring transits, set startYear and endYear to ONLY the specific year/period mentioned.
        - "2026" → startYear: 2026, endYear: 2026
        - "next year" → startYear: {current_year + 1}, endYear: {current_year + 1}
        - General timing questions ("when will I...") → startYear: {current_year}, endYear: {current_year + 2}

        MODES (USER INTENT):
        You must choose one of the following modes based on the user's question. This determines the structure of the final answer.

        - "PREDICT_DAILY": For explicit one-day predictions only (e.g., "How is today?", "What's in store for me tomorrow?", "How will 27 May 2026 be?").
        - "LIFESPAN_EVENT_TIMING": For open-ended "When" questions about major life events (e.g., "When will I get married?", "When did I buy my house?", "When will my daughter get married?", "In which year did I get married?"). 
          🚨 CRITICAL: Use this mode when the user's message is **primarily** a single timing question about one life event.
          🚨 EXCEPTION — BUNDLED MULTI-TOPIC MESSAGES: If the same message also asks **other unrelated** things (e.g. spouse nature, career, wealth, health) in separate sentences or clauses, you MUST NOT force READY just because one part is a "when" question. Return status: "CLARIFY" and ask which **one** topic to address first (or to send one question at a time), unless the clarification limit already applies.
          🚨 When the message is **only** a when/year question about one topic: return status: "READY" with this mode. Do not ask clarification for that narrow case.
        - "LIFE_TERMINATION_RESEARCH": Restricted mode for explicit death/life-termination/lifespan-end timing questions only when the configured unlock phrase is present in the current question. Use D1/D3/D8/D9/D30, health category, and broad lifetime timing; do not use ordinary daily or generic lifespan-event timing for these unlocked questions.
        - "PREDICT_PERIOD_OUTLOOK": For general questions about a specific timeframe (e.g., "How will the next 6 months be for my career?"). This is for a deep-dive analysis.
        - "PREDICT_EVENT_TIMING": For "when will X happen?" questions (e.g., "When will I get married?").
        - "PREDICT_EVENTS_FOR_PERIOD": For listing numerous potential events over a period (e.g., "Tell me all events for this year."). This is for a timeline-style list.
        - "ANALYZE_TOPIC_POTENTIAL": Assesses the potential of a life area (e.g., "Tell me about my financial prospects.").
        - "ANALYZE_PERSONALITY": Describes the user's character based on their chart (e.g., "What does my chart say about me?", "What are my strengths?").
        - "ANALYZE_ROOT_CAUSE": For deep-seated "why" questions (e.g., "Why do I always struggle with self-confidence?").
        - "RECOMMEND_REMEDY_FOR_PROBLEM": Suggests remedies for a specific issue (e.g., "I have a lot of anxiety. What can I do?").

        CHART-FOCUS DETECTION:
        Decide whether the user is asking for a specific chart/lens reading rather than a normal life-topic reading.
        - If the user explicitly or implicitly wants a chart-lens reading, set `chart_focus`.
        - Examples that SHOULD set `chart_focus`:
          - "Analyze my D10"
          - "Read my navamsha"
          - "Analyze my lagna"
          - broken but clear variants like "career in d10 tell"
        - Examples that should NOT set `chart_focus`:
          - "Tell me about my career"
          - "What career suits me from my chart"
          - "Marriage prospects in my birth chart"
        - Mentioning "chart" alone is NOT enough. Only set `chart_focus` when a specific lens/chart is actually the requested object.

        Return ONLY a JSON object:
        {{
            "status": "CLARIFY" or "READY",
            "clarification_question": "Your clarifying question here (only if status=CLARIFY; when giving options, use lettered quick replies like Type A/Type B with variable count, not fixed 3; keep same language + script as CURRENT QUESTION)",
            "chart_insights": [],
            "mode": "PREDICT_DAILY" or "PREDICT_PERIOD_OUTLOOK" or "LIFESPAN_EVENT_TIMING" or "LIFE_TERMINATION_RESEARCH" or "PREDICT_EVENT_TIMING" or "PREDICT_EVENTS_FOR_PERIOD" or "ANALYZE_TOPIC_POTENTIAL" or "ANALYZE_PERSONALITY" or "ANALYZE_ROOT_CAUSE" or "RECOMMEND_REMEDY_FOR_PROBLEM",
            "chart_focus": {{
                "kind": "chart_specific",
                "primary": "D1 or D9 or D10 or D7 or Karkamsa or Swamsa",
                "label": "Lagna or D10 or Navamsha",
                "explicit": true,
                "phrase": "the phrase or implied lens you detected",
                "requested": ["D10"]
            }} or null,
            "daily_intent_confirmed": true or false,
            "extracted_context": {{ "timeframe": "2025", "aspect": "promotion", "specific_date": "YYYY-MM-DD only when daily_intent_confirmed=true", "specific_date_basis": "explicit_user_day or relative_user_day or not_date_bound" }},
            "context_type": "annual" or "birth",
            "category": "category_name",
            "year": "SPECIFIC_YEAR_FROM_QUESTION (only for annual context_type)",
            "needs_transits": true or false,
            "divisional_charts": ["D3", "D9", "D10"],
            "transit_request": {{
                "startYear": "SPECIFIC_YEAR_FROM_QUESTION",
                "endYear": "SPECIFIC_YEAR_FROM_QUESTION",
                "yearMonthMap": {{
                    "SPECIFIC_YEAR_FROM_QUESTION": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                }}
            }}
        }}

        Categories: job, career, promotion, business, love, relationship, marriage, partner, wealth, money, finance, health, disease, property, home, child, pregnancy, education, learning, travel, visa, foreign, gain, wish, general, son, daughter, mother, father, spouse, siblings, children, family, soul, spirituality, purpose, dharma, vehicles, timing
        """
        
        model = self._get_model()
        model_name = model._model_name if hasattr(model, '_model_name') else 'Unknown'
        
        try:
            gemini_start = time.time()
            # Keep intent classification fast; slow/hung calls should fall back quickly.
            response = await asyncio.wait_for(
                model.generate_content_async(
                    prompt,
                    request_options={"timeout": 25},
                ),
                timeout=30.0,
            )
            gemini_time = time.time() - gemini_start
            
            cleaned = response.text.replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned)
            
            total_time = time.time() - intent_start
            logger.info(
                "intent router complete status=%s mode=%s category=%s model=%s duration_ms=%.1f",
                result.get('status'),
                result.get('mode'),
                result.get('category'),
                model_name,
                total_time * 1000.0,
            )
            
            return self._finalize_router_result(
                result,
                user_question=user_question,
                current_year=current_year,
                current_month=current_month,
                resolved_now=resolved_now,
                normalized_query_context=normalized_query_context,
                include_chart_insights=False,
                d1_chart=d1_chart,
            )
        except Exception as e:
            total_time = time.time() - intent_start
            logger.warning("intent classification failed after %.3fs: %s", total_time, e)
            return self._build_fallback_intent_result(
                user_question=user_question,
                current_year=current_year,
                current_month=current_month,
                resolved_now=resolved_now,
                normalized_query_context=normalized_query_context,
            )
    
    def _get_default_divisional_charts(self, category: str) -> list:
        """Get default divisional charts based on question category (see _DEFAULT_DIVISIONAL_CHARTS_BY_CATEGORY)."""
        return get_default_divisional_charts_for_category(category)
