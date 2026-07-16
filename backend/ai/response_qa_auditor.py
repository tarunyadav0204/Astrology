"""
Admin Astrology Response QA auditor.

Senior-jyotishi style exam of a delivered chat answer against branch evidence
and prior turns — finds technique errors, overclaims, timing drift, and
activation-vs-result conflation; proposes classical + product corrections.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from html import unescape
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

OVERCLAIM_PATTERNS: Tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\bguaranteed?\b",
        r"\bcopper[- ]bottomed\b",
        r"\bmathematical (?:conclusion|certainty|truth|guarantee)\b",
        r"\bperfectly accurate\b",
        r"\babsolute (?:truth|astrological truth|breakthrough)\b",
        r"\bnon[- ]negotiable\b",
        r"\bwithout (?:any )?doubt\b",
        r"\bdefinitely (?:will|get|happen)\b",
        r"\bcertain(?:ly)? (?:will|get|happen)\b",
        r"\bwill (?:definitely|certainly|surely) (?:get|receive|join)\b",
        r"\bunemployment wall dissolves\b",
        r"\bexact (?:astrological )?turning point\b",
    )
)

DATE_RANGE_RE = re.compile(
    r"(?P<a>"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?"
    r"|\d{1,2}(?:st|nd|rd|th)?\s+"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"(?:,?\s*\d{4})?"
    r"|\d{4}-\d{2}-\d{2}"
    r")"
    r"\s*(?:–|-|to|through|until|till|and|–)\s*"
    r"(?P<b>"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"(?:\s+\d{1,2}(?:st|nd|rd|th)?)?(?:,?\s*\d{4})?"
    r"|\d{1,2}(?:st|nd|rd|th)?\s+"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"(?:,?\s*\d{4})?"
    r"|\d{4}-\d{2}-\d{2}"
    r")",
    re.I,
)

SINGLE_DATE_RE = re.compile(
    r"\b(?:"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}"
    r"|\d{1,2}(?:st|nd|rd|th)?\s+"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r",?\s*\d{4}"
    r"|\d{4}-\d{2}-\d{2}"
    r")\b",
    re.I,
)

ACTIVATION_CUES = (
    "visible difference",
    "interview call",
    "more calls",
    "activity",
    "visibility",
    "ignition",
    "turning point",
    "blockage dissolves",
    "energy shift",
)
RESULT_CUES = (
    "offer letter",
    "joining",
    "first job",
    "job confirmation",
    "appointment letter",
    "career entry",
    "breakthrough window",
    "get the job",
    "will get",
)

HOUSE_FLIP_PATTERNS: Tuple[Tuple[str, re.Pattern[str], re.Pattern[str]], ...] = (
    (
        "mars_pd_7th_vs_8th",
        re.compile(r"mars.{0,80}(?:7th|seventh).{0,40}(?:contract|agreement|appointment)", re.I | re.S),
        re.compile(r"mars.{0,80}(?:8th|eighth).{0,40}(?:reject|obstacle|obstruction)", re.I | re.S),
    ),
)

AUDITOR_SYSTEM = """You are a SENIOR VEDIC JYOTISHI and ASTROLOGY EXAM EXAMINER auditing AstroRoshni product answers.

You are NOT a polite product reviewer. You grade like a hard classical teacher (Parashari + KP + Jaimini + Nadi + Ashtakavarga + dasha timing).

MISSION
1. Decide whether the FINAL ANSWER is astrologically sound, internally consistent, and honest with the user.
2. Separate TECHNIQUE errors from NARRATION/PRODUCT errors.
3. Propose concrete CORRECTIONS a production astrology system should make (prompt rules, timing contracts, wording).

HARD RULES
- Prefer evidence in GENERATION CONTEXT (rebuilt chart/dasha/divisional spine), BRANCH OUTPUTS, and DETERMINISTIC PRECHECK over speculation.
- When GENERATION CONTEXT is present, technical claims in the answer (dasha lords, SAV/BAV, house lords, AmK, CSL, windows) MUST be checked against that context. Mark unsupported claims as technique_error.
- If branch evidence or generation context is missing, say so; still audit narrative consistency with PRIOR TURNS.
- Never invent birth data, SAV/BAV numbers, or dasha dates not present in the packet.
- A Pratyantardasha / Antardasha START DATE is an ENVIRONMENT SHIFT, not an automatic event delivery date.
- For career/job questions you MUST grade whether the answer conflated:
  (A) Activation / effort / interviews
  (B) Offer / conversion
  (C) Joining / stability
