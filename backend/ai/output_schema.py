# Unified Output Schema - Single Source of Truth for Response Formatting
import json
import re
from datetime import datetime


def _question_has_devanagari(text: str) -> bool:
    if not text:
        return False
    for ch in text:
        if "\u0900" <= ch <= "\u097f":
            return True
    return False


def _question_looks_like_roman_hindi(text: str) -> bool:
    """
    Conservative Roman-Hindi cues (whole words). Avoid false positives on normal English
    (e.g. 'main' as in 'main idea').
    """
    if not text or not text.strip():
        return False
    low = text.lower()
    # Strong cues unlikely in ordinary English astrology questions
    patterns = (
        r"\b(mera|meri|mere|merko|mujhe|mujhko|hum|aap|tum|tera|teri|tere)\b",
        r"\b(batao|bata|btao|bataiye)\b",
        r"\b(kya|kyun|kab|kaise|kaisa|kaisi|kahan)\b",
        r"\b(shaadi|shadi|vivah|dasha|dasa|mahadasha|antar)\b",
        r"\b(hai|hain|hoga|hogi|tha|thi|the)\b",
        r"\b(mein|meri)\b",  # 'mein' as Hindi 'in' / I
        r"\b(sab|saari|saara|kuch)\b",
        r"\b(vishleshan|jyotish)\b",
    )
    return any(re.search(p, low) for p in patterns)

# --------------------------------------------------------------------------------------
# I. CENTRALIZED SYSTEM INSTRUCTIONS
# --------------------------------------------------------------------------------------

VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION = """
You are a master Vedic astrologer with deep knowledge of classical texts like Brihat Parashara Hora Shastra, Jaimini Sutras, and Phaladeepika. You provide insightful, accurate astrological guidance based on authentic Vedic principles.
"""

SYNASTRY_SYSTEM_INSTRUCTION = """
You are analyzing COMPATIBILITY between TWO birth charts for partnership/relationship analysis.

🚨 CRITICAL DATA SEPARATION WARNING 🚨
This request contains TWO SEPARATE COMPLETE CHART CONTEXTS:
- context['native']: Contains ALL data for {native_name} ONLY
- context['partner']: Contains ALL data for {partner_name} ONLY

⚠️ ABSOLUTE REQUIREMENT: NEVER mix or confuse data between the two charts.
- When analyzing {native_name}, use ONLY context['native'] data
- When analyzing {partner_name}, use ONLY context['partner'] data
- Each person has their own: planets, houses, dashas, nakshatras, yogas, divisional charts
- DO NOT apply {native_name}'s planetary positions to {partner_name} or vice versa

Context Structure:
- context['native']: First person's complete chart (all data)
- context['partner']: Second person's complete chart (all data)

Synastry Analysis Protocol:
1. **Moon Compatibility**: Compare Moon signs and nakshatras for emotional harmony
2. **Venus-Mars Dynamics**: Check attraction, passion, and relationship chemistry
3. **7th House Analysis**: Marriage potential from BOTH charts (cross-reference)
4. **Kuja Dosha**: Check Mars placement in both charts for cancellation
5. **Dasha Synchronization**: Compare current periods for relationship timing
6. **Ashtakoota Points**: Calculate traditional 36-point matching (Nadi, Gana, Yoni, etc.)
7. **Ascendant Compatibility**: Check Lagna harmony and mutual aspects
8. **Inter-chart Aspects**: Analyze how planets from one chart aspect the other

Response Format (keep **Quick Answer** label for client compatibility):
**Quick Answer**: Full direct answer for the couple—not a teaser. Include overall compatibility assessment (you may give a percentage if appropriate), the main emotional and practical verdict, key strengths, main challenges, and timing notes if relevant, in plain language across several sentences or short paragraphs as needed. Do not defer the core verdict only to **Detailed Analysis**.

**Key Insights**: 3-4 bullet points—scannable highlights; avoid duplicating the entire Quick Answer narrative.

**Detailed Analysis**:
- **Emotional Compatibility (Moon)**: Describe emotional connection quality
- **Physical Attraction (Venus-Mars)**: Analyze chemistry and passion
- **Marriage Potential (7th House)**: Long-term partnership viability
- **Challenges**: Specific areas requiring conscious effort
- **Timing (Dasha Alignment)**: When is the best time for major decisions

**Practical Guidance**: Actionable advice for relationship success

Tone: Balanced, honest, solution-oriented. Highlight both strengths and growth areas.
"""

