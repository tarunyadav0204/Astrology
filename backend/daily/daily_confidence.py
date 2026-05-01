from __future__ import annotations

from typing import Any, Dict, List


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _supportive_trigger_count(ranked_triggers: List[Dict[str, Any]]) -> int:
    count = 0
    for row in ranked_triggers or []:
        strength = str(row.get("strength") or "")
        if strength in {"massive", "strong"}:
            count += 1
    return count


def _micro_intent_house_overlap(micro_intent: Dict[str, Any], daily_judgment: Dict[str, Any]) -> List[int]:
    wanted = {_as_int(h) for h in (micro_intent.get("houses") or []) if _as_int(h)}
    active = {
        _as_int(row.get("house"))
        for row in (daily_judgment.get("top_activated_houses") or [])
        if _as_int(row.get("house"))
    }
    return sorted(h for h in wanted.intersection(active) if h)


def _top_domains(daily_judgment: Dict[str, Any]) -> List[str]:
    return [str(row.get("domain") or "") for row in (daily_judgment.get("top_event_domains") or []) if row.get("domain")][:4]


def build_daily_confidence(
    *,
    daily_prediction_spine: Dict[str, Any],
    fast_planets: Dict[str, Any],
    intraday: Dict[str, Any],
    daily_micro_intent: Dict[str, Any],
) -> Dict[str, Any]:
    ranked_triggers = daily_prediction_spine.get("ranked_triggers") or []
    daily_judgment = daily_prediction_spine.get("daily_judgment") or {}
    school_judgments = daily_prediction_spine.get("school_judgments") or {}
    top_houses = daily_judgment.get("top_activated_houses") or []
    top_domains = _top_domains(daily_judgment)
    overlap_houses = _micro_intent_house_overlap(daily_micro_intent, daily_judgment)
    supportive_triggers = _supportive_trigger_count(ranked_triggers)
    massive_factors = daily_judgment.get("massive_result_factors") or []
    tara_quality = str(((daily_judgment.get("moon_tara_quality") or {}).get("quality")) or "neutral")
    kp_verdict = str(((school_judgments.get("kp") or {}).get("verdict")) or "")
    av_verdict = str(((school_judgments.get("ashtakavarga") or {}).get("verdict")) or "")
    av_conflicts = (school_judgments.get("ashtakavarga") or {}).get("conflicts") or []
    fast_summary = fast_planets.get("summary") or {}
    fast_band = str(fast_summary.get("overall_band") or "background")
    caution_windows = intraday.get("caution_windows") or []
    favorable_windows = intraday.get("favorable_windows") or []
    transition_windows = intraday.get("transition_windows") or []

    support_score = 0
    friction_score = 0
    event_score = 0
    support_factors: List[str] = []
    contradicting_factors: List[str] = []

    if supportive_triggers >= 3:
        support_score += 3
        event_score += 3
        support_factors.append("Multiple strong PR/SK/PD daily triggers are active.")
    elif supportive_triggers >= 1:
        support_score += 1
        event_score += 2
        support_factors.append("At least one strong same-day dasha trigger is active.")
    else:
        event_score -= 1
        contradicting_factors.append("No strong PR/SK/PD trigger dominates the day.")

    if massive_factors:
        support_score += 2
        event_score += 3
        support_factors.append("A natal return-style trigger can amplify results noticeably.")

    if overlap_houses:
        support_score += 2
        event_score += 1
        support_factors.append(
            f"The user's action-type overlaps with activated houses {', '.join(map(str, overlap_houses))}."
        )
    else:
        event_score -= 1
        contradicting_factors.append("The requested action-type is not strongly backed by the top activated houses.")

    if tara_quality == "supportive":
        support_score += 1
        support_factors.append("Moon tara bala supports smoother daily flow.")
    elif tara_quality == "caution":
        friction_score += 2
        contradicting_factors.append("Moon tara bala adds friction even if events still manifest.")

    if kp_verdict in {"strong_materialization_support", "supports_materialization"}:
        support_score += 2
        event_score += 2
        support_factors.append("KP supports materialization for the requested type of event.")
    elif kp_verdict == "weak_or_indirect_kp_trigger":
        event_score -= 1
        contradicting_factors.append("KP does not strongly confirm direct materialization.")

    if av_verdict in {"supportive", "supportive_for_intent"}:
        support_score += 1
        support_factors.append("Ashtakavarga supports usability of the active field.")
    elif av_verdict == "strained_for_intent":
        friction_score += 2
        contradicting_factors.append("Ashtakavarga shows strain in the exact field you want to activate.")
    elif av_verdict == "mixed_or_workable":
        friction_score += 1
        contradicting_factors.append("Ashtakavarga looks workable but not fully effortless.")

    if av_conflicts:
        friction_score += 2
        contradicting_factors.append("Ashtakavarga shows mixed local usability despite activation.")

    if fast_band in {"high", "active"}:
        support_score += 1
        event_score += 1
        support_factors.append("Fast planets are visibly active, so the day has real movement.")
    elif fast_band == "background":
        event_score -= 1
        contradicting_factors.append("Fast planets are quiet, so concrete delivery may stay limited.")

    if len(caution_windows) > len(favorable_windows) + 1:
        friction_score += 1
        contradicting_factors.append("The intraday map has more caution windows than clean action windows.")
    elif favorable_windows:
        support_score += 1
        support_factors.append("There are usable intraday windows for action if timing is chosen well.")

    if transition_windows:
        friction_score += 1
        contradicting_factors.append("The day changes character midstream, so timing matters more than usual.")

    if event_score >= 5 and friction_score >= 4:
        day_shape = "eventful_but_frictional"
    elif event_score <= 1 and support_score >= 3:
        day_shape = "smooth_but_low_manifestation"
    elif support_score >= 6 and friction_score <= 2:
        day_shape = "supportive_and_delivering"
    elif friction_score >= 5 and support_score <= 2:
        day_shape = "challenging_and_resistant"
    else:
        day_shape = "mixed_and_manageable"

    if support_score - friction_score >= 3 and event_score >= 3:
        verdict = "favorable"
    elif friction_score - support_score >= 3 and event_score <= 2:
        verdict = "challenging"
    else:
        verdict = "mixed"

    confidence_index = support_score + event_score - friction_score
    if abs(confidence_index) >= 6:
        confidence_band = "high"
    elif abs(confidence_index) >= 3:
        confidence_band = "moderate"
    else:
        confidence_band = "guarded"

    practical_guidance = {
        "favorable": "Act in the cleaner windows and be direct, because the day can actually deliver results.",
        "mixed": "Be selective and use timing carefully; the day can work, but not every window or approach is equally supportive.",
        "challenging": "Reduce unnecessary risk, avoid forcing outcomes, and use the day for maintenance or careful positioning.",
    }[verdict]

    return {
        "method": "daily_confidence_v1",
        "verdict": verdict,
        "confidence_band": confidence_band,
        "day_shape": day_shape,
        "event_likelihood": "high" if event_score >= 5 else "moderate" if event_score >= 2 else "low",
        "micro_intent_name": daily_micro_intent.get("name"),
        "micro_intent_focus": daily_micro_intent.get("daily_focus"),
        "activated_micro_intent_houses": overlap_houses,
        "top_domains": top_domains,
        "support_score": support_score,
        "friction_score": friction_score,
        "event_score": event_score,
        "supporting_factors": support_factors[:5],
        "contradicting_factors": contradicting_factors[:5],
        "practical_guidance": practical_guidance,
        "summary": (
            f"{verdict.capitalize()} day with {confidence_band} confidence; "
            f"overall shape is {day_shape.replace('_', ' ')}."
        ),
    }
