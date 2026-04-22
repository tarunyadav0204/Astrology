"""Build per-branch context payloads from the same merged dict as legacy chat."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Set, Tuple

# Same mapping as ChatContextBuilder.build_complete_context (intent filter).
DIVISIONAL_CODE_TO_KEY: Dict[str, str] = {
    "D3": "d3_drekkana",
    "D4": "d4_chaturthamsa",
    "D7": "d7_saptamsa",
    "D9": "d9_navamsa",
    "D10": "d10_dasamsa",
    "D12": "d12_dwadasamsa",
    "D16": "d16_shodasamsa",
    "D20": "d20_vimsamsa",
    "D24": "d24_chaturvimsamsa",
    "D27": "d27_nakshatramsa",
    "D30": "d30_trimsamsa",
    "D40": "d40_khavedamsa",
    "D45": "d45_akshavedamsa",
    "D60": "d60_shashtiamsa",
}

_PARASHARI_KEYS: Set[str] = {
    "birth_details",
    "ascendant_info",
    "d1_chart",
    "divisional_charts",
    "planetary_analysis",
    "d9_planetary_analysis",
    "friendship_analysis",
    "current_dashas",
    "house_lordships",
    "transit_activations",
    "period_dasha_activations",
    "macro_transits_timeline",
    "unified_dasha_timeline",
    "requested_dasha_summary",
    "yogini_dasha",
    "kalchakra_dasha",
    "shoola_dasha",
    "dasha_conflicts",
    "yogas",
    "advanced_analysis",
    "sniper_points",
    "special_points",
    "kota_chakra",
    "sudarshana_chakra",
    "intent",
    "analysis_type",
    "user_facts",
    "extracted_context",
    "current_date_info",
    "response_format",
}


def _pick_keys(src: Dict[str, Any], keys: Set[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in keys:
        if k in src and src[k] is not None:
            out[k] = copy.deepcopy(src[k])
    return out


_SHARED_KERNEL_KEYS: Set[str] = {
    "birth_details",
    "ascendant_info",
    "d1_chart",
    "current_date_info",
    "response_format",
    # Vimshottari spine + intent-driven windows (present / past / future as computed by chat builder)
    "current_dashas",
    "requested_dasha_summary",
    "period_dasha_activations",
    "unified_dasha_timeline",
}


def build_shared_kernel(context: Dict[str, Any]) -> Dict[str, Any]:
    """Shared spine for every branch: birth, D1, today, intent, Vimshottari + period dasha fields."""
    kernel = _pick_keys(context, _SHARED_KERNEL_KEYS)
    if context.get("intent") is not None:
        kernel["intent"] = copy.deepcopy(context["intent"])
    return kernel


# Specialist parallel branches do not need full timeline blobs (those live in parashari_context or merge).
# Omitting these avoids ~5–6× duplication of the heaviest JSON across concurrent LLM calls.
_PARALLEL_KERNEL_LITE_KEYS: Set[str] = {
    "birth_details",
    "ascendant_info",
    "d1_chart",
    "current_date_info",
    "response_format",
    "current_dashas",
    "requested_dasha_summary",
}


def build_shared_kernel_lite(context: Dict[str, Any]) -> Dict[str, Any]:
    """Light spine for non-Parashari branches: no unified_dasha_timeline / period_dasha_activations."""
    kernel = _pick_keys(context, _PARALLEL_KERNEL_LITE_KEYS)
    if context.get("intent") is not None:
        kernel["intent"] = copy.deepcopy(context["intent"])
    return kernel


def without_keys(d: Dict[str, Any], omit: Set[str]) -> Dict[str, Any]:
    """Shallow copy of d without omitted keys (used to drop keys duplicated in a branch slice)."""
    return {k: v for k, v in d.items() if k not in omit}


def build_parashari_slice(context: Dict[str, Any]) -> Dict[str, Any]:
    """D1 + D9 + intent divisionals + Vimshottari-aligned dashas + transits + Parashari blocks (no Chara Dasha — Jaimini branch)."""
    return _pick_keys(context, _PARASHARI_KEYS)


def build_jaimini_slice(context: Dict[str, Any]) -> Dict[str, Any]:
    keys = {
        "jaimini_points",
        "chara_karakas",
        "relationships",
        "chara_dasha",
        "jaimini_full_analysis",
        "yogini_dasha",
        "current_dashas",
        "intent",
        "current_date_info",
        "response_format",
    }
    return _pick_keys(context, keys)


def build_nadi_slice(context: Dict[str, Any]) -> Dict[str, Any]:
    keys = {"nadi_links", "nadi_age_activation", "intent", "current_date_info", "response_format"}
    return _pick_keys(context, keys)


_ASHTAKAVARGA_KEYS: Set[str] = {
    "ashtakavarga",
    "ascendant_info",
    "birth_details",
    "d1_chart",
    "house_lordships",
    "intent",
    "current_date_info",
    "response_format",
}


def build_ashtakavarga_slice(context: Dict[str, Any]) -> Dict[str, Any]:
    """SAV/BAV (+ optional D9 AV) + frame for mapping bindus to houses.

    Injects `Ho` / `La` onto `ashtakavarga.d1_rashi` when ascendant is known so house-numbered
    bindus match whole-sign houses from lagna (flat SAV/BAV rows remain zodiac-indexed).
    """
    base = _pick_keys(context, _ASHTAKAVARGA_KEYS)
    out = copy.deepcopy(base)
    av_root = out.get("ashtakavarga")
    if not isinstance(av_root, dict):
        return out
    d1 = av_root.get("d1_rashi")
    if not isinstance(d1, dict) or not d1:
        return out
    from context_agents.agents.ashtakavarga import _asc_sign_0_from_static, _compact_d1_block

    asc0 = _asc_sign_0_from_static(
        {"ascendant_info": out.get("ascendant_info"), "d1_chart": out.get("d1_chart")}
    )
    compact = _compact_d1_block(d1, asc_sign_0=asc0)
    if asc0 is None or "Ho" not in compact:
        return out
    dr = copy.deepcopy(d1)
    dr["Ho"] = compact["Ho"]
    dr["La"] = compact["La"]
    ar = copy.deepcopy(av_root)
    ar["d1_rashi"] = dr
    out["ashtakavarga"] = ar
    return out


_KP_SLICE_KEYS: Set[str] = {
    "kp_analysis",
    "ascendant_info",
    "birth_details",
    "d1_chart",
    "house_lordships",
    "intent",
    "current_date_info",
    "response_format",
}


def build_kp_slice(context: Dict[str, Any]) -> Dict[str, Any]:
    """KP cusp/planet lords + significators + frame (Vimshottari spine lives in shared_kernel)."""
    return _pick_keys(context, _KP_SLICE_KEYS)


_SUDARSHAN_SLICE_KEYS: Set[str] = {
    "sudarshana_chakra",
    "sudarshana_dasha",
}


def build_sudarshan_slice(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sudarshana Chakra triple perspective (Lagna / Chandra / Surya rotated houses) plus optional
    Sudarshana Dasha year-clock — same keys as legacy `ChatContextBuilder` attaches to merged context.
    """
    return _pick_keys(context, _SUDARSHAN_SLICE_KEYS)