# --------------------------------------------------------------------------------------
# II. RESPONSE SCHEMA TEMPLATES
# --------------------------------------------------------------------------------------

# Reusable template components to reduce duplication
GLOSSARY_BLOCK_INSTRUCTION = ""  # Glossary is now handled entirely by backend term matcher

FOLLOW_UP_BLOCK_INSTRUCTION = """
<div class="follow-up-questions">
- [Question 1]
- [Question 2]
- [Question 3]
- [Question 4]
</div>
🚨 CRITICAL FORMATTING RULE: You MUST wrap the ENTIRE list of follow-up questions inside a single <div class="follow-up-questions"> block exactly as shown above. Each question MUST start with a hyphen (-). Do not add any other HTML tags inside this block.
"""

# FAQ metadata: LLM must output this exact line at the very end (for categorization + FAQs). Not shown to user.
FAQ_META_INSTRUCTION = """
CRITICAL - FAQ METADATA (do not include this line in the main answer the user sees):
At the very end of your response, after all other content, output exactly one line in this exact format:
FAQ_META: {"category": "<one of: career, marriage, health, education, progeny, wealth, trading, muhurat, karma, general, other>", "canonical_question": "<short phrase summarizing the question intent for FAQ grouping, e.g. Career change or job prospects, Marriage timing>"}
- category: use lowercase, one of the listed values.
- canonical_question: a concise FAQ-style phrase; similar questions should get the same or very similar phrase so they group together.
"""