- Absolute language ("guarantee", "mathematical conclusion", "perfectly accurate", "copper-bottomed") is a failure unless the packet literally supports certainty — which it almost never does.
- If PRIOR TURNS promised Window X as primary result and THIS answer quietly demotes X and promotes Y without explaining a score/evidence change, mark CRITICAL timing_drift.
- If the same period is used both as supportive (e.g. 7th/contracts) and obstructive (e.g. 8th/rejection) across turns without reconciliation, mark CRITICAL contradiction.
- Classical corrections must name the rule: e.g. "PD change ≠ fructification; require MD/AD + transit + divisional confluence for offer claims."
- Product fixes must be actionable for engineers/prompt writers.

OUTPUT
Return ONLY valid JSON matching the schema in the user message. No markdown fences. No prose outside JSON.
"""


def strip_html(text: str) -> str:
    if not text:
        return ""
    t = unescape(str(text))
    t = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", t)
    t = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", t)
    t = re.sub(r"(?is)<br\s*/?>", "\n", t)
    t = re.sub(r"(?is)</p>", "\n", t)
    t = re.sub(r"(?is)</div>", "\n", t)
    t = re.sub(r"(?is)<[^>]+>", " ", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def _truncate(text: str, limit: int) -> str:
    s = str(text or "")
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 20)] + "\n…[truncated]…"


def compact_branch_outputs(branches: Optional[Dict[str, Any]], *, per_branch_chars: int = 4500) -> Dict[str, Any]:
    if not isinstance(branches, dict):
        return {}
    out: Dict[str, Any] = {}
    for key in ("parashari", "jaimini", "nadi", "nakshatra", "kp", "ashtakavarga", "sudarshan", "sudarshana"):
        node = branches.get(key)
        if not isinstance(node, dict):
            continue
        bullets = [strip_html(b) for b in (node.get("bullets") or []) if b][:12]
        analysis = strip_html(node.get("analysis") or "")
        compact = {
            "bullets": bullets,
            "analysis": _truncate(analysis, per_branch_chars),
        }
        if any(compact["bullets"]) or compact["analysis"]:
            out[key] = compact
    # Preserve small top-level meta if present
    for meta_key in ("scope", "intent", "event_timing_verdict", "normalized_evidence"):
        if meta_key in branches and branches[meta_key] is not None:
            try:
                out[meta_key] = json.loads(
                    _truncate(json.dumps(branches[meta_key], ensure_ascii=False, default=str), 8000)
                )
            except Exception:
                out[meta_key] = _truncate(str(branches[meta_key]), 2500)
    return out


def infer_qa_intent_stub(question: str) -> Dict[str, Any]:
    """Lightweight intent stub so rebuilt context includes the right divisionals."""
    q = (question or "").lower()
    category = "general"
    mode = "ANALYZE_TOPIC_POTENTIAL"
    divisionals = ["D1", "D9"]

    if any(w in q for w in ("job", "career", "offer letter", "hiring", "interview", "salary", "mnc", "promotion", "unemploy")):
        category = "career"
        mode = "LIFESPAN_EVENT_TIMING"
        divisionals = ["D1", "D9", "D10"]
    elif any(w in q for w in ("marri", "spouse", "wedding", "husband", "wife", "divorce")):
        category = "marriage"
        mode = "LIFESPAN_EVENT_TIMING"
        divisionals = ["D1", "D9", "D7"]
    elif any(w in q for w in ("child", "pregnan", "baby", "conceive")):
        category = "children"
        mode = "LIFESPAN_EVENT_TIMING"
        divisionals = ["D1", "D9", "D7"]
    elif any(w in q for w in ("health", "disease", "illness", "hospital")):
        category = "health"
        mode = "ANALYZE_TOPIC_POTENTIAL"
        divisionals = ["D1", "D9", "D30"]
    elif any(w in q for w in ("money", "wealth", "finance", "income", "debt")):
        category = "wealth"
        mode = "ANALYZE_TOPIC_POTENTIAL"
        divisionals = ["D1", "D9", "D10"]
    elif any(w in q for w in ("when will", "timing", "which year", "which month")):
        mode = "LIFESPAN_EVENT_TIMING"

    return {
        "status": "READY",
        "mode": mode,
        "category": category,
        "needs_transits": True,
        "divisional_charts": divisionals,
        "source": "admin_response_qa_infer",
    }


def _cap_json_value(value: Any, limit: int) -> Any:
    """Keep structure when possible; fall back to truncated JSON string."""
    try:
        raw = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return _truncate(str(value), limit)
    if len(raw) <= limit:
        return value
    if isinstance(value, dict):
        slim: Dict[str, Any] = {}
        # Keep small/critical keys preferentially.
        for k, v in value.items():
            piece = json.dumps(v, ensure_ascii=False, default=str)
            if len(piece) <= max(400, limit // 12):
                slim[k] = v
            else:
                slim[k] = _truncate(piece, max(400, limit // 12))
        return slim
    return _truncate(raw, limit)


def compact_generation_context(full_context: Dict[str, Any], *, max_chars: int = 120000) -> Dict[str, Any]:
    """Compress rebuilt chat context into an examiner-usable generation packet."""
    from ai.parallel_chat.context_slices import (
        build_ashtakavarga_slice,
        build_jaimini_slice,
        build_kp_slice,
        build_nadi_slice,
        build_nakshatra_slice,
        build_parashari_slice,
        build_shared_kernel_lite,
        build_sudarshan_slice,
    )

    shared = build_shared_kernel_lite(full_context)
    # d1_chart can be huge; keep ascendant + planet placements essentials via existing minify if present.
    if isinstance(shared.get("d1_chart"), dict):
        d1 = shared["d1_chart"]
        shared["d1_chart"] = {
            k: d1.get(k)
            for k in ("planets", "ascendant", "houses", "house_cusps", "lagna")
            if k in d1
        } or _cap_json_value(d1, 18000)

    parashari = build_parashari_slice(full_context)
    for heavy in (
        "unified_dasha_timeline",
        "period_dasha_activations",
        "macro_transits_timeline",
        "transit_activations",
        "yogas",
        "advanced_analysis",
        "d1_chart",  # already in shared_kernel
    ):
        parashari.pop(heavy, None)
    if isinstance(parashari.get("divisional_charts"), dict):
        # Keep topic divisionals but cap each.
        capped_divs = {}
        for name, chart in list(parashari["divisional_charts"].items())[:6]:
            capped_divs[name] = _cap_json_value(chart, 8000)
        parashari["divisional_charts"] = capped_divs

    jaimini = build_jaimini_slice(full_context)
    jaimini.pop("jaimini_full_analysis", None)

    packet: Dict[str, Any] = {
        "source": "rebuilt_for_qa",
        "note": (
            "Rebuilt from the session birth chart + current question for full QA. "
            "Not a byte-identical replay of the original prompt, but the same chart math spine "
            "the product uses (dashas, divisionals, AV, KP, Jaimini, etc.)."
        ),
        "intent": full_context.get("intent"),
        "shared_kernel": _cap_json_value(shared, 35000),
        "parashari": _cap_json_value(parashari, 40000),
        "ashtakavarga": _cap_json_value(build_ashtakavarga_slice(full_context), 18000),
        "jaimini": _cap_json_value(jaimini, 16000),
        "kp": _cap_json_value(build_kp_slice(full_context), 16000),
        "nadi": _cap_json_value(build_nadi_slice(full_context), 10000),
        "nakshatra": _cap_json_value(build_nakshatra_slice(full_context), 10000),
        "sudarshan": _cap_json_value(build_sudarshan_slice(full_context), 10000),
    }

    raw = json.dumps(packet, ensure_ascii=False, default=str)
    if len(raw) <= max_chars:
        return packet

    # Last-resort: shrink optional schools first, keep shared + parashari + AV + KP.
    for optional_key in ("sudarshan", "nakshatra", "nadi", "jaimini"):
        if optional_key in packet:
            packet[optional_key] = {"_truncated": True, "note": f"{optional_key} omitted to fit examiner budget"}
        raw = json.dumps(packet, ensure_ascii=False, default=str)
        if len(raw) <= max_chars:
            return packet
    packet["parashari"] = _cap_json_value(packet.get("parashari"), 25000)
    packet["shared_kernel"] = _cap_json_value(packet.get("shared_kernel"), 25000)
    return packet


def rebuild_generation_context_for_qa(
    *,
    birth_details: Dict[str, Any],
    question: str,
    intent_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Rebuild the chart/dasha generation spine used for answering.
    Returns {ok, context_compact, intent, error, char_count}.
    """
    try:
        from chat.chat_context_builder import ChatContextBuilder
        from utils.timezone_service import parse_timezone_offset

        intent = intent_override or infer_qa_intent_stub(question)
        date_raw = str(birth_details.get("date") or "")
        time_raw = str(birth_details.get("time") or "")
        date = date_raw.split("T")[0] if "T" in date_raw else date_raw
        time_part = time_raw.split("T")[1][:5] if "T" in time_raw else time_raw
        if time_part.count(":") >= 2:
            hh, mm, *_ = time_part.split(":")
            time_part = f"{hh}:{mm}"
        lat = float(birth_details["latitude"])
        lon = float(birth_details["longitude"])
        tz = birth_details.get("timezone")
        if tz is None or tz == "":
            try:
                tz = parse_timezone_offset("", lat, lon)
            except Exception:
                tz = 5.5
        birth_data = {
            "name": birth_details.get("name") or "Native",
            "date": date,
            "time": time_part,
            "latitude": lat,
            "longitude": lon,
            "place": birth_details.get("place") or "Unknown",
            "timezone": tz,
        }
        builder = ChatContextBuilder()
        full = builder.build_complete_context(
            birth_data,
            user_question=question or "",
            intent_result=intent,
        )
        compact = compact_generation_context(full)
        raw = json.dumps(compact, ensure_ascii=False, default=str)
        return {
            "ok": True,
            "context_compact": compact,
            "intent": intent,
            "error": None,
            "char_count": len(raw),
        }
    except Exception as e:
        logger.exception("Failed rebuilding generation context for QA")
        return {
            "ok": False,
            "context_compact": None,
            "intent": intent_override or infer_qa_intent_stub(question),
            "error": str(e),
            "char_count": 0,
        }