# Sudarshan branch: do NOT use build_shared_kernel_lite — that pulls d1_chart (divisions D1–D60, bhav_chalit),
# requested_dasha_summary (multi-year prana/sookshma trees), and current_dashas. Triple-chakra analysis
# only needs sudarshana_context + a thin identity/date frame.
_SUDARSHAN_KERNEL_KEYS: Set[str] = {
    "birth_details",
    "ascendant_info",
    "current_date_info",
    "response_format",
    "current_dashas",
    "requested_dasha_summary",
}

_SUDARSHANA_TARGETS: Dict[str, List[int]] = {
    "career": [10, 6, 2, 11],
    "job": [10, 6, 2, 11],
    "promotion": [10, 6, 2, 11],
    "business": [10, 7, 2, 11],
    "marriage": [7, 2, 8, 11],
    "relationship": [7, 5, 2, 11],
    "love": [5, 7, 11, 2],
    "partner": [7, 2, 8, 11],
    "spouse": [7, 2, 8, 11],
    "children": [5, 9, 2, 11],
    "child": [5, 9, 2, 11],
    "pregnancy": [5, 8, 2, 11],
    "education": [4, 5, 9, 2],
    "learning": [4, 5, 9, 2],
    "health": [1, 6, 8, 12],
    "disease": [1, 6, 8, 12],
    "property": [4, 11, 2, 8],
    "home": [4, 2, 11, 8],
    "general": [1, 5, 7, 10],
}