# Template A: The Deep Dive (Default)
# Used for: ANALYZE_TOPIC_POTENTIAL, ANALYZE_ROOT_CAUSE, PREDICT_PERIOD_OUTLOOK
TEMPLATE_DEEP_DIVE = """
### 🏛️ RESPONSE STRUCTURE (MANDATORY)
Your response MUST follow this exact sequence. The subsection headers under "Astrological Analysis" are already provided with ####, do not add them again.
1. <div class="quick-answer-card">**Quick Answer**: [This block is the user's FULL direct answer—not a short teaser. Mobile and web render this inside a highlighted card; keep the wrapper and the exact label **Quick Answer**: for compatibility.]
   - First sentences: answer the user's exact question (verdict, timing, yes/no, or primary outcome) in plain language.
   - Include every conclusion a typical reader needs from this reading: important date ranges or windows when relevant, main opportunities, main risks or caveats, and mixed or uncertain outcomes if the chart is contradictory.
   - Write as coherent prose (usually 2–5 short paragraphs as needed). Do not artificially keep this short.
   - Do NOT leave essential conclusions only in later sections; do not replace substance with "see Astrological Analysis below." Later sections add technical WHY (houses, dasha, KP, nadi, divisional charts)—not the only place for the answer.
   - Prefer everyday wording; avoid proof-level technical detail here (save jargon and calculations for ### Astrological Analysis).
   - The next section (Key Insights) is for scannable bullets only; Quick Answer = one integrated narrative the user could stop after and still be satisfied.</div>
2. ### Key Insights: [3-4 bullets—distinct from Quick Answer: memorable factors, confirmations, or highlights; not a repeat of the full narrative]
3. ### Astrological Analysis: [Use #### for all subsections below]
   - #### The Parashari View: [Provide a detailed analysis explaining the 'why' behind each prediction. Mention specific house lordships, planetary placements, and aspects in D1 and D9. Explicitly discuss the planet's happiness (Friendship) in its current sign using the provided `friendship_analysis` (Panchadha Maitri).]
   - #### Ashtakavarga (SAV & BAV): [MANDATORY every time. For houses and planets central to the question: cite Sarvashtakavarga (SAV) bindus for the relevant house(s); cite the concerned planet's Bhinnashtakavarga (BAV) in that house/sign where applicable. State whether bindus support or weaken the Parashari conclusions. Apply the BAV override: if BAV < 3 in the focus house, stress obstacles even if SAV is high. When transits are discussed, tie SAV/BAV to those houses.]
   - #### The Jaimini View: [Explain the influence of the current Chara Dasha (MD & AD) and the role of relevant Chara Karakas like Atmakaraka or Darakaraka in the context of the query.]
   - #### KP Stellar Perspective: [Provide a technically detailed analysis. Explicitly mention the Cusp Sub-Lord (CSL) of the primary house, its Star Lord, and the specific houses they signify (e.g., 2, 7, 11). Apply the 4-Step Theory for the current Dasha/Antardasha lords to show the flow of results.]
   - #### Nadi Interpretation: [Bulleted list, one for each planetary combination]
   - #### Timing Synthesis: [Synthesize all dasha systems including KP significators]
   - #### Triple Perspective (Sudarshana): [Analyze from Lagna, Moon, Sun]
   - #### Divisional Chart Analysis: [Analyze relevant D-chart]
4. ### Nakshatra Insights: [Analysis + Remedies. This section is MANDATORY if nakshatra data is available.]
5. ### Timing & Guidance: [Actionable roadmap]
6. <div class="final-thoughts-card">**Final Verdict**: [Conclusion based on the HOLISTIC_SYNTHESIS_RULE]</div>

### 🚨 FORMATTING RULES
- [HEADERS]: Use ### for main headers, #### for subsections.
"""

# Template B: Event Prediction Timeline
# Used for: PREDICT_EVENTS_FOR_PERIOD
TEMPLATE_EVENT_PREDICTION = """
### Key Themes for [Period]
[Bullet points on main focus areas]

### Timeline of Potential Events
[A chronologically sorted list of events. Each item contains:]
- 🗓️ **[Date or Date Range]**
- **Potential Event:** [Description of the event]
- **Astrological Insight:** [The "why" behind the prediction]
- **Life Area:** [Career, Relationship, Health, etc.]

### Guidance for the Period
[Actionable advice on how to navigate the predicted events]
"""

# Template C: Daily Summary
# Used for: PREDICT_DAILY_* modes
TEMPLATE_DAILY_SUMMARY = """
<div class="quick-answer-card">**Daily Outlook**: [Brief summary]</div>

### Key Opportunities
[Bulleted list of positive influences and how to use them]

### Potential Challenges
[Bulleted list of obstacles and how to navigate them]

### Guidance for the Day
[A final piece of actionable advice]
"""

# Template D: Lifespan Timeline
# Used for: LIFESPAN_EVENT_TIMING
TEMPLATE_LIFESPAN_TIMELINE = """
### 🕰️ LIFESPAN EVENT TIMELINE (MANDATORY)
Your response must be a chronological analysis of the specific event requested across the native's lifespan.

1. <div class="quick-answer-card">**Executive Summary**: [Direct answer to the "When" question with the most likely window/year]</div>

2. ### 🗓️ Chronological Potential Windows
[List 3-5 specific time windows in chronological order]
- **Window [1/2/3]**: [Year/Period]
  - **Astrological Strength**: [High/Medium/Low]
  - **Key Triggers**: [Briefly mention the Dasha and Transit alignment]
  - **Manifestation**: [How the event is likely to occur in this period]

3. ### 🔍 Technical Deep Dive
- **Primary Dasha Promise**: [Analysis of the Mahadasha/Antardasha lords responsible]
- **Ashtakavarga (SAV & BAV)**: [MANDATORY: Cite SAV for relevant houses and BAV for key planets for the windows discussed; apply BAV override where BAV < 3]
- **KP Cusp Confirmation**: [Check the relevant Cusp Sub-Lord (CSL) and its significations for the event]
- **Transit Confirmations**: [Analysis of Jupiter/Saturn/Rahu transits for the key windows]
- **Divisional Confirmation**: [Brief mention of D9/D10/D7 support]

4. ### 💡 Guidance & Preparation
[Actionable advice for the upcoming windows or reflection for past windows]

<div class="final-thoughts-card">**Final Verdict**: [Summary of the most certain period and why]</div>
"""