def extract_date_mentions(text: str) -> List[str]:
    plain = strip_html(text)
    found: List[str] = []
    for m in DATE_RANGE_RE.finditer(plain):
        found.append(f"{m.group('a').strip()} – {m.group('b').strip()}")
    for m in SINGLE_DATE_RE.finditer(plain):
        token = m.group(0).strip()
        if not any(token.lower() in f.lower() for f in found):
            found.append(token)
    # de-dupe preserving order
    seen = set()
    uniq: List[str] = []
    for item in found:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(item)
    return uniq[:40]


def run_deterministic_precheck(
    *,
    answer_text: str,
    prior_assistant_texts: List[str],
    question_text: str,
) -> Dict[str, Any]:
    answer = strip_html(answer_text)
    question = strip_html(question_text)
    priors = [strip_html(p) for p in prior_assistant_texts if p]

    overclaims = []
    for pat in OVERCLAIM_PATTERNS:
        for m in pat.finditer(answer):
            overclaims.append(m.group(0))

    answer_dates = extract_date_mentions(answer)
    prior_dates: List[str] = []
    for p in priors:
        prior_dates.extend(extract_date_mentions(p))

    activation_hits = [c for c in ACTIVATION_CUES if c in answer.lower()]
    result_hits = [c for c in RESULT_CUES if c in answer.lower()]
    layer_risk = bool(activation_hits and result_hits)

    house_flips = []
    corpus = "\n\n".join(priors + [answer])
    for name, pos, neg in HOUSE_FLIP_PATTERNS:
        if pos.search(corpus) and neg.search(corpus):
            house_flips.append(name)

    # Crude primary-window drift: if a prior mentions Jul..Aug as offer and current demotes it
    timing_drift_hints: List[str] = []
    prior_blob = " ".join(priors).lower()
    answer_l = answer.lower()
    if priors:
        prior_july_offer = (
            ("july" in prior_blob or "jul" in prior_blob)
            and ("august" in prior_blob or "aug" in prior_blob)
            and any(x in prior_blob for x in ("offer", "first job", "breakthrough", "joining"))
        )
        current_demotes = any(
            x in answer_l
            for x in ("near-miss", "near miss", "activity but not", "not closing", "medium")
        ) and any(x in answer_l for x in ("august 28", "late august", "october"))
        if prior_july_offer and current_demotes:
            timing_drift_hints.append(
                "Prior turns emphasized July–August as offer/breakthrough; current answer demotes that band toward near-miss / late-August result."
            )

    q_l = question.lower()
    consistency_challenge = any(
        x in q_l
        for x in (
            "fake",
            "different",
            "previously told",
            "you told",
            "inaccurate",
            "contradict",
            "something else",
        )
    )

    flags: List[Dict[str, str]] = []
    if overclaims:
        flags.append(
            {
                "severity": "high",
                "category": "overclaim",
                "note": f"Deterministic overclaim language: {', '.join(sorted(set(overclaims))[:8])}",
            }
        )
    if layer_risk:
        flags.append(
            {
                "severity": "high",
                "category": "layer_conflation",
                "note": (
                    "Answer mixes activation cues "
                    f"({', '.join(activation_hits[:4])}) with result cues "
                    f"({', '.join(result_hits[:4])}) — verify they are cleanly separated."
                ),
            }
        )
    if house_flips:
        flags.append(
            {
                "severity": "critical",
                "category": "contradiction",
                "note": f"Cross-turn house signification flip detected: {', '.join(house_flips)}",
            }
        )
    for hint in timing_drift_hints:
        flags.append({"severity": "critical", "category": "timing_drift", "note": hint})
    if consistency_challenge:
        flags.append(
            {
                "severity": "high",
                "category": "user_care",
                "note": "User is challenging consistency/truthfulness — audit must address prior promises explicitly.",
            }
        )

    return {
        "overclaim_matches": sorted(set(overclaims)),
        "answer_date_mentions": answer_dates,
        "prior_date_mentions": prior_dates[:40],
        "activation_cues": activation_hits,
        "result_cues": result_hits,
        "layer_conflation_risk": layer_risk,
        "house_signification_flips": house_flips,
        "timing_drift_hints": timing_drift_hints,
        "user_consistency_challenge": consistency_challenge,
        "flags": flags,
    }


