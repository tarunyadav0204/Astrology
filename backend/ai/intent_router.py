import google.generativeai as genai
import json
import os
import re
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict

from ai.question_heuristics import looks_like_many_questions
from ai.output_schema import resolve_output_language_policy

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


def merge_divisional_charts_with_category_defaults(result: Dict) -> None:
    """
    After the model returns divisional_charts, ensure the list includes every chart required for
    `category` (additive merge — extra charts from the model are kept). Fixes omissions like D24 for education.
    """
    required = get_default_divisional_charts_for_category(str(result.get("category") or "general"))
    raw = result.get("divisional_charts")
    if not isinstance(raw, list):
        result["divisional_charts"] = list(required)
        return
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


def apply_transit_timing_guards(result: Dict, user_question: str, *, current_year: int, now: datetime | None = None) -> None:
    """
    Post-process router output: career/education (and related) questions that ask *when* or *whether*
    (will I / which year / job vs study) must request transits so the backend builds transit windows.
    """
    q = (user_question or "").strip().lower()
    cat = (result.get("category") or "general").strip().lower()
    now_dt = (now or datetime.now()).replace(hour=12, minute=0, second=0, microsecond=0)
    exact_date = _extract_specific_date_from_question(user_question, now=now_dt)

    if exact_date:
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
            print(f"✅ Intent router fallback model: {model_name}")
        except Exception as e:
            fallback_fast = "models/gemini-2.0-flash-lite-001"
            print(f"⚠️ Intent router model {model_name} not available ({e}), trying default")
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
            print(f"⚠️ Intent router model {name} not available ({e}), using fallback")
            return self.model
        
    async def classify_intent(self, user_question: str, chat_history: list = None, user_facts: dict = None, clarification_count: int = 0, language: str = 'english', force_ready: bool = False, d1_chart: dict = None, force_clarify: bool = False) -> Dict[str, str]:
        """
        Returns: {'status': 'CLARIFY' | 'READY', 'mode': 'PREDICT_DAILY' | 'ANALYZE_PERSONALITY' | ..., 'category': 'job'|'love'|..., 'needs_transits': bool, 'transit_request': {...}, 'extracted_context': {...}, 'context_type': 'birth' | 'annual'}
        """
        chat_history = chat_history or []
        user_facts = user_facts or {}
        import time
        from datetime import datetime
        
        intent_start = time.time()
        print(f"\n{'='*80}")
        print(f"🧠 INTENT CLASSIFICATION STARTED")
        print(f"{'='*80}")
        print(f"Question: {user_question}")
        
        current_year = datetime.now().year
        current_month = datetime.now().strftime('%B')
        current_date = datetime.now().strftime('%Y-%m-%d')
        
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
If the user's current message clearly packs SEVERAL distinct questions into one (e.g. two or more "?" marks, numbered asks like "1. ... 2. ...", phrases like "another question" / "few questions", or clearly separate topics joined with ";" / "also"), then:
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
2) If status is "READY": every "message" inside "chart_insights" MUST be in the language of CURRENT QUESTION.

Examples:
- English question -> English strings.
- Hindi Devanagari question -> Hindi strings in Devanagari.
- Hinglish / Roman Hindi question -> Hindi strings in Devanagari, not Roman Hindi.
- Tamil question -> Tamil strings.
- Telugu/Gujarati/Marathi/Bengali/French/German/Russian/Chinese/etc. question -> same language and script.