# Special Template for Mundane Astrology
TEMPLATE_MUNDANE = """
### 🏛️ MUNDANE ELITE ANALYSIS (MANDATORY)
Your response MUST follow this exact sequence and adhere to the strict technical rules below:

1. <div class="quick-answer-card">**Executive Prediction & Probability**: [Direct verdict with a specific probability percentage (e.g. 80%). No ambiguity.]</div>

2. ### Key Astrological Triggers & Macro Trends: [Cite 3-4 high-impact triggers from the event chart. You MUST also explicitly state the Nav Nayak (King of the Year) and the impact of the Aries Ingress from the `ingress_data`.]

3. ### Panchang & Event Synergy:
   - [Analyze the `Tithi`, `Nakshatra`, and `Yoga` from `event_panchang`. Explain how this specific combination influences the "auspiciousness" or "volatility" of the event start.]

4. ### Battle of the Charts (Side-by-Side Analysis):
   - #### Entity Dashas: [Detail the exact Vimshottari Mahadasha/Antardasha for EACH nation involved. Cite them by name. If data is unavailable for an entity, state it clearly.]
   - #### Locational Analysis: [Contrast the Lagna/House placements for the capitals of each entity from `locational_analysis`.]

5. ### Regional & Geographic Citations:
   - #### Strategic Impacts: [You MUST cite specific provinces or regions by name from the `geographic_impacts` data (e.g. "Gilan", "Kurdistan"). Generic regional terms are forbidden.]

6. ### Market & Commodity Precision:
   - #### Vedha Analysis: [Detail the exact triggers for Oil, Silver, or Grains from `commodity_impacts`. Specify the triggering planet and if it is a 'direct' or 'vedha' impact.]

7. ### Critical Timing & Tipping Points: [Exact dates/hours of peak volatility.]

8. <div class="final-thoughts-card">**Strategic Verdict**: [Final authoritative conclusion and warning.]</div>
"""

# Developer-focused, high-density event log
TEMPLATE_DEV_EVENT_LOG = """
### 🏛️ DEEP DIVE EVENT LOG (MANDATORY)
Your response MUST be a detailed log of all possible astrological events for the requested period.

- **Exhaustive List**: Generate an exhaustive list of all possible events, aiming for 40-50+ entries. Include major, minor, and subtle events.
- **Technical Details**: For each event, provide the astrological reasoning, including dasha periods, transiting planets, aspects, and house significations.
- **Raw Data Focus**: Prioritize raw data and technical analysis over user-friendly summaries. Omit "Quick Answer" and "Final Thoughts" sections.
- **Chronological Order**: List events in chronological order.

### RESPONSE STRUCTURE:
1. ### Full Event Log:
   - **Event 1**: [Date Range] - [Event Title]
     - **Astrological Reasoning**: [Detailed explanation of the planetary configurations causing the event.]
     - **Potential Manifestations**: [List of possible ways the event could manifest in the person's life.]
     - **Confidence Score**: [A score from 1-10 indicating the likelihood of the event.]
   - **Event 2**: [Date Range] - [Event Title]
     - ...
"""


# --------------------------------------------------------------------------------------
# III. SCHEMA SELECTION LOGIC
# --------------------------------------------------------------------------------------

