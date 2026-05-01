from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


_MICRO_INTENT_RULES: Dict[str, Dict[str, Any]] = {
    "communication": {
        "keywords": (
            "call", "text", "message", "reply", "respond", "email", "mail", "whatsapp", "sms",
            "talk", "conversation", "speak", "saying", "pitch", "proposal", "presentation",
            "negotiat", "discuss", "follow up", "follow-up", "send",
        ),
        "houses": [3, 7, 11],
        "fast_planets": ["Mercury", "Moon", "Venus"],
        "daily_focus": "message delivery, response quality, clarity, and social receptivity",
        "best_for": ["sending important communication", "follow-ups", "clear negotiation"],
        "watch_for": ["misunderstanding", "late replies", "over-explaining", "emotional tone drift"],
    },
    "interview_meeting": {
        "keywords": (
            "interview", "meeting", "panel", "discussion", "review", "presentation", "boss",
            "manager", "client", "appointment", "demo", "pitch", "office", "conference",
        ),
        "houses": [3, 6, 10, 11],
        "fast_planets": ["Mercury", "Sun", "Moon"],
        "daily_focus": "authority contact, performance under pressure, and impression management",
        "best_for": ["interviews", "formal meetings", "client-facing delivery"],
        "watch_for": ["nervous speech", "ego clashes", "timing pressure", "avoidable mistakes"],
    },
    "money_payment": {
        "keywords": (
            "money", "payment", "pay", "collect", "salary", "invoice", "bill", "transaction",
            "bank", "loan", "credit", "debit", "refund", "invest", "investment", "buy", "sell",
            "purchase", "finance", "cash",
        ),
        "houses": [2, 8, 11],
        "fast_planets": ["Mercury", "Venus", "Moon"],
        "daily_focus": "cash flow, collections, purchase judgment, and financial timing",
        "best_for": ["collections", "payments", "practical money decisions"],
        "watch_for": ["impulse spending", "confused terms", "avoidable leakage", "poor bargain timing"],
    },
    "relationship_outreach": {
        "keywords": (
            "relationship", "partner", "boyfriend", "girlfriend", "husband", "wife", "spouse",
            "love", "romance", "date", "proposal", "reconcile", "apolog", "patch up", "patch-up",
            "talk to him", "talk to her", "reach out", "contact him", "contact her",
        ),
        "houses": [5, 7, 11],
        "fast_planets": ["Venus", "Moon", "Mercury"],
        "daily_focus": "emotional rhythm, receptivity, affection, and partnership tone",
        "best_for": ["relationship outreach", "repair conversations", "romantic initiative"],
        "watch_for": ["oversensitivity", "mixed signals", "reactive words", "expectation mismatch"],
    },
    "travel_commute": {
        "keywords": (
            "travel", "trip", "journey", "commute", "drive", "driving", "flight", "train", "bus",
            "cab", "taxi", "traffic", "road", "ride", "visit", "go out", "leave today",
        ),
        "houses": [3, 9, 12],
        "fast_planets": ["Moon", "Mars", "Mercury"],
        "daily_focus": "movement, delays, route smoothness, and travel fatigue",
        "best_for": ["short trips", "planned movement", "travel with buffers"],
        "watch_for": ["delay", "friction", "haste", "navigation confusion", "fatigue"],
    },
    "health_treatment": {
        "keywords": (
            "health", "doctor", "treatment", "medicine", "test", "scan", "surgery", "procedure",
            "clinic", "hospital", "pain", "fever", "rest", "therapy", "counselling", "counseling",
            "exercise", "workout",
        ),
        "houses": [1, 6, 8, 12],
        "fast_planets": ["Moon", "Mars", "Sun"],
        "daily_focus": "vitality, irritation, recovery support, and treatment timing",
        "best_for": ["medical follow-through", "rest discipline", "planned treatment"],
        "watch_for": ["inflammation", "stress spikes", "overexertion", "avoidable aggravation"],
    },
    "study_exam": {
        "keywords": (
            "study", "exam", "test", "interview exam", "result", "class", "lecture", "learn",
            "revision", "revise", "focus", "concentrat", "assignment", "course", "education",
            "school", "college",
        ),
        "houses": [4, 5, 9],
        "fast_planets": ["Mercury", "Moon", "Sun"],
        "daily_focus": "retention, concentration, confidence, and academic output",
        "best_for": ["study blocks", "revision", "exam composure"],
        "watch_for": ["scattered mind", "memory slips", "rush errors", "mental fatigue"],
    },
    "decision_signing": {
        "keywords": (
            "sign", "agreement", "contract", "document", "paperwork", "deal", "decision", "decide",
            "finalize", "finalise", "approve", "submit", "apply", "application", "register",
            "commit", "booking",
        ),
        "houses": [3, 7, 10, 11],
        "fast_planets": ["Mercury", "Sun", "Venus"],
        "daily_focus": "judgment quality, formal commitment, and execution timing",
        "best_for": ["paperwork", "measured commitments", "submissions"],
        "watch_for": ["hidden clauses", "avoidable haste", "ego pressure", "terms not fully clear"],
    },
    "confrontation": {
        "keywords": (
            "fight", "argument", "confront", "complain", "complaint", "dispute", "case", "court",
            "legal", "enemy", "oppose", "challenge", "pressure", "demand", "angry", "angrily",
        ),
        "houses": [6, 7, 8],
        "fast_planets": ["Mars", "Mercury", "Moon"],
        "daily_focus": "conflict containment, emotional volatility, and strategic response",
        "best_for": ["measured pushback", "structured complaints", "controlled firmness"],
        "watch_for": ["escalation", "ego reactions", "aggressive words", "pointless provocation"],
    },
    "general_day": {
        "keywords": (),
        "houses": [1, 4, 7, 10, 11],
        "fast_planets": ["Moon", "Mercury", "Venus", "Sun"],
        "daily_focus": "overall momentum, mood, and practical use of the day",
        "best_for": ["general planning", "balanced action", "using the cleanest window well"],
        "watch_for": ["drift", "mixed priorities", "wasting favorable windows"],
    },
}