_SUDARSHANA_TOPIC_CODES: Tuple[str, ...] = ("career", "relationship", "education", "health")


def _sudarshana_topic_meta(context: Dict[str, Any]) -> Dict[str, Any]:
    intent = context.get("intent") or {}
    cat = str(intent.get("category") or "general").strip().lower() or "general"
    return {"cat": cat, "hs": list(_SUDARSHANA_TARGETS.get(cat, _SUDARSHANA_TARGETS["general"]))}


def _sudarshana_inverse_map(rotated: Dict[str, Any]) -> Dict[int, List[str]]:
    out: Dict[int, List[str]] = {i: [] for i in range(1, 13)}
    for planet, house in (rotated or {}).items():
        try:
            h = int(house)
        except (TypeError, ValueError):
            continue
        if 1 <= h <= 12:
            out[h].append(str(planet))
    for house in out:
        out[house].sort()
    return out


def _sudarshana_house_band(agree: int, benefics: int, malefics: int, house: int) -> str:
    supportive_houses = {1, 2, 4, 5, 7, 9, 10, 11}
    obstructive_houses = {6, 8, 12}
    if agree >= 3 and house in supportive_houses and benefics >= malefics:
        return "strong"
    if agree >= 3 and house in obstructive_houses and malefics >= benefics:
        return "hard"
    if agree >= 2:
        return "mixed"
    return "weak"


def _sudarshana_rows_for_houses(
    houses: List[int],
    lagna: Dict[int, List[str]],
    moon: Dict[int, List[str]],
    sun: Dict[int, List[str]],
) -> List[Dict[str, Any]]:
    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    rows = []
    for house in houses:
        by_view = {
            "lagna": lagna.get(house, []),
            "moon": moon.get(house, []),
            "sun": sun.get(house, []),
        }
        agree = sum(1 for occ in by_view.values() if occ)
        ben = sum(len([p for p in occ if p in benefics]) for occ in by_view.values())
        mal = sum(len([p for p in occ if p in malefics]) for occ in by_view.values())
        rows.append(
            {
                "h": house,
                "agree": agree,
                "band": _sudarshana_house_band(agree, ben, mal, house),
                "ben": ben,
                "mal": mal,
                "v": by_view,
            }
        )
    rows.sort(key=lambda row: (-int(row["agree"]), 0 if row["band"] == "strong" else 1 if row["band"] == "mixed" else 2, int(row["h"])))
    return rows


def _sudarshana_topic_block(
    topic: str,
    lagna: Dict[int, List[str]],
    moon: Dict[int, List[str]],
    sun: Dict[int, List[str]],
) -> Dict[str, Any]:
    houses = list(_SUDARSHANA_TARGETS.get(topic, _SUDARSHANA_TARGETS["general"]))
    rows = _sudarshana_rows_for_houses(houses, lagna, moon, sun)
    strong = [row["h"] for row in rows if row["band"] == "strong"]
    hard = [row["h"] for row in rows if row["band"] == "hard"]
    support = "supportive" if len(strong) > len(hard) else "challenging" if len(hard) > len(strong) else "mixed"
    return {
        "hs": houses,
        "rows": rows,
        "support": support,
        "dom": [row["h"] for row in rows[:4]],
        "strong": strong[:4],
        "hard": hard[:4],
    }


