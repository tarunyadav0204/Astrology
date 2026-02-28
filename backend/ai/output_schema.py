# Unified Output Schema - Single Source of Truth for Response Formatting
import json
from datetime import datetime

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

Response Format:
**Quick Answer**: Overall compatibility percentage and key insight (2-3 sentences)

**Key Insights**: 3-4 bullet points on strengths and challenges

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
<div class="follow-up-questions">[Generate 3-4 follow-up questions. Each question MUST be on a new line and start with a hyphen (-). DO NOT wrap each question in its own `<div>` tag.]</div>
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
1. <div class="quick-answer-card">**Quick Answer**: [Comprehensive summary]</div>
2. ### Key Insights: [3-4 bullets]
3. ### Analysis Steps: [A bulleted list of 3-4 key astrological calculation steps taken to generate the response, e.g., "- Analyzing Dasha periods", "- Calculating planetary dignities", "- Cross-referencing Navamsa chart".]
4. ### Astrological Analysis: [Use #### for all subsections below]
   - #### The Parashari View: [Provide a detailed analysis explaining the 'why' behind each prediction. Mention specific house lordships, planetary placements, and aspects in D1 and D9. Explicitly discuss the planet's happiness (Friendship) in its current sign using the provided `friendship_analysis` (Panchadha Maitri).]
   - #### The Jaimini View: [Explain the influence of the current Chara Dasha (MD & AD) and the role of relevant Chara Karakas like Atmakaraka or Darakaraka in the context of the query.]
   - #### KP Stellar Perspective: [Provide a technically detailed analysis. Explicitly mention the Cusp Sub-Lord (CSL) of the primary house, its Star Lord, and the specific houses they signify (e.g., 2, 7, 11). Apply the 4-Step Theory for the current Dasha/Antardasha lords to show the flow of results.]
   - #### Nadi Interpretation: [Bulleted list, one for each planetary combination]
   - #### Timing Synthesis: [Synthesize all dasha systems including KP significators]
   - #### Triple Perspective (Sudarshana): [Analyze from Lagna, Moon, Sun]
   - #### Divisional Chart Analysis: [Analyze relevant D-chart]
5. ### Nakshatra Insights: [Analysis + Remedies. This section is MANDATORY if nakshatra data is available.]
6. ### Timing & Guidance: [Actionable roadmap]
7. <div class="final-thoughts-card">**Final Verdict**: [Conclusion based on the HOLISTIC_SYNTHESIS_RULE]</div>

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
- **KP Cusp Confirmation**: [Check the relevant Cusp Sub-Lord (CSL) and its significations for the event]
- **Transit Confirmations**: [Analysis of Jupiter/Saturn/Rahu transits for the key windows]
- **Divisional Confirmation**: [Brief mention of D9/D10/D7 support]

4. ### 💡 Guidance & Preparation
[Actionable advice for the upcoming windows or reflection for past windows]

<div class="final-thoughts-card">**Final Verdict**: [Summary of the most certain period and why]</div>
"""

# Special Template for Mundane Astrology
TEMPLATE_MUNDANE = """
RESPONSE FORMAT - MUNDANE MODE:
<div class="quick-answer-card">**Executive Summary**: [Risk assessment & market outlook]</div>
### Key Risk Factors
[Bullet points]
### Economic & Market Analysis
[Detailed analysis]
### Geopolitical Outlook
[Political stability, conflicts]
<div class="final-thoughts-card">**Strategic Outlook**: [Conclusion]</div>
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

def build_final_prompt(user_question: str, context: dict, history: list, language: str, response_style: str, user_context: dict, premium_analysis: bool, mode: str = 'default') -> str:
    """
    Builds the final, consolidated prompt for the Gemini AI.
    """
    # Get the mode directly from the intent context, it's the source of truth.
    # The 'mode' parameter can be unreliable if reset in the call stack.
    intent_mode = context.get('intent', {}).get('mode', mode)
    
    # Handle None or empty intent_mode
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

    language_instruction = f"LANGUAGE: Respond in {language}.\n\n"
    
    # Use the new centralized schema selection function, using the reliable intent_mode
    response_format_instruction = get_response_schema_for_mode(intent_mode, premium_analysis=premium_analysis)
    
    from chat.system_instruction_config import build_system_instruction
    
    analysis_type = context.get('analysis_type', 'birth')
    
    if analysis_type == 'synastry':
        native_name = context.get('native', {}).get('birth_details', {}).get('name', 'Native')
        partner_name = context.get('partner', {}).get('birth_details', {}).get('name', 'Partner')
        system_instruction = SYNASTRY_SYSTEM_INSTRUCTION.replace('{native_name}', native_name).replace('{partner_name}', partner_name)
    else:
        analysis_type_from_intent = context.get('intent', {}).get('analysis_type')
        intent_category = context.get('intent', {}).get('category', 'general')

        # Override for daily predictions to use the specific daily structure
        if intent_mode.upper() == 'PREDICT_DAILY':
            analysis_type_from_intent = 'DAILY_PREDICTION'
        elif intent_mode.upper() == 'LIFESPAN_EVENT_TIMING':
            analysis_type_from_intent = 'LIFESPAN_EVENT_TIMING'
            
        system_instruction = build_system_instruction(analysis_type=analysis_type_from_intent, intent_category=intent_category)

    prompt_parts = []
    
    import copy
    static_context = copy.deepcopy(context)
    transits = static_context.pop('transit_activations', None)
    chart_json = json.dumps(static_context, indent=2, default=json_serializer, sort_keys=False)
    
    data_label = "MUNDANE ASTROLOGY DATA" if analysis_type == 'mundane' else "BIRTH CHART DATA"
    prompt_parts.append(f"{data_label}:\n{chart_json}")

    if transits:
        transit_json = json.dumps(transits, indent=2, default=json_serializer, sort_keys=False)
        prompt_parts.append(f"PLANETARY TRANSIT DATA (DYNAMIC):\n{transit_json}")

    time_context = f"IMPORTANT CURRENT DATE INFORMATION:\n- Today's Date: {current_date_str}\n- Current Time: {current_time_str}\n- Current Year: {current_date.year}\n\nCRITICAL CHART INFORMATION:\n{ascendant_summary}"
    prompt_parts.append(time_context)
    
    prompt_parts.append(system_instruction)
    prompt_parts.append(f"{language_instruction}{response_format_instruction}{user_context_instruction}{VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION}")
    
    prompt_parts.append(f"{history_text}\nCURRENT QUESTION: {user_question}")
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
