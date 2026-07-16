"""Timing-contract anchors for lifespan / career event predictions.

Locks Window-1 ranking across follow-ups unless deterministic scores change,
and splits career into Activation / Offer / Joining. Phrasing rules live in
prompts only (no English post-rewrite — answers are multi-language).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

ANCHORS_KEY = "prediction_anchors"

TOPIC_FAMILIES = frozenset(
    {
        "career",
        "marriage",
        "children",
        "property",
        "education",
        "health",
        "wealth",
        "general",
    }
)

CAREER_LAYER_KEYS = ("activation", "offer", "joining")

WINDOW1_PATTERNS = (
    re.compile(
        r"\*\*Window\s*1\*\*\s*[:\-–]?\s*([^\n*]{3,80})",
        re.I,
    ),
    re.compile(
        r"Window\s*1\s*[:\-–]\s*([^\n*]{3,80})",
        re.I,
    ),
)

PREDICTION_ANCHOR_META_INSTRUCTION = """
CRITICAL - PREDICTION ANCHOR METADATA (do not include this line in the main answer the user sees):
When this turn sets or updates a lifespan/event timing forecast (especially career/job/marriage/children/property), after NEXT_ACTION_META and before FAQ_META, output exactly one line:
PREDICTION_ANCHOR_META: {"topic_key":"<career|marriage|children|property|education|health|wealth|general>","confidence":"<high|medium|low>","window_1_label":"<ranked #1 window dates>","window_1_start":"<YYYY-MM-DD or empty>","window_1_end":"<YYYY-MM-DD or empty>","window_1_layer":"<activation|offer|joining|promise|execution>","window_1_dasha":"<MD-AD-PD if known>","window_1_strength":"<high|medium|low>","activation_window":"<career: more calls/effort band or empty>","offer_window":"<career: offer-likely band or empty>","joining_window":"<career: joining/settle band or empty>","score_fingerprint":"<short hash of ranking reason or empty>"}
- topic_key must be lowercase from the list above.
- For career/job answers, window_1_layer and the three career layer fields are mandatory. Never use one PD start date for all three layers.
- If this is a follow-up and TIMING_CONTRACT_LOCK is present, keep window_1_* identical unless the lock explicitly allows a re-rank.
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def infer_topic_family(
    question: str = "",
    category: Optional[str] = None,
    faq_category: Optional[str] = None,
) -> str:
    cat = str(faq_category or category or "").strip().lower()
    if cat in {"job", "promotion", "business"}:
        cat = "career"
    if cat in {"relationship", "spouse"}:
        cat = "marriage"
    if cat in {"child", "childbirth", "progeny"}:
        cat = "children"
    if cat in TOPIC_FAMILIES:
        return cat

    q = str(question or "").lower()
    career_cues = (
        "job",
        "career",
        "promotion",
        "interview",
        "offer",
        "joining",
        "employment",
        "unemploy",
        "salary",
        "work",
        "profession",
    )
    marriage_cues = ("marriage", "wedding", "spouse", "husband", "wife", "engage")
    children_cues = ("child", "pregnancy", "conceive", "baby", "progeny")
    property_cues = ("house", "property", "flat", "home purchase", "relocation")
    education_cues = ("exam", "admission", "education", "degree", "college")
    health_cues = ("health", "surgery", "illness", "disease")
    wealth_cues = ("wealth", "money", "income", "finance", "profit")

    if any(c in q for c in career_cues):
        return "career"
    if any(c in q for c in marriage_cues):
        return "marriage"
    if any(c in q for c in children_cues):
        return "children"
    if any(c in q for c in property_cues):
        return "property"
    if any(c in q for c in education_cues):
        return "education"
    if any(c in q for c in health_cues):
        return "health"
    if any(c in q for c in wealth_cues):
        return "wealth"
    return "general"


def infer_topic_key(
    question: str = "",
    category: Optional[str] = None,
    faq_category: Optional[str] = None,
) -> str:
    family = infer_topic_family(question, category=category, faq_category=faq_category)
    q = str(question or "").lower()
    if family == "career":
        if any(c in q for c in ("first job", "first employment", "get a job", "unemploy")):
            return "career_first_job"
        if "promotion" in q or "raise" in q:
            return "career_promotion"
        if "business" in q or "startup" in q:
            return "career_business"
        return "career"
    if family == "marriage":
        return "marriage"
    if family == "children":
        return "children"
    return family