def _sudarshana_current_topic_block(
    topic: str,
    lagna: Dict[int, List[str]],
    moon: Dict[int, List[str]],
    sun: Dict[int, List[str]],
    dasha_levels: Dict[str, Any],
) -> Dict[str, Any]:
    houses = list(_SUDARSHANA_TARGETS.get(topic, _SUDARSHANA_TARGETS["general"]))
    rows: List[Dict[str, Any]] = []
    strong = 0
    hard = 0
    for level in ("md", "ad", "pd"):
        drow = dasha_levels.get(level) or {}
        planet = str(drow.get("p") or "").strip()
        if not planet:
            continue
        lv = sorted([house for house in houses if planet in (lagna.get(house) or [])])
        mv = sorted([house for house in houses if planet in (moon.get(house) or [])])
        sv = sorted([house for house in houses if planet in (sun.get(house) or [])])
        agree = sum(1 for hit in (lv, mv, sv) if hit)
        touched = sorted(set(lv + mv + sv))
        if agree >= 3:
            band = "strong"
            strong += 1
        elif agree >= 2:
            band = "mixed"
        elif agree == 1:
            band = "weak"
            hard += 1
        else:
            band = "inactive"
            hard += 1
        rows.append(
            {
                "lvl": level,
                "p": planet,
                "agree": agree,
                "band": band,
                "touched": touched,
                "v": {"lagna": lv, "moon": mv, "sun": sv},
                "st": drow.get("st"),
                "en": drow.get("en"),
            }
        )
    support = "supportive" if strong > hard else "challenging" if hard > strong else "mixed"
    return {
        "hs": houses,
        "rows": rows,
        "support": support,
        "strong": [row["lvl"] for row in rows if row["band"] == "strong"],
        "hard": [row["lvl"] for row in rows if row["band"] in {"weak", "inactive"}],
    }


def _extract_current_dasha_summary(kernel: Dict[str, Any]) -> Dict[str, Any]:
    current = kernel.get("current_dashas") or {}
    requested = kernel.get("requested_dasha_summary") or {}
    base = current if isinstance(current, dict) and current else requested if isinstance(requested, dict) else {}
    if not isinstance(base, dict):
        return {}
    out = {}
    for src, dst in (("mahadasha", "md"), ("antardasha", "ad"), ("pratyantar", "pd")):
        row = base.get(src) or {}
        if not isinstance(row, dict):
            continue
        if row.get("planet"):
            out[dst] = {"p": row.get("planet"), "st": row.get("start_date"), "en": row.get("end_date")}
    return out


def _build_sudarshana_reasoning_spine(context: Dict[str, Any]) -> Dict[str, Any]:
    meta = _sudarshana_topic_meta(context)
    sud = build_sudarshan_slice(context)
    chakra = sud.get("sudarshana_chakra") or {}
    dasha = sud.get("sudarshana_dasha") or {}
    dasha_levels = _extract_current_dasha_summary(build_sudarshan_shared_kernel_lite(context))
    lagna = _sudarshana_inverse_map(chakra.get("lagna_chart") or {})
    moon = _sudarshana_inverse_map(chakra.get("chandra_lagna") or {})
    sun = _sudarshana_inverse_map(chakra.get("surya_lagna") or {})

    topic_block = _sudarshana_topic_block(meta["cat"], lagna, moon, sun)
    rows = topic_block["rows"]

    trig_rows = []
    for row in (dasha.get("precision_triggers") or []):
        if not isinstance(row, dict):
            continue
        trig_rows.append(
            {
                "dt": row.get("date"),
                "p": row.get("planet"),
                "cf": row.get("confirmation"),
                "cn": row.get("confidence"),
                "int": row.get("intensity"),
                "sg": row.get("sign"),
                "pv": list(row.get("perspectives") or []),
            }
        )

    return {
        "cat": meta["cat"],
        "hs": meta["hs"],
        "topic": topic_block,
        "career": _sudarshana_topic_block("career", lagna, moon, sun),
        "relationship": _sudarshana_topic_block("relationship", lagna, moon, sun),
        "education": _sudarshana_topic_block("education", lagna, moon, sun),
        "health": _sudarshana_topic_block("health", lagna, moon, sun),
        "current": {
            "topic": _sudarshana_current_topic_block(meta["cat"], lagna, moon, sun, dasha_levels),
            "career": _sudarshana_current_topic_block("career", lagna, moon, sun, dasha_levels),
            "relationship": _sudarshana_current_topic_block("relationship", lagna, moon, sun, dasha_levels),
            "education": _sudarshana_current_topic_block("education", lagna, moon, sun, dasha_levels),
            "health": _sudarshana_current_topic_block("health", lagna, moon, sun, dasha_levels),
        },
        "dom": [row["h"] for row in rows[:5]],
        "patterns": list(((chakra.get("synthesis") or {}).get("patterns") or []))[:6],
        "triggers": {
            "active_house": dasha.get("active_house"),
            "year_focus": dasha.get("year_focus"),
            "rows": trig_rows[:8],
        },
        "D": dasha_levels,
    }