# Maps analysis 'modes' to their corresponding response schema templates.
# This makes the system extensible. Add a new mode and template here.
SCHEMA_MAPPING = {
    'ANALYZE_TOPIC_POTENTIAL': TEMPLATE_DEEP_DIVE,
    'ANALYZE_ROOT_CAUSE': TEMPLATE_DEEP_DIVE,
    'PREDICT_PERIOD_OUTLOOK': TEMPLATE_DEEP_DIVE,
    'PREDICT_EVENTS_FOR_PERIOD': TEMPLATE_DEV_EVENT_LOG,
    'PREDICT_DAILY': TEMPLATE_DEEP_DIVE,
    'MUNDANE': TEMPLATE_MUNDANE,
    'DEV_EVENT_LOG': TEMPLATE_DEV_EVENT_LOG,
    'LIFESPAN_EVENT_TIMING': TEMPLATE_LIFESPAN_TIMELINE,
    'DEFAULT': TEMPLATE_DEEP_DIVE,
}

def get_response_schema_for_mode(mode: str, premium_analysis: bool = False) -> str:
    """
    Selects the appropriate response schema based on the analysis mode.
    This function now centralizes the inclusion of common response blocks.
    """
    # Handle None or empty mode
    if not mode:
        mode = 'DEFAULT'
    
    # Select the base schema using the mapping, falling back to DEFAULT
    base_schema = SCHEMA_MAPPING.get(mode.upper(), SCHEMA_MAPPING['DEFAULT'])
    
    # Programmatically add common blocks to all schemas except special cases
    if mode.upper() not in ['DEV_EVENT_LOG', 'LIFESPAN_EVENT_TIMING']:
        # Ensure there's a newline before appending
        schema_with_common_blocks = base_schema.strip() + "\n"
        # Only attach follow-up questions block; glossary is injected by backend
        schema_with_common_blocks += FOLLOW_UP_BLOCK_INSTRUCTION
    else:
        # Dev log and Lifespan: keep base schema as-is
        schema_with_common_blocks = base_schema.strip()

    # Optional: Append instructions for premium features
    image_instructions = ""
    if premium_analysis:
        image_instructions = """
9. SUMMARY_IMAGE_START
   [A multi-panel visual narrative prompt for an image generation model.]
   SUMMARY_IMAGE_END
"""
        # This is appended carefully to avoid breaking the structure of simpler templates
        if mode.upper() in ['ANALYZE_TOPIC_POTENTIAL', 'ANALYZE_ROOT_CAUSE', 'PREDICT_PERIOD_OUTLOOK', 'DEFAULT', 'PREDICT_DAILY', 'LIFESPAN_EVENT_TIMING']:
             return schema_with_common_blocks + "\n" + image_instructions

    return schema_with_common_blocks


# --------------------------------------------------------------------------------------
# IV. FINAL PROMPT CONSTRUCTION
# --------------------------------------------------------------------------------------

def _summarize_natal_for_mundane_prompt(chart: dict) -> dict:
    """Strip heavy chart blobs so Gemini sees dasha/geo context without token overflow."""
    if not chart or not isinstance(chart, dict):
        return chart
    planets = chart.get("planets") or {}
    slim_p = {}
    for name in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
    ):
        if name not in planets:
            continue
        p = planets[name]
        if not isinstance(p, dict):
            continue
        slim_p[name] = {
            "longitude": p.get("longitude"),
            "house": p.get("house"),
            "sign_name": p.get("sign_name"),
            "retrograde": p.get("retrograde"),
        }
        nk = p.get("nakshatra")
        if isinstance(nk, dict) and nk.get("name"):
            slim_p[name]["nakshatra"] = nk.get("name")
    out = {
        "ascendant": chart.get("ascendant"),
        "ascendant_sign": chart.get("ascendant_sign"),
        "planets": slim_p,
    }
    return out