def is_timing_followup_question(question: str) -> bool:
    q = str(question or "").lower().strip()
    cues = (
        "still true",
        "still hold",
        "you said",
        "you mentioned",
        "earlier you",
        "previous answer",
        "same window",
        "confirm",
        "update on",
        "has it changed",
        "changed now",
        "july",
        "august",
        "window 1",
        "is this accurate",
        "recheck",
        "revise",
    )
    return any(c in q for c in cues)


def should_apply_timing_contract(
    *,
    mode: Optional[str] = None,
    category: Optional[str] = None,
    question: str = "",
    faq_category: Optional[str] = None,
) -> bool:
    mode_u = str(mode or "").upper()
    if mode_u in {"LIFESPAN_EVENT_TIMING", "PREDICT_EVENT_TIMING"}:
        return True
    family = infer_topic_family(question, category=category, faq_category=faq_category)
    if family in {"career", "marriage", "children", "property"} and (
        is_timing_followup_question(question)
        or any(
            token in str(question or "").lower()
            for token in ("when", "which year", "which month", "timing", "window", "dasha")
        )
    ):
        return True
    return False


def _extract_balanced_json_object(text: str, start_idx: int) -> Optional[Tuple[str, int]]:
    """Return (json_str, end_index_exclusive) for a `{...}` object starting at start_idx."""
    if start_idx < 0 or start_idx >= len(text) or text[start_idx] != "{":
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start_idx, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start_idx : i + 1], i + 1
    return None