Only if CURRENT QUESTION is too short or language-ambiguous, use app-selected language "{app_language}" as fallback.
JSON keys stay English; only end-user string values change language.
"""

        chart_insights_message_spec = (
            '- message: SPECIFIC insight about THIS native\'s chart, written in the language and natural script '
            'you infer from CURRENT QUESTION. For Hinglish/Roman Hindi, write the message in Hindi Devanagari.'
        )
        chart_insights_example_block = """
        Example structure only. Replace bracketed text with real chart-specific prose in the inferred CURRENT QUESTION language:
        "chart_insights": [
            {"house_number": 1, "message": "[real insight in inferred CURRENT QUESTION language]", "highlight_type": "ascendant"},
            {"house_number": 2, "message": "[real insight in inferred CURRENT QUESTION language]", "highlight_type": "planets"},
            {"house_number": 5, "message": "[real insight in inferred CURRENT QUESTION language]", "highlight_type": "planets"}
        ]
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
Keep it warm and polite. Do not ask for birth details.
The clarification_question MUST follow the language rule and use the inferred CURRENT QUESTION language/script.
"""

        prompt = f"""
        You are a clarification assistant for an astrology chatbot. Your job is to determine if a question is too vague and needs clarification, and to classify the user's intent.
        
        🚨 CRITICAL INSTRUCTION FOR chart_insights:
        - When status is "READY", you MUST generate chart_insights array with 5-7 house insights
        - When status is "CLARIFY", set chart_insights to null
        - chart_insights is MANDATORY when status="READY"
        - DO NOT return null for chart_insights when status="READY"
        
        🚨 ABSOLUTE PROHIBITION - NEVER ASK FOR BIRTH DETAILS:
        - The user's complete birth chart data is ALREADY PROVIDED in the D1_CHART_DATA below
        - You have access to ALL planetary positions, houses, and signs
        - NEVER ask for birth date, time, place, or any birth information
        - If a question seems to need birth details, use the provided chart data to answer
        - Only ask clarification about WHICH ASPECT of their life they want to focus on (career, health, relationships, etc.)
        
        {force_ready_instruction}
        {force_clarify_instruction}
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

        - "PREDICT_DAILY": For daily predictions (e.g., "How is today?", "What's in store for me today?").
        - "LIFESPAN_EVENT_TIMING": For open-ended "When" questions about major life events (e.g., "When will I get married?", "When did I buy my house?", "When will my daughter get married?", "In which year did I get married?"). 
          🚨 CRITICAL: Use this mode when the user's message is **primarily** a single timing question about one life event.
          🚨 EXCEPTION — BUNDLED MULTI-TOPIC MESSAGES: If the same message also asks **other unrelated** things (e.g. spouse nature, career, wealth, health) in separate sentences or clauses, you MUST NOT force READY just because one part is a "when" question. Return status: "CLARIFY" and ask which **one** topic to address first (or to send one question at a time), unless the clarification limit already applies.
          🚨 When the message is **only** a when/year question about one topic: return status: "READY" with this mode. Do not ask clarification for that narrow case.
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

        CHART INSIGHTS:
        🚨 MANDATORY REQUIREMENT 🚨
        When status is "READY", you MUST generate chart_insights using the D1 chart data provided.
        DO NOT set chart_insights to null when status is "READY".
        
        D1 CHART DATA PROVIDED:
        {json.dumps(d1_chart) if d1_chart else 'No chart data available'}
        
        Generate a `chart_insights` array with 5-7 objects analyzing THIS NATIVE'S SPECIFIC CHART.
        Look at which planets are in which houses and signs, then provide SPECIFIC insights.
        
        Each object MUST have:
        - house_number: (1-12)
        {chart_insights_message_spec}
        - highlight_type: "ascendant" | "planets" | "empty"
        
        DO NOT give generic house meanings. Analyze the ACTUAL planetary placements in the chart.
        {chart_insights_example_block}

        Return ONLY a JSON object:
        {{
            "status": "CLARIFY" or "READY",
            "clarification_question": "Your clarifying question here (only if status=CLARIFY; if user wrote Hindi/Hinglish, this string must be Devanagari Hindi)",
            "chart_insights": [{{"house_number": 1, "message": "Devanagari Hindi prose for Hinglish users; English for English-only questions", "highlight_type": "ascendant"}}],
            "mode": "PREDICT_DAILY" or "PREDICT_EVENT_TIMING" or "ANALYZE_PERSONALITY",
            "chart_focus": {{
                "kind": "chart_specific",
                "primary": "D1 or D9 or D10 or D7 or Karkamsa or Swamsa",
                "label": "Lagna or D10 or Navamsha",
                "explicit": true,
                "phrase": "the phrase or implied lens you detected",
                "requested": ["D10"]
            }} or null,
            "extracted_context": {{ "timeframe": "2025", "aspect": "promotion" }},
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
        print(f"\n📤 INTENT ROUTER REQUEST:")
        print(f"Model: {model_name}")
        print(f"Prompt length: {len(prompt)} characters")
        
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
            print(f"🔍 RAW INTENT RESPONSE: {cleaned}")
            result = json.loads(cleaned)
            
            total_time = time.time() - intent_start
            print(f"✅ Intent: {result.get('status')} | Mode: {result.get('mode')} | Category: {result.get('category')} | Time: {total_time:.2f}s")
            
            # Add fallback values if missing
            if 'status' not in result:
                result['status'] = 'READY'
            if 'mode' not in result or result['mode'] is None:
                result['mode'] = 'PREDICT_EVENTS_FOR_PERIOD' if any(w in user_question.lower() for w in ['all events', 'events', 'timeline']) else 'ANALYZE_PERSONALITY'
            if 'context_type' not in result:
                result['context_type'] = 'birth'
            if 'category' not in result or result['category'] is None:
                result['category'] = 'general'
            if 'extracted_context' not in result:
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
            if 'divisional_charts' not in result:
                result['divisional_charts'] = self._get_default_divisional_charts(result.get('category', 'general'))
            merge_divisional_charts_with_category_defaults(result)
            apply_chart_focus_guards(result, user_question)
            # Only keep chart_insights when the model returned a valid list of insight objects
            raw_insights = result.get('chart_insights')
            if isinstance(raw_insights, list) and raw_insights:
                valid = [x for x in raw_insights if isinstance(x, dict) and x.get('house_number') and x.get('message')]
                result['chart_insights'] = valid
            else:
                result['chart_insights'] = []
            
            apply_transit_timing_guards(result, user_question, current_year=current_year)

            if result.get('needs_transits') and 'transit_request' not in result:
                result['transit_request'] = {
                    "startYear": current_year,
                    "endYear": current_year + 2,
                    "yearMonthMap": {
                        str(y): ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"] for y in range(current_year, current_year + 3)
                    }
                }

            return result
        except Exception as e:
            total_time = time.time() - intent_start
            print(f"\n❌ INTENT CLASSIFICATION FAILED")
            print(f"Error: {e}")
            print(f"Total time: {total_time:.3f}s")
            
            # Fallback logic
            is_timing_question = any(w in user_question.lower() for w in ['when', 'time', 'date', 'year', 'month', 'will i', 'should i'])
            is_daily_question = any(w in user_question.lower() for w in ['today', 'tomorrow', 'day after tomorrow', 'daily'])

            if is_daily_question:
                result = {
                    "status": "READY", "extracted_context": {}, "mode": "PREDICT_DAILY", "context_type": "birth", "category": "general", "needs_transits": True,
                    "divisional_charts": ["D1", "D9"],
                    "chart_insights": [],
                    "transit_request": {
                        "startYear": current_year, "endYear": current_year,
                        "yearMonthMap": {str(current_year): [current_month]}
                    }
                }
                apply_transit_timing_guards(result, user_question, current_year=current_year)
                apply_chart_focus_guards(result, user_question)
                return result
            elif is_timing_question:
                result = {
                    "status": "READY", "extracted_context": {}, "mode": "PREDICT_EVENT_TIMING", "context_type": "birth", "category": "timing", "needs_transits": True,
                    "divisional_charts": ["D1", "D9"],
                    "chart_insights": [],
                    "transit_request": {
                        "startYear": current_year, "endYear": current_year + 2,
                        "yearMonthMap": {str(y): ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"] for y in range(current_year, current_year + 3)}
                    }
                }
                apply_chart_focus_guards(result, user_question)
                return result
            else:
                result = {
                    "status": "READY", "extracted_context": {}, "mode": "ANALYZE_PERSONALITY", "context_type": "birth", "category": "general", "needs_transits": False,
                    "divisional_charts": ["D1", "D9"],
                    "chart_insights": [],
                }
                apply_chart_focus_guards(result, user_question)
                return result
    
    def _get_default_divisional_charts(self, category: str) -> list:
        """Get default divisional charts based on question category (see _DEFAULT_DIVISIONAL_CHARTS_BY_CATEGORY)."""
        return get_default_divisional_charts_for_category(category)