def _extract_json_object(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            if isinstance(obj, dict):
                return obj
        except Exception:
            return None
    return None


def _fallback_report(precheck: Dict[str, Any], error: str) -> Dict[str, Any]:
    findings = []
    for flag in precheck.get("flags") or []:
        findings.append(
            {
                "id": f"precheck_{flag.get('category')}",
                "severity": flag.get("severity") or "medium",
                "category": flag.get("category") or "technique_error",
                "claim_in_answer": "",
                "evidence_problem": flag.get("note") or "",
                "classical_correction": "Re-run full auditor once LLM is available; apply deterministic flag immediately.",
                "product_fix": "Block overclaim language; separate activation vs offer vs joining; lock timing anchors on follow-ups.",
            }
        )
    return {
        "overall_grade": "C" if findings else "I",
        "trust_risk": "high" if findings else "medium",
        "executive_summary": (
            "Deterministic precheck completed, but the LLM examiner failed. "
            f"Error: {error}"
        ),
        "question_answered": None,
        "layers": {
            "activation_vs_result": {
                "status": "unknown",
                "notes": "LLM examiner unavailable",
            },
            "timing_consistency": {
                "status": "flagged" if precheck.get("timing_drift_hints") else "unknown",
                "notes": "; ".join(precheck.get("timing_drift_hints") or []) or "LLM examiner unavailable",
            },
            "technical_astrology": {"status": "unknown", "notes": "LLM examiner unavailable"},
            "language_and_certainty": {
                "status": "fail" if precheck.get("overclaim_matches") else "unknown",
                "notes": ", ".join(precheck.get("overclaim_matches") or []) or "LLM examiner unavailable",
            },
            "branch_fidelity": {"status": "unknown", "notes": "LLM examiner unavailable"},
        },
        "findings": findings,
        "timing_contract": {
            "windows_claimed": precheck.get("answer_date_mentions") or [],
            "primary_window": None,
            "activation_window": None,
            "result_window": None,
            "consistency_with_prior": "unknown",
        },
        "corrected_executive_summary": "",
        "prompt_rule_proposals": [
            "Never equate dasha micro-period start with event delivery.",
            "On follow-ups, load prior timing contract and forbid silent Window-1 re-rank.",
            "Ban guarantee / mathematical-certainty phrasing in lifespan event answers.",
        ],
        "knowledge_test_notes": "Partial report from deterministic exam only.",
        "auditor_error": error,
    }


def build_auditor_user_packet(
    *,
    question: str,
    answer: str,
    prior_turns: List[Dict[str, str]],
    branch_compact: Dict[str, Any],
    precheck: Dict[str, Any],
    generation_context: Optional[Dict[str, Any]] = None,
    native_name: Optional[str] = None,
    admin_notes: Optional[str] = None,
) -> str:
    schema = {
        "overall_grade": "A|B|C|D|F",
        "trust_risk": "critical|high|medium|low",
        "executive_summary": "2-4 sentences: what failed or passed as an astrology exam",
        "question_answered": True,
        "layers": {
            "activation_vs_result": {"status": "pass|warn|fail", "notes": "..."},
            "timing_consistency": {"status": "pass|warn|fail", "notes": "..."},
            "technical_astrology": {"status": "pass|warn|fail", "notes": "..."},
            "language_and_certainty": {"status": "pass|warn|fail", "notes": "..."},
            "branch_fidelity": {"status": "pass|warn|fail|unavailable", "notes": "..."},
        },
        "findings": [
            {
                "id": "short_id",
                "severity": "critical|high|medium|low",
                "category": "timing_drift|overclaim|contradiction|technique_error|layer_conflation|branch_ignore|user_care|other",
                "claim_in_answer": "quote or paraphrase",
                "evidence_problem": "why wrong vs evidence/classical method",
                "classical_correction": "what a correct jyotishi reading should say",
                "product_fix": "prompt/rule/engine change",
            }
        ],
        "timing_contract": {
            "windows_claimed": ["..."],
            "primary_window": "...",
            "activation_window": "... or null",
            "result_window": "... or null",
            "consistency_with_prior": "aligned|shifted|unknown",
        },
        "corrected_executive_summary": "Honest rewritten executive summary the product should have given",
        "prompt_rule_proposals": ["concrete rule 1", "concrete rule 2"],
        "knowledge_test_notes": "Exam-style notes: marks lost and why",
    }
    packet = {
        "native_name": native_name or "",
        "current_question": strip_html(question),
        "final_answer_under_exam": strip_html(answer),
        "prior_turns_oldest_first": [
            {
                "role": t.get("role"),
                "text": _truncate(strip_html(t.get("text") or ""), 4500),
            }
            for t in prior_turns[-8:]
        ],
        "specialist_branch_outputs_compact": branch_compact,
        "generation_context": generation_context or {
            "source": "unavailable",
            "note": "Generation context could not be rebuilt for this message.",
        },
        "deterministic_precheck": precheck,
        "admin_notes": (admin_notes or "").strip(),
        "required_json_schema": schema,
        "examiner_instructions": [
            "Grade harshly but fairly.",
            "Use generation_context as the technical ground truth for chart/dasha/AV/KP claims.",
            "Every critical/high finding must include classical_correction AND product_fix.",
            "If user challenged prior consistency, findings must explicitly reconcile prior vs current windows.",
            "Prefer 4-10 findings; do not pad with fluff.",
            "If branches are empty, set branch_fidelity.status=unavailable and still grade using generation_context + narrative.",
            "If generation_context.source is rebuilt_for_qa, treat it as authoritative chart math for this exam.",
        ],
    }
    return (
        "Examine this AstroRoshni answer packet and return ONLY JSON.\n\n"
        + json.dumps(packet, ensure_ascii=False, default=str)
    )


async def audit_astrology_response(
    *,
    question: str,
    answer: str,
    prior_turns: Optional[List[Dict[str, str]]] = None,
    branch_outputs: Optional[Dict[str, Any]] = None,
    generation_context: Optional[Dict[str, Any]] = None,
    generation_context_meta: Optional[Dict[str, Any]] = None,
    native_name: Optional[str] = None,
    admin_notes: Optional[str] = None,
    analyzer: Any = None,
) -> Dict[str, Any]:
    """
    Run deterministic precheck + Gemini Pro examiner with generation context.
    Returns a structured report dict.
    """
    prior_turns = prior_turns or []
    prior_assistant = [t.get("text") or "" for t in prior_turns if (t.get("role") or "").lower() == "assistant"]
    precheck = run_deterministic_precheck(
        answer_text=answer,
        prior_assistant_texts=prior_assistant,
        question_text=question,
    )
    branch_compact = compact_branch_outputs(branch_outputs)
    gen_meta = generation_context_meta or {}
    user_prompt = build_auditor_user_packet(
        question=question,
        answer=answer,
        prior_turns=prior_turns,
        branch_compact=branch_compact,
        precheck=precheck,
        generation_context=generation_context,
        native_name=native_name,
        admin_notes=admin_notes,
    )

    started = datetime.utcnow()
    llm_meta: Dict[str, Any] = {}
    report: Optional[Dict[str, Any]] = None
    raw_response = ""

    try:
        from utils.admin_settings import DEFAULT_GEMINI_PREMIUM_MODEL, get_gemini_premium_model
        from ai.gemini_chat_analyzer import GeminiChatAnalyzer

        if analyzer is None:
            analyzer = GeminiChatAnalyzer()

        pro_model_name = (get_gemini_premium_model() or "").strip() or DEFAULT_GEMINI_PREMIUM_MODEL
        pro_model = analyzer.get_named_gemini_model(pro_model_name, premium_analysis=True)

        full_prompt = f"{AUDITOR_SYSTEM}\n\n---\n\n{user_prompt}"
        llm_out = await analyzer.generate_text_from_prompt(
            full_prompt,
            premium_analysis=True,
            force_gemini=True,
            model_name_override=pro_model_name,
            model_override=pro_model,
            llm_log_tag="admin_response_qa_auditor",
            request_timeout_s=240.0,
        )
        llm_meta = {
            "success": bool(llm_out.get("success")),
            "model": llm_out.get("chat_llm_model") or pro_model_name,
            "provider": llm_out.get("chat_llm_provider") or "gemini",
            "forced_pro": True,
            "requested_model": pro_model_name,
            "token_usage": llm_out.get("token_usage") or {},
            "elapsed_s": llm_out.get("elapsed_s"),
            "error": llm_out.get("error"),
        }
        raw_response = llm_out.get("response") or ""
        if not llm_out.get("success"):
            report = _fallback_report(precheck, str(llm_out.get("error") or "LLM call failed"))
        else:
            report = _extract_json_object(raw_response)
            if not report:
                report = _fallback_report(precheck, "LLM returned non-JSON examiner output")
                report["raw_examiner_excerpt"] = _truncate(raw_response, 2500)
    except Exception as e:
        logger.exception("response QA auditor failed")
        report = _fallback_report(precheck, str(e))

    assert report is not None
    # Merge deterministic flags that the model may have missed
    existing_cats = {(f.get("category"), f.get("evidence_problem")) for f in (report.get("findings") or []) if isinstance(f, dict)}
    for flag in precheck.get("flags") or []:
        key = (flag.get("category"), flag.get("note"))
        if key in existing_cats:
            continue
        findings = report.setdefault("findings", [])
        if isinstance(findings, list):
            findings.append(
                {
                    "id": f"precheck_{flag.get('category')}",
                    "severity": flag.get("severity") or "medium",
                    "category": flag.get("category") or "other",
                    "claim_in_answer": "",
                    "evidence_problem": flag.get("note") or "",
                    "classical_correction": "Acknowledge deterministic exam flag; reconcile with classical timing layers.",
                    "product_fix": "Enforce timing-contract lock and overclaim bans in lifespan career answers.",
                    "source": "deterministic_precheck",
                }
            )

    report["deterministic_precheck"] = precheck
    report["evidence_available"] = {
        "branch_keys": sorted(list(branch_compact.keys())),
        "prior_turn_count": len(prior_turns),
        "has_branches": bool(branch_compact),
        "has_generation_context": bool(generation_context),
        "generation_context_chars": int(gen_meta.get("char_count") or 0),
        "generation_context_error": gen_meta.get("error"),
        "generation_context_intent": gen_meta.get("intent"),
    }
    report["auditor_meta"] = {
        **llm_meta,
        "elapsed_total_s": round((datetime.utcnow() - started).total_seconds(), 3),
        "auditor_version": "1.1.0",
    }
    return report
