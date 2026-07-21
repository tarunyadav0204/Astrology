from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


REMEDY_CARD_FOMO_COPY_RULES = """
When type="remedy", the UI remedy card shows ONLY these three fields — write them in the SAME language/script as the user's CURRENT QUESTION (not English unless the question is English):
- title: 4–10 word FOMO headline tied to the chart pressure just discussed (urgency + opportunity, no fear-mongering).
- reason: One short FOMO subline (why acting in this dasha/window matters; what they gain by opening remedies now).
- follow_up_questions[0]: Short button label (e.g. "Show my remedies" / "उपाय देखें") — this is the only CTA text on the card.
Do NOT use generic labels like "Practical remedy plan" or "Generate remedies". Make copy specific to this reading and question language.
""".strip()


NO_INLINE_REMEDY_PLAN_RULE = """
Do NOT write a practical remedy or wellness plan in normal chat answers (only in explicit Remedies CTA / remedy_action mode).
Forbidden outside remedy mode:
- Numbered lifestyle action lists: diet rules, exercise routines, yoga/swimming/pranayama/breathwork, dental/cardio monitoring checklists, alkaline/Pitta/Vata/Kapha prescriptions
- Mantras, gemstones, charity/seva, upayas, nakshatra remedy layers, or sections titled "Guidance and Remedies"
Allowed instead:
- Timing phases and dasha/transit windows
- Astrological vulnerability themes (which houses/body-systems are sensitized) without prescribing how to fix them
- Brief theme-level cautions tied to chart evidence

IMPORTANT — Remedies CTA is separate from the answer body:
- Still append NEXT_ACTION_META with type="remedy" when a practical remedy reading would help (health, blocks, stress, afflictions).
- The card lets the user click for remedies; do NOT put the remedy/wellness plan in the main answer text.
""".strip()


NEXT_ACTION_NONE_IN_REMEDY_MODE = """
CRITICAL - REMEDY MODE (user already tapped the Remedies CTA):
- Put all practical remedies in the answer body — this IS the remedy reading.
- Append NEXT_ACTION_META with type="none" only. NEVER type="remedy" — do not show a second remedy card.
- Do NOT add a Follow-up section, follow-up question chips, or prompts asking for more remedies.
""".strip()


_FOLLOW_UP_HTML_RE = re.compile(
    r'<div\s+class="follow-up-questions"[^>]*>.*?</div>',
    re.DOTALL | re.IGNORECASE,
)


def is_in_remedy_delivery_mode(
    *,
    remedy_followup_active: bool = False,
    answer_mode: str = "",
) -> bool:
    """
    Only an explicit Remedies CTA breadcrumb activates delivery mode.

    `answer_mode` is intentionally ignored: the router/LLM can misclassify a
    normal question as remedy_action, and treating that as proof of a CTA click
    both hides the normal remedy card and strips the wrong content.
    """
    _ = answer_mode  # retained for call-site compatibility
    return bool(remedy_followup_active)