def parse_prediction_anchor_meta(text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Find PREDICTION_ANCHOR_META: {...} anywhere; strip it. Tolerates FAQ/NEXT_ACTION neighbors."""
    src = text or ""
    marker = re.search(r"\n?\s*PREDICTION_ANCHOR_META:\s*", src, re.IGNORECASE)
    if not marker:
        return text, None
    brace_at = src.find("{", marker.end())
    if brace_at < 0:
        return text, None
    extracted = _extract_balanced_json_object(src, brace_at)
    if not extracted:
        return text, None
    json_str, json_end = extracted
    try:
        meta = json.loads(json_str)
        if not isinstance(meta, dict):
            return text, None
        # Drop optional trailing whitespace after the JSON object on the same meta block.
        end = json_end
        while end < len(src) and src[end] in " \t\r":
            end += 1
        if end < len(src) and src[end] == "\n":
            end += 1
        stripped = (src[: marker.start()] + src[end:]).rstrip()
        return stripped, meta
    except (json.JSONDecodeError, TypeError, ValueError):
        return text, None


def extract_window1_label_from_answer(answer: str) -> str:
    for pat in WINDOW1_PATTERNS:
        m = pat.search(answer or "")
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip(" .-–")[:120]
    return ""


def _window_from_verdict_side(side: Dict[str, Any], *, rank: int, layer: str) -> Dict[str, Any]:
    if not isinstance(side, dict) or not side:
        return {}
    start = side.get("start")
    if not start:
        segments = side.get("segments") if isinstance(side.get("segments"), list) else []
        if segments and isinstance(segments[0], dict):
            start = segments[0].get("start")
    end = side.get("end")
    if not end:
        segments = side.get("segments") if isinstance(side.get("segments"), list) else []
        if segments and isinstance(segments[-1], dict):
            end = segments[-1].get("end")
    chain = side.get("chain") or side.get("dasha_chain") or ""
    score = side.get("score")
    label_parts = [str(p) for p in (start, end) if p]
    label = " – ".join(label_parts) if label_parts else str(chain or "").strip()
    return {
        "rank": rank,
        "label": label,
        "start": start,
        "end": end,
        "strength": "high" if isinstance(score, (int, float)) and score >= 70 else "medium",
        "layer": layer,
        "dasha_chain": chain,
        "score": score,
        "significations": list(side.get("why") or [])[:6]
        if isinstance(side.get("why"), list)
        else [],
    }


def build_anchor_from_event_timing_verdict(
    verdict: Dict[str, Any],
    *,
    topic_key: str,
    question: str = "",
    message_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    if not isinstance(verdict, dict) or not verdict:
        return None
    future = verdict.get("best_future_cluster") or verdict.get("best_future_window") or {}
    current = verdict.get("current_window") or {}
    windows: List[Dict[str, Any]] = []
    primary = future if future else current
    w1 = _window_from_verdict_side(primary, rank=1, layer="activation")
    if w1 and w1.get("label"):
        windows.append(w1)
    if future and current:
        w2 = _window_from_verdict_side(current, rank=2, layer="activation")
        if w2 and w2.get("label"):
            windows.append(w2)
    if not windows:
        return None

    family = infer_topic_family(question, category=topic_key.split("_")[0])
    layers = {}
    if family == "career":
        layers = {
            "activation": windows[0].get("label") or "",
            "offer": "",
            "joining": "",
        }

    return {
        "topic_key": topic_key,
        "topic_family": family,
        "question_preview": str(question or "")[:240],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "message_id": message_id,
        "confidence": str(verdict.get("confidence") or "medium"),
        "window_1": windows[0],
        "windows": windows[:5],
        "layers": layers,
        "verdict_fingerprint": {
            "comparison": verdict.get("comparison"),
            "score_delta": verdict.get("score_delta"),
            "best_future_start": (future or {}).get("start"),
            "best_future_end": (future or {}).get("end"),
            "best_future_chain": (future or {}).get("chain"),
            "current_start": (current or {}).get("start"),
            "current_chain": (current or {}).get("chain") or (current or {}).get("dasha_chain"),
        },
        "source": "event_timing_verdict",
    }


def build_anchor_from_meta(
    meta: Dict[str, Any],
    *,
    question: str = "",
    message_id: Optional[int] = None,
    fallback_answer: str = "",
) -> Optional[Dict[str, Any]]:
    if not isinstance(meta, dict):
        return None
    topic_key = str(meta.get("topic_key") or infer_topic_key(question)).strip().lower()
    if topic_key not in TOPIC_FAMILIES and not topic_key.startswith("career"):
        topic_key = infer_topic_key(question, category=topic_key)
    family = infer_topic_family(question, category=topic_key.split("_")[0])
    label = str(meta.get("window_1_label") or "").strip() or extract_window1_label_from_answer(fallback_answer)
    if not label and not meta.get("activation_window"):
        return None
    window_1 = {
        "rank": 1,
        "label": label or str(meta.get("activation_window") or "").strip(),
        "start": meta.get("window_1_start") or None,
        "end": meta.get("window_1_end") or None,
        "strength": str(meta.get("window_1_strength") or "medium").lower(),
        "layer": str(meta.get("window_1_layer") or ("activation" if family == "career" else "execution")).lower(),
        "dasha_chain": str(meta.get("window_1_dasha") or "").strip(),
        "score": None,
        "significations": [],
    }
    layers = {}
    if family == "career":
        layers = {
            "activation": str(meta.get("activation_window") or window_1["label"] or "").strip(),
            "offer": str(meta.get("offer_window") or "").strip(),
            "joining": str(meta.get("joining_window") or "").strip(),
        }
    return {
        "topic_key": topic_key if topic_key.startswith("career") else family,
        "topic_family": family,
        "question_preview": str(question or "")[:240],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "message_id": message_id,
        "confidence": str(meta.get("confidence") or "medium").lower(),
        "window_1": window_1,
        "windows": [window_1],
        "layers": layers,
        "verdict_fingerprint": {
            "score_fingerprint": str(meta.get("score_fingerprint") or "").strip(),
        },
        "source": "llm_meta",
    }


def build_anchor_from_answer_heuristic(
    answer: str,
    *,
    question: str = "",
    category: Optional[str] = None,
    faq_category: Optional[str] = None,
    message_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    label = extract_window1_label_from_answer(answer)
    if not label:
        return None
    topic_key = infer_topic_key(question, category=category, faq_category=faq_category)
    family = infer_topic_family(question, category=category, faq_category=faq_category)
    window_1 = {
        "rank": 1,
        "label": label,
        "start": None,
        "end": None,
        "strength": "medium",
        "layer": "activation" if family == "career" else "execution",
        "dasha_chain": "",
        "score": None,
        "significations": [],
    }
    layers = {}
    if family == "career":
        layers = {"activation": label, "offer": "", "joining": ""}
    return {
        "topic_key": topic_key,
        "topic_family": family,
        "question_preview": str(question or "")[:240],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "message_id": message_id,
        "confidence": "medium",
        "window_1": window_1,
        "windows": [window_1],
        "layers": layers,
        "verdict_fingerprint": {},
        "source": "answer_heuristic",
    }


def get_anchors_map(extracted_context: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(extracted_context, dict):
        return {}
    raw = extracted_context.get(ANCHORS_KEY)
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for key, val in raw.items():
        if isinstance(val, dict) and val.get("window_1"):
            out[str(key)] = val
    return out


def get_locked_anchor(
    extracted_context: Optional[Dict[str, Any]],
    topic_key: str,
) -> Optional[Dict[str, Any]]:
    anchors = get_anchors_map(extracted_context)
    if not anchors:
        return None
    if topic_key in anchors:
        return anchors[topic_key]
    # Fall back to family-level key (career_first_job -> career)
    family = topic_key.split("_")[0]
    if family in anchors:
        return anchors[family]
    for key, anchor in anchors.items():
        if str(key).startswith(family) or str(anchor.get("topic_family") or "") == family:
            return anchor
    return None


def upsert_anchor_into_extracted_context(
    extracted_context: Optional[Dict[str, Any]],
    anchor: Dict[str, Any],
    *,
    replace_window1: bool = False,
) -> Dict[str, Any]:
    ctx = dict(extracted_context or {})
    anchors = get_anchors_map(ctx)
    key = str(anchor.get("topic_key") or "general")
    existing = anchors.get(key)
    if existing and not replace_window1:
        # Preserve original Window 1; refresh metadata / layers if empty.
        merged = dict(existing)
        merged["updated_at"] = _now_iso()
        if anchor.get("message_id"):
            merged["last_message_id"] = anchor.get("message_id")
        if not merged.get("layers") and anchor.get("layers"):
            merged["layers"] = anchor.get("layers")
        elif isinstance(merged.get("layers"), dict) and isinstance(anchor.get("layers"), dict):
            layers = dict(merged["layers"])
            for lk, lv in anchor["layers"].items():
                if lv and not layers.get(lk):
                    layers[lk] = lv
            merged["layers"] = layers
        if anchor.get("verdict_fingerprint"):
            merged["verdict_fingerprint"] = {
                **(merged.get("verdict_fingerprint") or {}),
                **(anchor.get("verdict_fingerprint") or {}),
            }
        anchors[key] = merged
    else:
        anchors[key] = dict(anchor)
        # Also store under family for coarse follow-up matching
        family = str(anchor.get("topic_family") or key.split("_")[0])
        if family and family != key and family not in anchors:
            anchors[family] = dict(anchor)
            anchors[family]["topic_key"] = family
    ctx[ANCHORS_KEY] = anchors
    return ctx


def compare_verdict_to_anchor(
    anchor: Optional[Dict[str, Any]],
    verdict: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Decide whether Window-1 re-rank is allowed from deterministic score change."""
    if not isinstance(anchor, dict) or not isinstance(verdict, dict):
        return {
            "allows_rerank": False,
            "reason": "missing_anchor_or_verdict",
            "score_delta_change": None,
        }
    prior_fp = anchor.get("verdict_fingerprint") or {}
    prior_delta = prior_fp.get("score_delta")
    new_delta = verdict.get("score_delta")
    prior_comp = str(prior_fp.get("comparison") or "")
    new_comp = str(verdict.get("comparison") or "")
    prior_chain = str(prior_fp.get("best_future_chain") or "")
    new_cluster = verdict.get("best_future_cluster") or verdict.get("best_future_window") or {}
    new_chain = str((new_cluster or {}).get("chain") or "")
    prior_start = str(prior_fp.get("best_future_start") or "")
    new_start = str((new_cluster or {}).get("start") or "")

    delta_change = None
    if isinstance(prior_delta, (int, float)) and isinstance(new_delta, (int, float)):
        delta_change = abs(float(new_delta) - float(prior_delta))

    material_score_flip = delta_change is not None and delta_change >= 8
    comparison_flip = bool(prior_comp and new_comp and prior_comp != new_comp and material_score_flip)
    chain_flip = bool(prior_chain and new_chain and prior_chain != new_chain and material_score_flip)
    start_flip = bool(prior_start and new_start and prior_start != new_start and material_score_flip)

    allows = bool(material_score_flip and (comparison_flip or chain_flip or start_flip))
    reason = "scores_materially_changed" if allows else "scores_stable_lock_window1"
    return {
        "allows_rerank": allows,
        "reason": reason,
        "score_delta_change": delta_change,
        "prior_comparison": prior_comp,
        "new_comparison": new_comp,
        "prior_chain": prior_chain,
        "new_chain": new_chain,
    }


def format_timing_contract_lock_block(
    anchor: Dict[str, Any],
    *,
    rerank: Optional[Dict[str, Any]] = None,
) -> str:
    w1 = anchor.get("window_1") or {}
    layers = anchor.get("layers") or {}
    family = str(anchor.get("topic_family") or "")
    lines = [
        "TIMING_CONTRACT_LOCK (MANDATORY — highest authority for this follow-up):",
        f"- Locked topic: {anchor.get('topic_key')}",
        f"- Locked Window 1: {w1.get('label') or 'unknown'}"
        + (f" ({w1.get('start')} → {w1.get('end')})" if w1.get("start") or w1.get("end") else ""),
        f"- Locked strength/confidence: {w1.get('strength') or anchor.get('confidence') or 'medium'}",
    ]
    if w1.get("dasha_chain"):
        lines.append(f"- Locked dasha chain for Window 1: {w1.get('dasha_chain')}")
    if w1.get("layer"):
        lines.append(f"- Locked Window 1 claim layer: {w1.get('layer')} (do not promote it to a different outcome layer)")
    if family == "career":
        lines.append(
            "- Career layers (keep separate): "
            f"Activation={layers.get('activation') or w1.get('label') or 'n/a'}; "
            f"Offer={layers.get('offer') or 'not yet specified'}; "
            f"Joining={layers.get('joining') or 'not yet specified'}."
        )
        lines.append(
            "- PD / micro-dasha start dates are environment shifts (activation), not offer/joining SLAs "
            "unless ranked execution evidence supports that layer."
        )
    if rerank and rerank.get("allows_rerank"):
        lines.append(
            f"- RE-RANK ALLOWED: deterministic scores changed ({rerank.get('reason')}; "
            f"score_delta_change={rerank.get('score_delta_change')}). "
            "You may update Window 1, but you MUST explicitly state what changed and why."
        )
    else:
        lines.append(
            "- RE-RANK FORBIDDEN: keep the same Window 1 dates/rank. "
            "Do not silently demote it to a near-miss or promote a secondary window to #1. "
            "If nuance is needed, refine Activation vs Offer vs Joining language without changing Window 1 rank."
        )
        lines.append(
            "- Ban flipping the same period's house signification (e.g. 7th/contracts → 8th/rejection) "
            "without a new deterministic evidence flag."
        )
    lines.append(
        "- Overclaim ban: do not use guarantee / copper-bottomed / mathematical conclusion / "
        "perfectly accurate / absolute truth / non-negotiable / will get. "
        "Prefer stronger window / likely band / confidence High|Medium|Low."
    )
    return "\n".join(lines)


def career_layer_prompt_rules() -> str:
    return (
        "CAREER TIMING LAYERS (MANDATORY for job/career event timing):\n"
        "1) Activation = more calls, effort, interviews, visibility (environment shift).\n"
        "2) Conversion / Offer = offer letter becomes likely.\n"
        "3) Joining / Stability = start date / settle-in.\n"
        "Never let one dasha/PD start date mean all three. "
        "A PD change is an environment shift; call it offer/joining only if the ranked execution window "
        "and score support that layer. Executive summary must name Activation vs Offer vs Joining separately."
    )


def merge_anchor_candidates(
    *,
    question: str,
    mode: Optional[str],
    category: Optional[str],
    faq_category: Optional[str],
    answer_text: str,
    prediction_anchor_meta: Optional[Dict[str, Any]],
    event_timing_verdict: Optional[Dict[str, Any]],
    message_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    if not should_apply_timing_contract(
        mode=mode, category=category, question=question, faq_category=faq_category
    ):
        # Still allow meta-driven career timing anchors even if mode drifted.
        if not prediction_anchor_meta and not event_timing_verdict:
            return None
    topic_key = infer_topic_key(question, category=category, faq_category=faq_category)
    if prediction_anchor_meta:
        from_meta = build_anchor_from_meta(
            prediction_anchor_meta,
            question=question,
            message_id=message_id,
            fallback_answer=answer_text,
        )
        if from_meta:
            return from_meta
    if isinstance(event_timing_verdict, dict) and event_timing_verdict:
        from_verdict = build_anchor_from_event_timing_verdict(
            event_timing_verdict,
            topic_key=topic_key,
            question=question,
            message_id=message_id,
        )
        if from_verdict:
            return from_verdict
    return build_anchor_from_answer_heuristic(
        answer_text,
        question=question,
        category=category,
        faq_category=faq_category,
        message_id=message_id,
    )