def build_sudarshan_shared_kernel_lite(context: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal frame: birth, ascendant, dates, response_format, and a small dasha anchor."""
    kernel = _pick_keys(context, _SUDARSHAN_KERNEL_KEYS)
    if context.get("intent") is not None:
        kernel["intent"] = copy.deepcopy(context["intent"])
    return kernel


def build_sudarshan_branch_payload(context: Dict[str, Any], user_question: str) -> Dict[str, Any]:
    """VARIABLE_DATA_JSON for the Sudarshan parallel branch: minimal frame + sudarshana_* + derived spine."""
    return {
        "shared_kernel": build_sudarshan_shared_kernel_lite(context),
        "sudarshana_context": build_sudarshan_slice(context),
        "sx": _build_sudarshana_reasoning_spine(context),
        "user_question": user_question,
    }


_THIN_BASIC_KEYS: Tuple[str, ...] = (
    "nakshatra",
    "nakshatra_pada",
    "house",
    "sign_name",
    "degree",
    "exact_degree_in_sign",
    "longitude",
)


def _thin_basic_info_for_nakshatra(bi: Dict[str, Any]) -> Dict[str, Any]:
    if not bi:
        return {}
    out: Dict[str, Any] = {}
    for k in _THIN_BASIC_KEYS:
        if k in bi and bi[k] is not None:
            out[k] = copy.deepcopy(bi[k])
    return out


def _thin_planetary_for_nakshatra(planetary: Dict[str, Any]) -> Dict[str, Any]:
    if not planetary:
        return {}
    out: Dict[str, Any] = {}
    for pname, pdata in planetary.items():
        if not isinstance(pdata, dict):
            continue
        bi = pdata.get("basic_info")
        if isinstance(bi, dict):
            thin = _thin_basic_info_for_nakshatra(bi)
            out[pname] = {"basic_info": thin} if thin else {}
        else:
            out[pname] = {}
    return out


_NAKSHATRA_SLICE_KEYS: Set[str] = {
    "birth_details",
    "ascendant_info",
    "d1_chart",
    "house_lordships",
    "intent",
    "current_date_info",
    "response_format",
    "nakshatra_remedies",
    "navatara_warnings",
    "pushkara_navamsa",
}


def build_nakshatra_slice(context: Dict[str, Any]) -> Dict[str, Any]:
    """D1/D9 per-graha nakshatra rows (thinned) + remedies + navatara / pushkara hints."""
    base = _pick_keys(context, _NAKSHATRA_SLICE_KEYS)
    pa = context.get("planetary_analysis")
    d9 = context.get("d9_planetary_analysis")
    if pa is not None:
        base["planetary_analysis"] = (
            _thin_planetary_for_nakshatra(pa) if isinstance(pa, dict) else copy.deepcopy(pa)
        )
    if d9 is not None:
        base["d9_planetary_analysis"] = (
            _thin_planetary_for_nakshatra(d9) if isinstance(d9, dict) else copy.deepcopy(d9)
        )
    return base


def format_history_for_prompt(history: Optional[List[Dict[str, Any]]], max_pairs: int = 3, cap: int = 500) -> str:
    """Last N Q&A pairs (default 3), same shape as `build_final_prompt` / merge step."""
    if not history:
        return ""
    text = "\n\nLAST Q&A TURNS (FOR CONTEXT ONLY; max " + str(max_pairs) + " pairs):\n"
    text += (
        "⚠️ RELEVANCE RULE: ONLY refer to this history if the current question is a follow-up "
        "or directly linked to these past messages.\n\n"
    )
    recent = history[-max_pairs:] if len(history) >= max_pairs else history
    for msg in recent:
        q = (msg.get("question") or "")[:cap]
        r = (msg.get("response") or "")[:cap]
        text += f"User: {q}\nAssistant: {r}\n\n"
    return text