_CATEGORY_DEFAULTS = {
    "career": "interview_meeting",
    "job": "interview_meeting",
    "promotion": "interview_meeting",
    "business": "communication",
    "love": "relationship_outreach",
    "relationship": "relationship_outreach",
    "marriage": "relationship_outreach",
    "partner": "relationship_outreach",
    "travel": "travel_commute",
    "health": "health_treatment",
    "disease": "health_treatment",
    "education": "study_exam",
    "learning": "study_exam",
    "wealth": "money_payment",
    "money": "money_payment",
    "finance": "money_payment",
}


def _normalize(text: str) -> str:
    low = (text or "").lower()
    low = re.sub(r"[^a-z0-9\s]", " ", low)
    return re.sub(r"\s+", " ", low).strip()


def _score_rule(normalized_question: str, keywords: Tuple[str, ...]) -> Tuple[int, List[str]]:
    score = 0
    matched: List[str] = []
    for raw_kw in keywords:
        kw = _normalize(raw_kw)
        if not kw:
            continue
        if " " in kw:
            hit = kw in normalized_question
        else:
            hit = bool(re.search(rf"\b{re.escape(kw)}", normalized_question))
        if hit:
            matched.append(raw_kw)
            score += 2 if " " in kw else 1
    return score, matched


def classify_daily_micro_intent(user_question: str, category: str | None = None) -> Dict[str, Any]:
    normalized = _normalize(user_question)
    category_low = str(category or "general").strip().lower()

    best_name = "general_day"
    best_score = -1
    best_matches: List[str] = []

    for name, rule in _MICRO_INTENT_RULES.items():
        if name == "general_day":
            continue
        score, matches = _score_rule(normalized, tuple(rule.get("keywords") or ()))
        if category_low and _CATEGORY_DEFAULTS.get(category_low) == name:
            score += 1
        if score > best_score:
            best_name = name
            best_score = score
            best_matches = matches

    if best_score <= 0:
        best_name = _CATEGORY_DEFAULTS.get(category_low, "general_day")
        best_matches = []

    rule = _MICRO_INTENT_RULES[best_name]
    confidence = "high" if best_score >= 3 else "moderate" if best_score >= 1 else "defaulted"

    return {
        "name": best_name,
        "confidence": confidence,
        "matched_terms": best_matches,
        "source_category": category_low or "general",
        "houses": list(rule.get("houses") or []),
        "fast_planets": list(rule.get("fast_planets") or []),
        "daily_focus": str(rule.get("daily_focus") or ""),
        "best_for": list(rule.get("best_for") or []),
        "watch_for": list(rule.get("watch_for") or []),
        "summary": f"{best_name.replace('_', ' ')} focus: {rule.get('daily_focus') or ''}".strip(),
    }


def get_daily_micro_intent_profile(name: str) -> Dict[str, Any]:
    rule = _MICRO_INTENT_RULES.get(str(name or "").strip(), _MICRO_INTENT_RULES["general_day"])
    return {
        "name": str(name or "general_day").strip() or "general_day",
        "houses": list(rule.get("houses") or []),
        "fast_planets": list(rule.get("fast_planets") or []),
        "daily_focus": str(rule.get("daily_focus") or ""),
        "best_for": list(rule.get("best_for") or []),
        "watch_for": list(rule.get("watch_for") or []),
    }