def strip_remedy_followup_prompts_from_content(content: str) -> str:
    """Remove follow-up chips/sections the model should not emit in remedy-only answers."""
    text = str(content or "")
    text = _FOLLOW_UP_HTML_RE.sub("", text)
    text = re.sub(
        r"\n(?:#{1,3}\s*)?(?:\*\*)?Follow[- ]up(?:\s+questions)?(?:\*\*)?\s*\n[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\n-{3,}\s*\n[\s\S]*?(?:Tell me more about|Provide a detailed|Analyze my health|Detailed\s+[\w\s-]+(?:Guide|Ritual))[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\n(?:Detailed\s+[\w\s-]+(?:Guide|Ritual)|Tell me more about|Provide a detailed guide|Analyze my health)[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text.strip()


def strip_inline_remedy_sections_from_content(content: str) -> str:
    """
    Remove remedy-plan body sections from normal (non-CTA) answers.
    Remedies belong behind the Remedies card, not inline in the first reading.
    """
    text = str(content or "")
    # Cut from common remedy section headers through the rest of the answer.
    text = re.sub(
        r"(?:^|\n)(?:#{1,3}\s*)?(?:\*\*)?(?:"
        r"Guidance and Remedies|"
        r"Remedy layers|"
        r"What needs attention now|"
        r"Analysis \+ Remedies"
        r")(?:\*\*)?\s*\n[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Model sometimes dumps layers without a markdown header.
    text = re.sub(
        r"(?:^|\n)(?:\*\*)?(?:"
        r"Core planetary remedy|"
        r"Gemstone\s*/\s*ratna|"
        r"Biological\s*/\s*Vriksha|"
        r"Nakshatra remedy|"
        r"Behavioral support|"
        r"Charity\s*/\s*seva|"
        r"Mantra\s*/\s*Sound|"
        r"Special blockage layers|"
        r"Dietary\s*:"
        r")[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text.strip()


def apply_remedy_mode_delivery_guards(
    *,
    content: str,
    next_action: Optional[Dict[str, Any]] = None,
    follow_up_questions: Optional[List[Any]] = None,
    remedy_followup_active: bool = False,
    answer_mode: str = "",
) -> tuple[str, Optional[Dict[str, Any]], List[Any]]:
    if not is_in_remedy_delivery_mode(
        remedy_followup_active=remedy_followup_active,
        answer_mode=answer_mode,
    ):
        return content, next_action, list(follow_up_questions or [])
    cleaned = strip_remedy_followup_prompts_from_content(content)
    return cleaned, None, []


def apply_normal_answer_remedy_guards(
    *,
    content: str,
    next_action: Optional[Dict[str, Any]] = None,
    follow_up_questions: Optional[List[Any]] = None,
    answer_mode: str = "",
    category: str = "",
    question: str = "",
    language: str = "",
    remedy_followup_active: bool = False,
) -> tuple[str, Optional[Dict[str, Any]], List[Any]]:
    """
    For normal answers: strip leaked inline remedy plans and keep/ensure the Remedies CTA card.
    For CTA remedy delivery: strip follow-ups and clear the remedy card.
    """
    if remedy_followup_active:
        return apply_remedy_mode_delivery_guards(
            content=content,
            next_action=next_action,
            follow_up_questions=follow_up_questions,
            remedy_followup_active=True,
            answer_mode="remedy_action",
        )
    cleaned = strip_inline_remedy_sections_from_content(content)
    action = ensure_remedy_cta_next_action(
        next_action,
        answer_mode=answer_mode,
        category=category,
        question=question,
        remedy_followup_active=False,
        language=language,
    )
    return cleaned, action, list(follow_up_questions or [])


def should_offer_remedy_cta(
    *,
    answer_mode: str = "",
    category: str = "",
    question: str = "",
    remedy_followup_active: bool = False,
) -> bool:
    """Whether the UI should show the Generate remedies card after a normal answer."""
    if remedy_followup_active:
        return False
    mode = str(answer_mode or "").strip().lower()
    if mode in {
        "remedy_action",
        "conversational_ack",
        "year_clarification",
        "explanation_mechanism",
        "comparison_choice",
        "trait_nature",
        "relationship_person",
    }:
        return False
    cat = str(category or "").strip().lower()
    if cat in {"health", "disease", "stress", "mental", "anxiety"}:
        return True
    if mode == "problem_diagnosis":
        return True
    q = str(question or "").lower()
    problem_markers = (
        "problem", "issue", "anxiety", "stress", "why am i", "why do i",
        "blocked", "stuck", "struggling", "remedy", "upay", "what should i do",
        "what can i do", "how to fix",
    )
    if any(m in q for m in problem_markers):
        return True
    if mode in {"topic_reading", "timing_window", "potential_capacity"} and cat in {
        "health", "career", "job", "marriage", "love", "relationship", "wealth", "money", "finance",
    }:
        return True
    return False


def _question_script_family(question: str, language: str = "") -> str:
    lang = str(language or "").strip().lower()
    if lang in {"hindi", "hi", "hinglish", "devanagari"}:
        return "hindi"
    if re.search(r"[\u0900-\u097F]", str(question or "")):
        return "hindi"
    return "english"


def _fallback_remedy_fomo_copy(category: str, question: str, language: str = "") -> Dict[str, str]:
    """Last-resort FOMO card copy when the model omitted NEXT_ACTION_META."""
    family = _question_script_family(question, language)
    cat = str(category or "").strip().lower()
    if family == "hindi":
        by_cat = {
            "health": (
                "स्वास्थ्य दबाव अभी सक्रिय है",
                "इस दशा में चार्ट की कमज़ोरी तेज़ हो सकती है — सही समय पर उपाय से संतुलन बेहतर रहता है।",
                "मेरे उपाय देखें",
            ),
            "career": (
                "करियर का यह मोड़ अभी खुला है",
                "सक्रिय दशा में सही उपाय रास्ता साफ़ कर सकते हैं — देरी से असर कम होता है।",
                "करियर उपाय देखें",
            ),
            "marriage": (
                "रिश्तों का दबाव अभी चरम पर है",
                "इस चक्र में उपाय से रुकावटें हल्की हो सकती हैं — अभी देखना फायदेमंद है।",
                "रिश्ता उपाय देखें",
            ),
        }
        title, reason, button = by_cat.get(
            cat,
            (
                "यह दबाव अभी सक्रिय है",
                "चार्ट में दिखी कमज़ोरी इस दशा में बढ़ सकती है — समय पर उपाय ज़्यादा असरदार रहते हैं।",
                "उपाय देखें",
            ),
        )
        return {"title": title, "reason": reason, "follow_up": button}
    by_cat_en = {
        "health": (
            "Your health pressure is peaking now",
            "This dasha window can intensify the chart stress you just saw — timely remedies land better.",
            "Show my health remedies",
        ),
        "career": (
            "Your career window is open now",
            "Aligned remedies in this active period can clear blocks faster — worth opening before it passes.",
            "Show my career remedies",
        ),
        "marriage": (
            "Relationship pressure is active now",
            "This cycle responds well to targeted remedies — see what fits before the phase shifts.",
            "Show relationship remedies",
        ),
    }
    title, reason, button = by_cat_en.get(
        cat,
        (
            "This chart pressure is active now",
            "The vulnerability in your reading is strongest in the current dasha — remedies work best when matched to this phase.",
            "Show my remedies",
        ),
    )
    return {"title": title, "reason": reason, "follow_up": button}


def _complete_remedy_fomo_copy(
    next_action: Dict[str, Any],
    *,
    category: str,
    question: str,
    language: str = "",
) -> Dict[str, Any]:
    """Fill missing remedy-card fields; keep any LLM-provided FOMO copy."""
    fb = _fallback_remedy_fomo_copy(category, question, language)
    follow = [
        str(q).strip()
        for q in (next_action.get("follow_up_questions") or [])
        if str(q).strip()
    ]
    if not follow:
        follow = [fb["follow_up"]]
    return {
        **next_action,
        "type": "remedy",
        "title": str(next_action.get("title") or "").strip() or fb["title"],
        "reason": str(next_action.get("reason") or "").strip() or fb["reason"],
        "confidence": str(next_action.get("confidence") or "medium").strip().lower() or "medium",
        "follow_up_questions": follow[:3],
        "source": str(next_action.get("source") or "merge").strip() or "merge",
    }


def ensure_remedy_cta_next_action(
    next_action: Optional[Dict[str, Any]],
    *,
    answer_mode: str = "",
    category: str = "",
    question: str = "",
    remedy_followup_active: bool = False,
    language: str = "",
) -> Optional[Dict[str, Any]]:
    """
    If the model omitted NEXT_ACTION_META or set type=none, still show the Remedies card
    when this turn is eligible (normal reading, not already remedy mode).
    In remedy mode, never surface another remedy CTA card.
    """
    action_type = str((next_action or {}).get("type") or "").strip().lower()
    mode = str(answer_mode or "").strip().lower()
    if remedy_followup_active:
        if action_type in {"", "none", "remedy"}:
            return None
        return next_action
    # Defensive recovery: a normal turn misclassified as remedy_action is not
    # remedy delivery. Treat it as a problem reading for CTA eligibility.
    if mode == "remedy_action":
        mode = "problem_diagnosis"
    if action_type == "remedy":
        return _complete_remedy_fomo_copy(next_action or {}, category=category, question=question, language=language)
    if action_type and action_type != "none":
        return next_action
    if not should_offer_remedy_cta(
        answer_mode=mode,
        category=category,
        question=question,
        remedy_followup_active=remedy_followup_active,
    ):
        return next_action if action_type else None
    fb = _fallback_remedy_fomo_copy(category, question, language)
    return {
        "type": "remedy",
        "title": fb["title"],
        "reason": fb["reason"],
        "confidence": "medium",
        "follow_up_questions": [fb["follow_up"]],
        "source": "fallback",
    }


def is_remedy_followup_request(intent_or_context: Optional[Dict[str, Any]]) -> bool:
    """
    True only when the client explicitly marked a Remedies CTA / remedy follow-up.
    Do not infer from question wording alone.
    """
    if not isinstance(intent_or_context, dict):
        return False

    query_context = intent_or_context.get("query_context")
    if not isinstance(query_context, dict):
        # Bare query_context dict (no nested query_context key).
        query_context = intent_or_context if any(
            key in intent_or_context
            for key in (
                "follow_up_type",
                "followUpType",
                "chat_action",
                "chatAction",
                "remedy_followup",
                "remedy_action",
                "open_remedy",
                "openRemedy",
            )
        ) else {}

    candidate_values = [
        intent_or_context.get("follow_up_type"),
        query_context.get("follow_up_type"),
        query_context.get("followUpType"),
        query_context.get("chat_action"),
        query_context.get("chatAction"),
        query_context.get("mode"),
        query_context.get("answer_mode"),
    ]
    normalized = {
        str(value or "").strip().lower()
        for value in candidate_values
        if str(value or "").strip()
    }
    if normalized & {"remedy", "remedy_followup", "remedy_action"}:
        return True
    if bool(query_context.get("remedy_followup")) or bool(query_context.get("remedy_action")):
        return True
    if bool(query_context.get("open_remedy")) or bool(query_context.get("openRemedy")):
        return True
    return False


_REMEDY_CHAIN_MARKERS = (
    "remedy-only",
    "generate a remedy-only",
    "give practical remedies only",
    "do not give a general chart reading",
)


def is_remedy_chain_question(text: Optional[str]) -> bool:
    """Detect remedy CTA follow-up text merged into a clarification chain."""
    lowered = str(text or "").strip().lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in _REMEDY_CHAIN_MARKERS)


def resolve_remedy_followup_active(
    intent_or_context: Optional[Dict[str, Any]],
    *,
    combined_question: str = "",
) -> bool:
    """True only for explicit Remedies CTA / chain text — never from answer_mode alone."""
    if is_remedy_followup_request(intent_or_context):
        return True
    return is_remedy_chain_question(combined_question)


def clamp_remedy_modes_on_intent(result: Optional[Dict[str, Any]], question: str = "") -> None:
    """
    Mutate an intent-router result so remedy modes only survive with CTA flags.
    With CTA: force remedy_action. Without: demote remedy_action / RECOMMEND_REMEDY.
    """
    if not isinstance(result, dict):
        return
    if is_remedy_followup_request(result):
        result["answer_mode"] = "remedy_action"
        mode = str(result.get("mode") or "").strip().upper()
        if mode in {"", "ANALYZE_PERSONALITY", "ANALYZE_TOPIC_POTENTIAL", "DEFAULT"}:
            result["mode"] = "RECOMMEND_REMEDY_FOR_PROBLEM"
        return

    if str(result.get("answer_mode") or "").strip() == "remedy_action":
        q = str(question or "").lower()
        problem_markers = (
            "why", "problem", "issue", "stuck", "delay", "blocked", "struggle",
            "anxiety", "stress", "difficult", "trouble", "leak", "loss",
        )
        result["answer_mode"] = (
            "problem_diagnosis" if any(m in q for m in problem_markers) else "topic_reading"
        )

    if str(result.get("mode") or "").strip().upper() == "RECOMMEND_REMEDY_FOR_PROBLEM":
        result["mode"] = "ANALYZE_ROOT_CAUSE"


def normalize_query_context(query_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(query_context, dict):
        return {}
    out: Dict[str, Any] = {}

    timezone_name = (
        query_context.get("timezone_name")
        or query_context.get("query_timezone_name")
        or query_context.get("timeZone")
    )
    if timezone_name:
        out["timezone_name"] = str(timezone_name).strip()

    client_now_iso = (
        query_context.get("client_now_iso")
        or query_context.get("clientNowIso")
        or query_context.get("now_iso")
    )
    if client_now_iso:
        out["client_now_iso"] = str(client_now_iso).strip()

    utc_offset_minutes = (
        query_context.get("utc_offset_minutes")
        if query_context.get("utc_offset_minutes") is not None
        else query_context.get("utcOffsetMinutes")
    )
    if utc_offset_minutes is not None:
        try:
            out["utc_offset_minutes"] = int(float(utc_offset_minutes))
        except (TypeError, ValueError):
            pass

    for src_key, dst_key in (
        ("latitude", "latitude"),
        ("longitude", "longitude"),
        ("query_latitude", "latitude"),
        ("query_longitude", "longitude"),
    ):
        value = query_context.get(src_key)
        if value is None or dst_key in out:
            continue
        try:
            out[dst_key] = float(value)
        except (TypeError, ValueError):
            continue

    # Preserve follow-up / action flags so downstream chat mode routing can
    # distinguish remedy clicks, native gates, and other explicit follow-ups.
    # These values are intentionally copied through without transformation.
    for key in (
        "follow_up_type",
        "followUpType",
        "chat_action",
        "chatAction",
        "mode",
        "answer_mode",
        "remedy_followup",
        "remedy_action",
        "open_remedy",
        "openRemedy",
        "remedy_card_source",
        "remedy_next_action_title",
        "source_message_id",
        "sourceMessageId",
    ):
        if key in query_context and key not in out and query_context.get(key) is not None:
            out[key] = query_context.get(key)

    return out


def _parse_client_now(value: str) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def resolve_query_now(query_context: Optional[Dict[str, Any]]) -> datetime:
    normalized = normalize_query_context(query_context)
    tz_name = normalized.get("timezone_name")
    tz_obj = None
    if tz_name and ZoneInfo is not None:
        try:
            tz_obj = ZoneInfo(str(tz_name))
        except Exception:
            tz_obj = None

    offset_minutes = normalized.get("utc_offset_minutes")
    offset_tz = None
    if offset_minutes is not None:
        try:
            offset_tz = timezone(timedelta(minutes=int(offset_minutes)))
        except Exception:
            offset_tz = None

    parsed = _parse_client_now(str(normalized.get("client_now_iso") or ""))
    if parsed is not None:
        if parsed.tzinfo is None:
            if tz_obj is not None:
                return parsed.replace(tzinfo=tz_obj)
            if offset_tz is not None:
                return parsed.replace(tzinfo=offset_tz)
            return parsed
        if tz_obj is not None:
            return parsed.astimezone(tz_obj)
        if offset_tz is not None:
            return parsed.astimezone(offset_tz)
        return parsed

    if tz_obj is not None:
        return datetime.now(tz_obj)
    if offset_tz is not None:
        return datetime.now(offset_tz)
    return datetime.now()
