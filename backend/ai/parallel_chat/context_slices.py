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
}


def build_sudarshan_shared_kernel_lite(context: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal frame: birth, ascendant, dates, response_format, intent. No D1, no Vimshottari blobs."""
    kernel = _pick_keys(context, _SUDARSHAN_KERNEL_KEYS)
    if context.get("intent") is not None:
        kernel["intent"] = copy.deepcopy(context["intent"])
    return kernel


def build_sudarshan_branch_payload(context: Dict[str, Any], user_question: str) -> Dict[str, Any]:
    """VARIABLE_DATA_JSON for the Sudarshan parallel branch: minimal frame + sudarshana_* only."""
    return {
        "shared_kernel": build_sudarshan_shared_kernel_lite(context),
        "sudarshana_context": build_sudarshan_slice(context),
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