def _slim_mundane_context_for_llm(ctx: dict) -> dict:
    """Reduce token load for mundane prompts; authoritative summary carries dasha truth."""
    ev = ctx.get("event_chart")
    if isinstance(ev, dict):
        ctx["event_chart"] = _summarize_natal_for_mundane_prompt(ev)
    ec = ctx.get("entity_charts")
    if isinstance(ec, dict):
        for _ent, data in list(ec.items()):
            if not isinstance(data, dict) or not data.get("available"):
                continue
            nc = data.get("natal_chart")
            if isinstance(nc, dict):
                data["natal_chart"] = _summarize_natal_for_mundane_prompt(nc)
    la = ctx.get("locational_analysis")
    if isinstance(la, dict):
        for _ent, data in list(la.items()):
            if not isinstance(data, dict) or not data.get("available"):
                continue
            lg = data.get("lagna_chart")
            if isinstance(lg, dict):
                data["lagna_chart"] = _summarize_natal_for_mundane_prompt(lg)
    return ctx


def build_final_prompt(user_question: str, context: dict, history: list, language: str, response_style: str, user_context: dict, premium_analysis: bool, mode: str = 'default') -> str:
    """
    Builds the final, consolidated prompt for the Gemini AI.
    """
    analysis_type = context.get('analysis_type', 'birth')
    intent_block = context.get('intent', {}) or {}
    intent_mode = intent_block.get('mode', mode)
    if analysis_type == 'mundane':
        intent_mode = 'MUNDANE'
    if intent_block.get('lab_mode'):
        intent_mode = 'LAB_EDUCATION'
    if not intent_mode:
        intent_mode = mode or 'DEFAULT'

    history_text = ""
    if history:
        history_text = "\n\nCONVERSATION HISTORY (FOR CONTEXT ONLY):\n"
        history_text += "⚠️ RELEVANCE RULE: ONLY refer to this history if the current question is a follow-up or directly linked to these past messages. If the user has shifted to a new topic, IGNORE the specifics of the history below.\n\n"
        recent_messages = history[-3:] if len(history) >= 3 else history
        for msg in recent_messages:
            question = msg.get('question', '')[:500]
            response = msg.get('response', '')[:500]
            history_text += f"User: {question}\nAssistant: {response}\n\n"

    current_date = datetime.now()
    current_date_str = current_date.strftime("%B %d, %Y")
    current_time_str = current_date.strftime("%H:%M UTC")

    ascendant_info = context.get('ascendant_info', {})
    ascendant_summary = f"ASCENDANT: {ascendant_info.get('sign_name', 'Unknown')} at {ascendant_info.get('exact_degree_in_sign', 0):.2f}°"

    user_context_instruction = ""
    if user_context:
        user_name = user_context.get('user_name', 'User')
        native_name = context.get('birth_details', {}).get('name', 'the native')
        relationship = user_context.get('user_relationship', 'self')
        
        if relationship == 'self' or (user_name and native_name and user_name.lower() == native_name.lower()):
            user_context_instruction = f"USER CONTEXT - SELF CONSULTATION:\nThe person asking questions is {native_name} themselves. Use direct personal language: 'Your chart shows...', 'You have...'"
        else:
            user_context_instruction = f"🚨 CRITICAL USER CONTEXT - THIRD PARTY CONSULTATION 🚨\nThe person asking is {user_name} about {native_name}'s chart. You MUST use '{native_name}' or 'they/their' in your response. NEVER use 'you/your'."

    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    _lang = str(language or "english").strip() or "english"
    _lang_lower = _lang.lower()

    # When the client requests English, default to English unless the *question* is clearly Hindi/Hinglish.
    if _lang_lower == "english":
        language_instruction = f"""OUTPUT LANGUAGE (read CURRENT QUESTION at the end of this prompt):

DEFAULT — ENGLISH: The app language is **english**. Write the **entire** answer in **clear English** (prose and section headers), including when birth data or chart JSON contains Indian place names or Hindi labels. Indian names or locations in the context do **not** mean you should switch the answer to Hindi.

SWITCH TO HINDI (Devanagari) **only if** CURRENT QUESTION is clearly Hindi or Roman-Hindi:
- The question contains **Devanagari** script, **or**
- The question contains **obvious conversational Roman-Hindi** (e.g. mera/meri, batao/btao, kya/kab in a Hindi-style question — not normal English words like "what", "when", "career").

If the question is ordinary English, you **must not** answer primarily in Hindi. Do not use Devanagari for the main answer in that case.

"""
        if (
            not _question_has_devanagari(user_question)
            and not _question_looks_like_roman_hindi(user_question)
        ):
            language_instruction += (
                "\nAUTO-CHECK: CURRENT QUESTION has no Devanagari and no Roman-Hindi cues → "
                "**English answer required**.\n"
            )
    else:
        language_instruction = f"""OUTPUT LANGUAGE (you will see CURRENT QUESTION at the end of this prompt—infer language from that text and app language "{_lang}"):

1) If CURRENT QUESTION is Hindi OR Roman Hindi (Hinglish), write the ENTIRE substantive answer in Hindi using Devanagari script (हिंदी) when appropriate for {_lang}. Jyotish terms may use natural Hindi or common transliteration.

   Signals for Hinglish: words like mera/meri/mere, batao/btao, sab/sba kuch, dasha/dasa, shaadi/shadi, kab, kya, kaisa/kaisi, vishleshan, hai/hain, or any Devanagari.

2) Otherwise: use app language "{_lang}" for the answer.

"""
    
    elaborate_instruction = """
CRITICAL - RESPONSE LENGTH & DEPTH (NON-NEGOTIABLE):
Your full response MUST be comprehensive. Short or summary-style answers are FORBIDDEN.
- For Birth Chart queries: Aim for 12,000 characters. Expand every section with planetary reasoning, classical references, and technical detail.
- For Mundane/Event queries: Aim for 3,000-5,000 characters. Focus on precision, house comparison (1st vs 7th), dasha synchronization, and critical timing.
- Prioritize depth and clarity. Output sufficient detail to justify the prediction.
"""
    
    # Use the new centralized schema selection function, using the reliable intent_mode
    response_format_instruction = get_response_schema_for_mode(intent_mode, premium_analysis=premium_analysis)
    
    from chat.system_instruction_config import build_system_instruction
    from calculators.mundane.mundane_context_builder import MundaneContextBuilder

    if analysis_type == 'synastry':
        native_name = context.get('native', {}).get('birth_details', {}).get('name', 'Native')
        partner_name = context.get('partner', {}).get('birth_details', {}).get('name', 'Partner')
        system_instruction = SYNASTRY_SYSTEM_INSTRUCTION.replace('{native_name}', native_name).replace('{partner_name}', partner_name)
    elif analysis_type == 'mundane':
        system_instruction = MundaneContextBuilder.MUNDANE_SYSTEM_INSTRUCTION
    else:
        analysis_type_from_intent = context.get('intent', {}).get('analysis_type')
        intent_category = context.get('intent', {}).get('category', 'general')

        # Override for daily predictions to use the specific daily structure
        if intent_mode.upper() == 'PREDICT_DAILY':
            analysis_type_from_intent = 'DAILY_PREDICTION'
        elif intent_mode.upper() == 'LIFESPAN_EVENT_TIMING':
            analysis_type_from_intent = 'LIFESPAN_EVENT_TIMING'
            
        system_instruction = build_system_instruction(analysis_type=analysis_type_from_intent, intent_category=intent_category, mode=intent_mode)

    prompt_parts = []
    
    import copy
    static_context = copy.deepcopy(context)
    transits = static_context.pop('transit_activations', None)

    mundane_auth = None
    if analysis_type == "mundane":
        mundane_auth = static_context.pop("mundane_authoritative_summary", None)
        static_context = _slim_mundane_context_for_llm(static_context)

    chart_json = json.dumps(static_context, indent=2, default=json_serializer, sort_keys=False)
    
    data_label = "MUNDANE ASTROLOGY DATA" if analysis_type == 'mundane' else "BIRTH CHART DATA"
    if analysis_type == "mundane" and mundane_auth:
        prompt_parts.append(
            "⚠️ MUNDANE AUTHORITATIVE SUMMARY (READ FIRST — if national_dasha_loaded is true for an entity, "
            "national Vimshottari data exists; do not claim the repository is missing it):\n"
            + json.dumps(mundane_auth, indent=2, default=json_serializer, sort_keys=False)
        )
    prompt_parts.append(f"{data_label}:\n{chart_json}")

    if transits:
        transit_json = json.dumps(transits, indent=2, default=json_serializer, sort_keys=False)
        prompt_parts.append(f"PLANETARY TRANSIT DATA (DYNAMIC):\n{transit_json}")

    time_context = f"IMPORTANT CURRENT DATE INFORMATION:\n- Today's Date: {current_date_str}\n- Current Time: {current_time_str}\n- Current Year: {current_date.year}\n\nCRITICAL CHART INFORMATION:\n{ascendant_summary}"
    prompt_parts.append(time_context)
    
    prompt_parts.append(system_instruction)
    prompt_parts.append(f"{language_instruction}{elaborate_instruction}{response_format_instruction}{user_context_instruction}{VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION}")
    
    prompt_parts.append(f"{history_text}\nCURRENT QUESTION: {user_question}")
    if _lang_lower == "english":
        prompt_parts.append(
            "FINAL CHECK BEFORE YOU WRITE: Re-read CURRENT QUESTION and OUTPUT LANGUAGE above. "
            "If CURRENT QUESTION is ordinary English (no Devanagari, not clear Roman-Hindi), "
            "the full answer must be in English—do not switch to Hindi because of chart labels or names. "
            "Only if CURRENT QUESTION is clearly Hindi or Roman-Hindi (per OUTPUT LANGUAGE), "
            "write the substantive answer in Devanagari Hindi; you may use Hindi section titles then."
        )
    else:
        prompt_parts.append(
            "FINAL CHECK BEFORE YOU WRITE: Re-read CURRENT QUESTION. If it is Hindi or Hinglish, "
            "your answer must be in Devanagari Hindi—not English—regardless of any English examples "
            "or English section headers elsewhere in this prompt; you may use Hindi section titles."
        )
    prompt_parts.append(FAQ_META_INSTRUCTION.strip())
    
    return "\n\n".join(prompt_parts)

# Legacy compatibility - maps old RESPONSE_SKELETON to new schema
RESPONSE_SKELETON = """
[QUICK ANSWER CARD]: Comprehensive summary answering user's specific question decisively. Synthesize Parashari lords, Jaimini status, and Dasha timing into single verdict.
### Key Insights: 3 specific wins and 1 specific challenge.
### Astrological Analysis:
#### [Protocol] View: (Parashari, Jaimini, or Nadi results). For Parashari "Provide a Technically Exhaustive analysis. For the Parashari View, go into deep detail for every dasha level. Do not summarize; explain the 'why' behind every prediction using house significations."
#### Timing Synthesis: (Synthesize Vimshottari MD/AD/PD + Chara Sign + Yogini Lord)
#### Triple Perspective: Compare house strength from Lagna, Moon, and Sun.
### Nakshatra Insights: Star Shakti + Biological (Vriksha) remedy.
### Timing & Guidance: Specific monthly roadmap for next 6-12 months.
[FINAL THOUGHTS CARD]: Outlook anchored in classical text authority (cite BPHS, Saravali, or Phaladeepika).
"""
