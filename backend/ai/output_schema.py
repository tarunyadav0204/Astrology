from __future__ import annotations

# Unified Output Schema - Single Source of Truth for Response Formatting
import json
from datetime import datetime


def resolve_output_language_policy(language: str, user_question: str) -> dict:
    app_language = str(language or "english").strip() or "english"
    app_language_lower = app_language.lower()
    return {
        "kind": "llm_current_question",
        "app_language": app_language,
        "app_language_lower": app_language_lower,
        "question_is_hindi": None,
    }


def build_output_language_blocks(language: str, user_question: str) -> tuple[dict, str, str]:
    policy = resolve_output_language_policy(language, user_question)
    app_language = policy["app_language"]
    language_instruction = f"""OUTPUT LANGUAGE — LLM MUST INFER FROM CURRENT QUESTION:

The app-selected language is **{app_language}**, but for chat answers it is only UI context. Do **not** blindly follow it.

You must infer the language of the **CURRENT QUESTION** yourself and write the entire user-visible answer in that same language and natural script.

NON-NEGOTIABLE EXAMPLES:
- If CURRENT QUESTION is English, answer in English.
- If CURRENT QUESTION is Hindi in Devanagari, answer in Hindi using Devanagari.
- If CURRENT QUESTION is Hinglish / Roman Hindi, answer in Hindi using Devanagari, not Roman Hindi.
- If CURRENT QUESTION is Tamil, answer in Tamil.
- If CURRENT QUESTION is Telugu, Gujarati, Marathi, Bengali, Kannada, Malayalam, French, German, Russian, Chinese, Arabic, or any other language, answer in that same language and script.

CRITICAL:
- Decide from the CURRENT QUESTION, not from app-selected language, previous messages, chart labels, names, glossary terms, or stored preferences.
- Do not translate an English question into Hindi.
- Do not answer a Tamil/Telugu/etc. question in Hindi.
- Only if the CURRENT QUESTION is too short or language-ambiguous, use the app-selected language "{app_language}" as a fallback.
"""
    final_check = (
        "FINAL CHECK BEFORE YOU WRITE: Infer the language of CURRENT QUESTION yourself. "
        "English question -> English. Hinglish/Roman Hindi -> Devanagari Hindi. "
        "Tamil/Telugu/etc. -> same language and script. App language is fallback only for ambiguous questions."
    )
    return policy, language_instruction, final_check


def build_delivery_format_instruction(intent_block: dict | None) -> str:
    if not isinstance(intent_block, dict):
        return ""
    delivery_channel = str(intent_block.get("delivery_channel") or "").strip().lower()
    render_target = str(intent_block.get("render_target") or "").strip().lower()
    plain_text_output = bool(intent_block.get("plain_text_output"))
    if delivery_channel != "whatsapp" and render_target != "plain_text" and not plain_text_output:
        return ""
    return """
DELIVERY FORMAT — WHATSAPP PLAIN TEXT:
- The final answer will be sent as a WhatsApp text message, not rendered by the app UI.
- Do NOT ask option-based clarification questions like "Type A/B/C" for broad but understandable questions. Answer the broad topic directly. Ask a clarification only if answering would be impossible without it.
- Do NOT output HTML tags of any kind: no `<span>`, no `<div>`, no `<br>`, no classes, and no follow-up question HTML block.
- Do NOT use markdown tables or UI-only cards. Use short paragraphs and simple "- " bullets.
- If emphasis is needed, use WhatsApp-friendly `*bold*` sparingly. Keep the answer readable as plain text.
- Any follow-up suggestions, if present, must be plain text bullets only.
"""


def build_multi_question_focus_instruction(language: str = "english") -> str:
    """
    Tells the answer model: if CURRENT QUESTION still bundles several distinct asks,
    pick one, answer it deeply, and state scope at the very top of the user-visible reply.
    (OUTPUT LANGUAGE rules elsewhere still apply — the notice must match the answer language.)
    """
    _ = (language or "english").strip()
    return """
📌 MULTIPLE QUESTIONS IN "CURRENT QUESTION" (APPLY ONLY WHEN RELEVANT):
If the user's CURRENT QUESTION (at the end of this prompt) clearly contains **two or more distinct, unrelated questions**—for example several question marks, numbered asks, "I have two questions", or clearly separate unrelated topics in one message—do **not** try to answer everything at equal depth in a single reply.

Do NOT treat one coherent question with related facets as multiple questions. Examples that are ONE question:
- career + job + salary + promotion
- marriage + spouse + husband/wife + relationship
- health + stress + work pressure
- timing + description of the same event/person

Instead you MUST:
1) **Choose one focus question** for this reading: the most urgent, chart-central, or emotionally weighty ask (use dasha timing, house emphasis, or what the chart best supports).
2) **Answer only that question** with full depth and the usual response structure. Do **not** give parallel full analyses for every other bundled question.
3) **At the very top of your reply**, before any section headers (before "Quick Answer", markdown titles, or the first substantive paragraph), add a **short scope notice** in the **same language as the rest of your answer** (per OUTPUT LANGUAGE rules):
   - State clearly that this reading is focused on that one question; briefly restate it in your own words (one short clause).
   - Add one warm line inviting them to send remaining questions **one at a time** in follow-up messages so each can get proper depth.
   - Tone: helpful and respectful, never scolding.

If CURRENT QUESTION is genuinely **one** integrated question (even if long), **do not** add this disclaimer—answer normally.

"""


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
🚨 CRITICAL FORMATTING RULE: You MUST wrap the ENTIRE list of follow-up questions inside a single <div class="follow-up-questions"> block exactly as shown above (literal HTML: double-quote characters only—never a backslash before a quote). Each question MUST start with a hyphen (-). Do not add any other HTML tags inside this block.
"""

# FAQ metadata: LLM must output this exact line at the very end (for categorization + FAQs). Not shown to user.
FAQ_META_INSTRUCTION = """
CRITICAL - FAQ METADATA (do not include this line in the main answer the user sees):
At the very end of your response, after all other content, output exactly one line in this exact format:
FAQ_META: {"category": "<one of: career, marriage, health, education, progeny, wealth, trading, muhurat, karma, general, other>", "canonical_question": "<short phrase summarizing the question intent for FAQ grouping, e.g. Career change or job prospects, Marriage timing>"}
- category: use lowercase, one of the listed values.
- canonical_question: a concise FAQ-style phrase; similar questions should get the same or very similar phrase so they group together.
"""

NEXT_ACTION_META_INSTRUCTION = """
CRITICAL - NEXT ACTION METADATA (do not include this line in the main answer the user sees):
At the very end of your response, before FAQ_META, output exactly one line in this exact format:
NEXT_ACTION_META: {"type":"<remedy|diagnosis|timing|clarification|comparison|chart_explanation|none>","title":"<short label>","reason":"<short reason>","confidence":"<high|medium|low>","follow_up_questions":["<up to 3 short user-facing options>"],"source":"merge"}
- If no follow-up is needed, set type to "none" and follow_up_questions to an empty array.
- If the best immediate next step is a practical remedy reading, you MUST use type="remedy". This is required even when the main answer must NOT contain inline remedies—the card opens remedy mode.
- For type="remedy", write ALL card copy in the SAME language/script as the user's current question:
  * title = FOMO headline (4–10 words, specific to this chart pressure, gentle urgency)
  * reason = one FOMO subline (why opening remedies now helps in this dasha/window)
  * follow_up_questions[0] = short button label only (e.g. "Show my remedies" / "उपाय देखें")
  The UI shows ONLY title, reason, and follow_up_questions[0] on the remedy card — no generic English boilerplate.
- For non-remedy types, follow_up_questions can be normal follow-up prompts.
- If REMEDY FOLLOW-UP MODE is active (user already opened the Remedies CTA), set type to "none" — remedies belong in the answer body, not another card.
- Keep the line valid JSON and short.
"""


def _single_native_format_guard(analysis_type: str) -> str:
    if analysis_type in ("synastry", "relational"):
        return ""
    return """
FORMAT GUARD FOR SINGLE-NATIVE READINGS:
- This is NOT a two-person synastry/relational reading unless the data explicitly contains two full charts.
- Do NOT use the relational two-person answer template or its fixed section labels such as:
  "Core Nature", "Behavioral Texture", "Interaction Pattern", or a spouse-vs-partner comparison layout.
- Do NOT speak as if you are comparing native and partner charts unless two-chart data is actually present.
- If the topic is marriage/relationship but the input is still one native chart, answer it as a single-chart relationship reading, not a dual-chart compatibility reading.
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
4. ### Nakshatra Insights: [Nakshatra analysis only—themes, shakti, deity context. Do NOT add remedies, upayas, mantras, gemstones, or charity lists here. This section is MANDATORY if nakshatra data is available.]
5. ### Timing & Guidance: [Timing roadmap only: active dasha/transit phases, when pressure eases or peaks, and astrological vulnerability themes. Do NOT write a wellness/remedy playbook—no diet, exercise, yoga, pranayama, dosha prescriptions, or numbered "do this" lifestyle lists. The app offers a separate Remedies CTA for practical steps.]
6. <div class="final-thoughts-card">**Final Verdict**: [Conclusion based on the HOLISTIC_SYNTHESIS_RULE. Do not end with a lifestyle remedy checklist—keep it astrological.]</div>

### 🚨 FORMATTING RULES
- [HEADERS]: Use ### for main headers, #### for subsections.
- [NO INLINE REMEDIES]: Do not include remedy layers, upayas, gemstones, mantras, charity/seva lists, OR practical wellness plans (diet/exercise/yoga/pranayama/dosha routines) in this normal reading. Timing & Guidance = phases and chart themes only.
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

TEMPLATE_REMEDIAL_GUIDANCE = """
### Guidance and Remedies
[A practical remedy reading based on the strongest live chart pressure.]

### What needs attention now
[State the most pressing issue, the active planet(s), and why this area needs care.]

### Remedy layers
- **Core planetary remedy**: the main planet-focused remedy
- **Gemstone / ratna**: only if suitable for the strongest planet; keep it optional and specific
- **Biological / vriksha**: tree, leaf, wood, body-routine, or other physical-support remedy if present
- **Nakshatra remedy**: shakti, deity, vriksha, mantra, and the most direct star-specific action if present
- **Behavioral support**: routine, speech, discipline, or relationship adjustments
- **Charity / seva**: service-oriented or giving-based support
- **Mantra / sound**: the relevant mantra or sound practice
- **Special blockage layers**: Mudakku / Gandanta / Mrityu Bhaga only if present

### What to avoid
[Brief caution on overdoing remedies, gemstone suitability, or fear-based language.]
"""

# Template C: Daily Summary
# Used for: PREDICT_DAILY_* modes
TEMPLATE_DAILY_SUMMARY = """
### Astrological Blueprint for [Requested Date]

<div class="quick-answer-card">**Daily Outlook**: [Answer exactly what is likely for the requested day in 2-4 practical paragraphs. Name the requested date explicitly. Keep natal/dasha factors as background only.]</div>

### Main Day Triggers
[3-5 bullets focused on the transiting Moon, nakshatra/tara, tithi/karana/yoga if available, and fast transits. Mention slow planets only as background.]

### What To Use
[Bulleted list of concrete opportunities and how to use them during this day.]

### What To Watch
[Bulleted list of practical cautions for this day. Avoid life-wide claims.]

### Timing Through The Day
[Morning / afternoon / evening guidance. If exact time data is not available, keep it approximate and say so.]

### Guidance for the Day
[A final piece of actionable advice]
"""

# Template D: Lifespan Timeline
# Used for: LIFESPAN_EVENT_TIMING
TEMPLATE_LIFESPAN_TIMELINE = """
### 🕰️ LIFESPAN EVENT TIMELINE (MANDATORY)
Your response must be a chronological analysis of the specific event requested across the native's lifespan.

1. <div class="quick-answer-card">**Executive Summary**: [Direct answer naming the strongest window AND, when justified, the best month or 2-3 month execution band. For **first-job/job-seeking**: separate **Activation** / **Offer** / **Joining**. For **promotion/raise**: separate **Visibility** / **Formalization** / **Settle** — never use Activation/Offer/Joining. Never collapse all three into one PD start date.]</div>

2. **Event arc** (career REQUIRED; other events when phases apply): One short chronological line in time order. Job-seeking: `Activation → Offer → Joining`. Promotion: `Visibility → Formalization → Settle`.

3. ### 🗓️ Ranked Potential Windows
[List 3–5 windows ranked by strength (Window 1 = strongest claim), NOT by calendar order. Ranking MUST follow scored clusters / event_timing_verdict when present; otherwise cite dasha+transit+divisional confluence — do not invent numeric scores. Do not silently re-rank Window 1 on follow-ups.]
- **Window [1/2/3]**: [Year/Period] — tag **Same arc** (phase of the primary story) or **Alternate path** (backup / later / different outcome path)
  - **Ripe Window**: [Broader year/range when the event is ripe — not natal chart promise / not KP CSL]
  - **Execution Window**: [Best month or narrow month-band]
  - **Career/Promotion layer**: Job-seeking: exactly one of Activation | Offer | Joining. Promotion: exactly one of Visibility | Formalization | Settle. Never combine two layers on one window.
  - **Astrological Strength**: [High/Medium/Low]
  - **Key Triggers**: [Brief dasha + one transit/divisional hook]
  - **What Helps**: [Why this window is strong]
  - **What Weakens It**: [Why it is not ranked higher / obstruction]
  - **Manifestation**: [How the event is likely to occur in this period]
  - 🚨 PD / micro-dasha start = environment shift (Activation), not an offer/joining SLA unless the ranked execution window supports that layer.

4. ### 🔍 Technical Deep Dive (KEEP SLIM — 3 beats only)
Do NOT dump a full school-by-school report. Cap this section to:
- **Why Window 1**: Primary dasha stack + the 1–2 strongest confirming factors (pick from transit / divisional / KP CSL / SAV-BAV — only what actually decides the rank)
- **Main risk**: The single biggest weakeners for Window 1 or the next-best alternate
- **Optional one-liner**: Extra school detail only if the user asked for technical depth or remedies
Do not add long KP Sign→Star→Sub stacks, Kota essays, or remedy lists unless requested. Candidate ranking must explain Window 1 vs 2 vs 3 in plain confluence language (or scores when present).

5. ### 💡 Guidance & Preparation
[2–4 short actionable points for the upcoming windows — not a second technical essay]

<div class="final-thoughts-card">**Final Verdict**: [Confidence High/Medium/Low for Window 1 + what would demote it. Do not restate the full executive summary. No guarantee / copper-bottomed / mathematical-certainty language.]</div>
"""

# Template D2: Restricted Life Termination Research
# Used for: LIFE_TERMINATION_RESEARCH
TEMPLATE_LIFE_TERMINATION_RESEARCH = """
### 🕰️ LIFE TERMINATION RESEARCH ANALYSIS (MANDATORY)
This is a restricted classical longevity research answer. Keep it evidence-first, probabilistic, and sober.

1. <div class="quick-answer-card">**Executive Summary**: [Directly state the baseline longevity class, the strongest candidate window(s), and whether the evidence is high/medium/low. Do NOT state a guaranteed death date.]</div>

2. ### Method Boundary
[One short paragraph: this is classical astrological research, not medical/legal advice; it identifies sensitive windows and life-force stress patterns, not certainty.]

3. ### Baseline Longevity Promise
- **Ayu Class**: [Alpayu/Madhyayu/Deerghayu/Purnayu or mixed classification, with reasoning]
- **Vitality Foundation**: [Lagna, Lagna lord, Moon, Saturn/Ayushkaraka]
- **Longevity Houses**: [3rd and 8th houses/lords]
- **Protection Factors**: [Benefic protections, strong 6th/12th recovery support, D9 resilience, if present]
- **Vulnerability Factors**: [Weak Lagna/8th/Saturn, afflictions, low SAV/BAV, if present]
- **Evidence Limits**: [Name any missing mandatory layers early, especially D8 or missing sniper derivation rows]

4. ### Calculation Audit
[MANDATORY: Show the source path for each sensitive factor. If the payload does not provide a derivation row, write "source derivation not supplied" instead of asserting.]
- **Badhaka**: [Lagna sign/type -> Badhaka house -> sign/lord -> active dasha/transit links]
- **Primary Marakas**: [2nd/7th lords and their natal condition]
- **Secondary Maraka / Exit Layer**: [12th lord/house and relevant activation]
- **Kharesh / 22nd Drekkana**: [D3 ascendant sign if supplied -> 8th from D3 ascendant / danger sign -> Kharesh lord -> D1 condition. Do not merely say "Kharesh is X" without this path.]
- **64th Navamsa from Moon**: [D9 Moon sign if supplied -> 4th from D9 Moon / danger sign -> lord -> D1 condition. Do not merely say "64th Navamsa lord is X" without this path.]
- **Bhrigu Bindu / Mrityu Bhaga**: [Point, sign, lord, planets/degree rows if supplied]
- **D8 / D3 / D30 Availability**: [Present or missing. If D8 is not supplied, write "D8 not supplied; longevity divisional confirmation is incomplete" and reduce D8/D3/D30 score accordingly.]

5. ### Confluence Matrix
[MANDATORY: Do NOT use markdown tables or pipe-separated table rows. Mobile chat cannot render wide tables. Use stacked window blocks exactly like this.]

#### Window 1: [Name + date range]
- **Dasha Trigger**: [Present/Weak/Missing + MD/AD/PD/SK/PR or Chara MD/AD]
- **Maraka/Badhaka/Kharesh**: [Present/Weak/Missing + 2/7, 12th, Badhaka, Kharesh links]
- **8th/12th/Longevity Activation**: [Present/Weak/Missing + houses/lords/karakas]
- **D8/D3/D30 Confirmation**: [Present/Weak/Missing or "not available"; name the chart and exact confirming house/lord/planet]
- **Sniper Points**: [Present/Weak/Missing + 64th Navamsa, Mrityu Bhaga, Bhrigu Bindu, Kharesh sign]
- **Ashtakavarga Filter**: [Present/Weak/Missing + SAV/BAV from provided data only]
- **Transit Trigger**: [Present/Weak/Missing + Saturn/Jupiter/Rahu-Ketu over sensitive points]
- **Score Breakdown**: [Dasha 0-2; Maraka/Badhaka/Kharesh 0-2; 8th/12th 0-1.5; D8/D3/D30 0-1.5; Sniper 0-1.5; AV 0-1; Transit 0-1. If D8 is missing, D8/D3/D30 score cannot exceed 0.8.]
- **Confluence Score**: [0-10 total, based only on the score breakdown above]
- **Confluence Grade**: [Only one of: High / Medium / Low. Do not write "Medium-High". High requires 6+ score and 3+ independent categories including dasha.]
- **Classification**: [health stress-test / critical transition risk / classical terminal candidate]

[Repeat the same stacked block for Window 2, Window 3, etc. Never output a table.]

6. ### Ranked Candidate Windows
[List 3-5 windows strongest first.]
- **Window [1/2/3]**: [Name + date range]
  - **Promise Window**: [Broader period]
  - **Execution Band**: [Narrower period only if evidence supports it]
  - **Confluence Score / Grade**: [0-10 + exactly one of High/Medium/Low; do not write Medium-High]
  - **Score Breakdown**: [Repeat compact score components; never give a score without this]
  - **Why It Ranks Here**: [Evidence categories that agree]
  - **What Protects**: [Contradictory/protective factors]
  - **What Is Missing**: [Required evidence not present]
  - **Interpretation**: [Stress-test / critical transition risk / terminal candidate; no fatal certainty]

7. ### Technical Deep Dive
- **Dasha Logic**: [Why the selected dasha lords matter]
- **Maraka-Badhaka-Kharesh Logic**: [Specific planets/houses + derivation/source path]
- **64th Navamsa / Mrityu Bhaga / Bhrigu Bindu**: [Only from supplied data + derivation/source path]
- **D8 / D3 / D30 / D9 Confirmation**: [Divisional evidence; state missing charts explicitly]
- **Ashtakavarga (SAV & BAV)**: [Numeric values only when present]
- **Transit Confirmation**: [How transits refine timing]
- **Conflict Resolution**: [Why lower windows are not ranked higher]
- **Evidence Limitations**: [What could not be verified from the supplied payload]

8. ### Practical Caution
[Health/lifestyle caution and medical-care reminder without diagnosing or prescribing. Do not name specific diseases, organ diagnoses, or therapeutic instructions unless the user already named them.]

<div class="final-thoughts-card">**Final Verdict**: [Ranked conclusion: strongest window, confidence level, and key evidence. No guaranteed death date.]</div>

### ABSOLUTE LANGUAGE RESTRICTIONS
- Do not use deterministic claims: "guarantee", "ensure", "will successfully", "certain", "unavoidable", "projecting a lifespan", "final exit", "death date", "will die".
- Do not promise the manner or emotional quality of death: no "peaceful release", "spiritually oriented release", "merges back with source", or similar.
- Do not call a planet a "sub-lord", "sub-period lord", CSL, CSSL, or dasha lord unless the supplied dasha/KP evidence explicitly shows that role. If a planet is only Kharesh, 64th Navamsa lord, dispositor, or transit trigger, name that exact mechanism.
- Do not say D8/D3/D30 confirmation is "Yes" when D8 is missing; write "D3/D30 present, D8 missing" or equivalent.
"""

TEMPLATE_CHART_FOCUS = """
### 🪐 CHART-FOCUSED READING (MANDATORY)
Use this structure when the user explicitly asks to analyze a specific chart or lens such as Lagna, D9/Navamsha, D10, Karkamsa, or Swamsa.

1. <div class="quick-answer-card">**Quick Answer**: [Give the direct high-level reading of the requested chart. State what this chart/lens says overall about the native, in plain language, without splitting into school-wise sections.]</div>

2. ### What This Chart Governs
[Briefly explain what the requested chart/lens primarily represents in Jyotish and why it matters for the user's question.]

3. ### Core Strengths
[3-5 bullets naming the strongest supportive combinations, planets, houses, or signatures inside this chart/lens.]

4. ### Core Challenges
[3-5 bullets naming the main weaknesses, delays, contradictions, or karmic pressure points in this chart/lens.]

5. ### Focused Interpretation
[A unified synthesis of the requested chart. Blend Parashari, Jaimini, Nakshatra, and other relevant logic into one chart-centric explanation. Do NOT create separate sections titled "The Jaimini View", "Nadi Interpretation", "KP", or similar unless the user explicitly asked for school-by-school comparison.]

6. ### Current Activation
[Optional but preferred when dasha/transit/current-period support exists: explain whether the requested chart is presently activated, and through which current periods or triggers.]

7. ### Practical Guidance
[Actionable advice based on the requested chart's strengths and weaknesses.]

8. <div class="final-thoughts-card">**Final Verdict**: [A concise final judgment centered on the requested chart/lens and its present relevance.]</div>
"""

# Special Template for Mundane Astrology
TEMPLATE_MUNDANE = """
### 🏛️ MUNDANE ELITE ANALYSIS (MANDATORY)
Your response MUST follow this exact sequence and adhere to the strict technical rules below:

1. <div class="quick-answer-card">**Executive Prediction & Probability**: [Direct verdict with a specific probability percentage (e.g. 80%). No ambiguity.]</div>
   - [If `sports_scorecard.available` is true, the verdict MUST follow `sports_scorecard.edge.predicted_winner` / `result_type` and the probability MUST match `sports_scorecard.edge.confidence_percent`.]
   - [If `sports_scorecard.edge.result_type = narrow_edge`, use explicitly narrow wording such as "slight edge", "narrow edge", or "lean". Do NOT use "decisive", "dominant", "certain", or equivalent.]
   - [If `sports_scorecard.edge.result_type = draw_or_extra_time`, present the match as balanced and do NOT name a regulation-time winner.]

2. ### Key Astrological Triggers & Macro Trends: [Cite 3-4 high-impact triggers from the event chart. You MUST also explicitly state the Nav Nayak (King of the Year) and the impact of the Aries Ingress from the `ingress_data`.]

3. ### Panchang & Event Synergy:
   - [Analyze the `Tithi`, `Nakshatra`, and `Yoga` from `event_panchang`. Explain how this specific combination influences the "auspiciousness" or "volatility" of the event start.]
   - [If `event_panchang.vara.name` is present, weekday rulership must match it exactly. Do not assign a conflicting day lord.]

4. ### Battle of the Charts (Side-by-Side Analysis):
   - #### Deterministic Scorecard: [If `sports_scorecard.available` is true, compare the two sides using `sports_scorecard.sides`, their anchor lords, scores, and reasons. This is the primary match-outcome spine.]
   - #### Entity Dashas: [Detail the exact Vimshottari Mahadasha/Antardasha for EACH nation involved. Cite them by name. If data is unavailable for an entity, state it clearly.]
   - #### Locational Analysis: [Contrast the Lagna/House placements for the capitals of each entity from `locational_analysis`.]
   - [For sports answers, clearly separate deterministic evidence from broader interpretive color. The deterministic scorecard must come first.]

5. ### Regional & Geographic Citations:
   - #### Strategic Impacts: [You MUST cite specific provinces or regions by name from the `geographic_impacts` data (e.g. "Gilan", "Kurdistan"). Generic regional terms are forbidden.]

6. ### Market & Commodity Precision:
   - #### Vedha Analysis: [Detail the exact triggers for Oil, Silver, or Grains from `commodity_impacts`. Specify the triggering planet and if it is a 'direct' or 'vedha' impact.]

7. ### Critical Timing & Tipping Points:
   - [For non-sports mundane answers: exact dates/hours of peak volatility.]
   - [For sports answers: if no explicit timing sub-data is present in the JSON, write exactly one short line stating that no intra-match turning-point windows were computed in the current model, so the judgment is based on the kickoff chart and the deterministic scorecard.]

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
    'PREDICT_DAILY': TEMPLATE_DAILY_SUMMARY,
    # CTA-only remedy mode (query_context.remedy_followup). Wording-only asks are remapped away before schema selection.
    'RECOMMEND_REMEDY_FOR_PROBLEM': TEMPLATE_REMEDIAL_GUIDANCE,
    'REMEDIAL_GUIDANCE': TEMPLATE_REMEDIAL_GUIDANCE,
    'MUNDANE': TEMPLATE_MUNDANE,
    'DEV_EVENT_LOG': TEMPLATE_DEV_EVENT_LOG,
    'LIFESPAN_EVENT_TIMING': TEMPLATE_LIFESPAN_TIMELINE,
    'LIFE_TERMINATION_RESEARCH': TEMPLATE_LIFE_TERMINATION_RESEARCH,
    'DEFAULT': TEMPLATE_DEEP_DIVE,
}

def _normalize_chart_focus_label(chart_focus: dict | None) -> str:
    if not isinstance(chart_focus, dict):
        return "requested chart"
    label = (chart_focus.get("label") or chart_focus.get("primary") or "").strip()
    return label or "requested chart"


def _chart_focus_section_customizations(chart_focus: dict | None) -> tuple[str, str, str, str]:
    primary = ""
    if isinstance(chart_focus, dict):
        primary = (chart_focus.get("primary") or "").strip()
    if primary == "D1":
        return (
            "### Identity, Body, and Life Direction",
            "[Explain how this chart/lens defines the native's identity, physical embodiment, temperament, and overall life direction.]",
            "### Life Path Interpretation",
            "[A unified reading of how the Lagna/D1 shapes the native's personality, vitality, orientation to life, and the broad direction of worldly experience.]",
        )
    if primary == "D9":
        return (
            "### Marriage, Dharma, and Maturity",
            "[Explain how this chart/lens reflects marriage quality, dharmic alignment, inner maturity, and how the natal promise ripens over time.]",
            "### Marriage and Dharma Interpretation",
            "[A unified reading of relationship karma, spouse/marital quality, dharmic growth, and how the native matures through commitment, values, and inner development.]",
        )
    if primary == "D10":
        return (
            "### Vocation, Status, and Work Function",
            "[Explain how this chart/lens reflects profession, public role, status, responsibility, and the kind of work the native is meant to perform.]",
            "### Career and Work Interpretation",
            "[A unified reading of vocation, work function, authority, visibility, contribution, and the way professional karma manifests in concrete roles.]",
        )
    return (
        "### What This Chart Governs",
        "[Briefly explain what the requested chart/lens primarily represents in Jyotish and why it matters for the user's question.]",
        "### Focused Interpretation",
        "[A unified synthesis of the requested chart. Blend Parashari, Jaimini, Nakshatra, and other relevant logic into one chart-centric explanation. Do NOT create separate sections titled \"The Jaimini View\", \"Nadi Interpretation\", \"KP\", or similar unless the user explicitly asked for school-by-school comparison.]",
    )


def _get_chart_focus_schema(chart_focus: dict | None) -> str:
    label = _normalize_chart_focus_label(chart_focus)
    schema = TEMPLATE_CHART_FOCUS.replace("requested chart/lens", f"{label} chart/lens")
    schema = schema.replace("requested chart", label)
    governs_header, governs_body, interp_header, interp_body = _chart_focus_section_customizations(chart_focus)
    schema = schema.replace(
        "### What This Chart Governs",
        governs_header,
    )
    schema = schema.replace(
        "[Briefly explain what the requested chart/lens primarily represents in Jyotish and why it matters for the user's question.]",
        governs_body,
    )
    schema = schema.replace(
        "### Focused Interpretation",
        interp_header,
    )
    schema = schema.replace(
        "[A unified synthesis of the requested chart. Blend Parashari, Jaimini, Nakshatra, and other relevant logic into one chart-centric explanation. Do NOT create separate sections titled \"The Jaimini View\", \"Nadi Interpretation\", \"KP\", or similar unless the user explicitly asked for school-by-school comparison.]",
        interp_body,
    )
    return schema


def get_response_schema_for_mode(mode: str, premium_analysis: bool = False, chart_focus: dict | None = None) -> str:
    """
    Selects the appropriate response schema based on the analysis mode.
    This function now centralizes the inclusion of common response blocks.
    """
    # Handle None or empty mode
    if not mode:
        mode = 'DEFAULT'
    
    # Chart-focused questions should render as a unified chart reading rather than the
    # normal multi-school deep-dive template.
    if isinstance(chart_focus, dict) and chart_focus.get("kind") == "chart_specific":
        base_schema = _get_chart_focus_schema(chart_focus)
    else:
        # Select the base schema using the mapping, falling back to DEFAULT
        base_schema = SCHEMA_MAPPING.get(mode.upper(), SCHEMA_MAPPING['DEFAULT'])
    
    # Programmatically add common blocks to all schemas except special cases
    if mode.upper() not in [
        'DEV_EVENT_LOG',
        'LIFESPAN_EVENT_TIMING',
        'LIFE_TERMINATION_RESEARCH',
        'RECOMMEND_REMEDY_FOR_PROBLEM',
        'REMEDIAL_GUIDANCE',
    ]:
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
        if mode.upper() in ['ANALYZE_TOPIC_POTENTIAL', 'ANALYZE_ROOT_CAUSE', 'PREDICT_PERIOD_OUTLOOK', 'DEFAULT', 'PREDICT_DAILY', 'LIFESPAN_EVENT_TIMING', 'LIFE_TERMINATION_RESEARCH']:
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
    _, language_instruction, final_check = build_output_language_blocks(_lang, user_question)
    delivery_format_instruction = build_delivery_format_instruction(intent_block)
    
    if str(intent_mode or "").upper() == "PREDICT_DAILY":
        elaborate_instruction = """
CRITICAL - DAILY ANSWER SCOPE (NON-NEGOTIABLE):
The user asked about one specific day. Keep the answer day-specific and practical.
- Aim for 2,500-4,000 characters, not a lifetime report.
- Do not expand into full natal, Jaimini, KP, Nadi, divisional, or long dasha methodology blocks.
- Use natal chart and major dashas only as background filters; do not present Mahadasha/Antardasha as the day's event.
- If `daily_prediction_spine` is present in BIRTH CHART DATA, it is the authoritative daily evidence. Use it before all broad natal context.
- Lead from `daily_prediction_spine.dasha_stack`: Prana and Sookshma are the sharpest event triggers, Pratyantardasha frames the day, Antardasha/Mahadasha are background permission.
- For each active dasha planet, use its `natal`, `transit`, and `trigger` fields. If it returns to natal sign/nakshatra/degree or aspects/conjoins natal planets, explicitly translate those activated houses/lordships into concrete day-level possibilities.
- Use `daily_prediction_spine.daily_judgment.top_activated_houses`, `top_event_domains`, and `massive_result_factors` to rank what is most likely to happen. Do not treat all houses or all dasha levels equally.
- Use `daily_prediction_spine.school_judgments` as the daily cross-check: Parashari = main event trigger, KP = materialization through event cusps, Nadi = exact conjunction/trine linkage, Jaimini = Chara Karaka manifestation, Ashtakavarga = ease/resistance/confidence. Keep these as compact evidence, not separate lifetime reports.
- Lead with the requested date, the transiting Moon/nakshatra, panchanga/day quality if available, fast transits, and practical morning/afternoon/evening guidance.
"""
    else:
        elaborate_instruction = """
CRITICAL - RESPONSE LENGTH & DEPTH (NON-NEGOTIABLE):
Your full response MUST be comprehensive. Short or summary-style answers are FORBIDDEN.
- For Birth Chart queries: Aim for 12,000 characters. Expand every section with planetary reasoning, classical references, and technical detail.
- For Mundane/Event queries: Aim for 3,000-5,000 characters. Focus on precision, house comparison (1st vs 7th), dasha synchronization, and critical timing.
- Prioritize depth and clarity. Output sufficient detail to justify the prediction.
"""
    
    # Use the new centralized schema selection function, using the reliable intent_mode
    response_format_instruction = get_response_schema_for_mode(
        intent_mode,
        premium_analysis=premium_analysis,
        chart_focus=intent_block.get("chart_focus") if isinstance(intent_block.get("chart_focus"), dict) else None,
    )
    
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
        elif intent_mode.upper() == 'LIFE_TERMINATION_RESEARCH':
            analysis_type_from_intent = 'LIFE_TERMINATION_RESEARCH'
            
        system_instruction = build_system_instruction(
            analysis_type=analysis_type_from_intent,
            intent_category=intent_category,
            mode=intent_mode,
            death_analysis_unlocked=bool(context.get("death_analysis_unlocked")),
        )

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

    if static_context.get("classical_rule_matches"):
        prompt_parts.append(
            "CLASSICAL RULE MATCH USAGE:\n"
            "- `classical_rule_matches` contains pre-filtered supporting sutra evidence, not a mandate.\n"
            "- For now only `derived_12th_from_topic_house` is enabled: the 12th counted from the topic house shows expense, sacrifice, loss, release, or investment for that topic.\n"
            "- Use it only when its evidence makes it relevant; do not force it into the answer if stronger chart/dasha/transit evidence points elsewhere."
        )

    time_context = f"IMPORTANT CURRENT DATE INFORMATION:\n- Today's Date: {current_date_str}\n- Current Time: {current_time_str}\n- Current Year: {current_date.year}\n\nCRITICAL CHART INFORMATION:\n{ascendant_summary}"
    prompt_parts.append(time_context)
    
    prompt_parts.append(system_instruction)
    prompt_parts.append(
        f"{language_instruction}"
        f"{delivery_format_instruction}"
        f"{elaborate_instruction}"
        f"{response_format_instruction}"
        f"{user_context_instruction}"
        f"{_single_native_format_guard(analysis_type)}"
        f"{VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION}"
    )
    
    prompt_parts.append(build_multi_question_focus_instruction(_lang))
    try:
        from ai.prediction_anchor import (
            PREDICTION_ANCHOR_META_INSTRUCTION,
            career_timing_prompt_for_topic,
            compare_verdict_to_anchor,
            format_timing_contract_lock_block,
            get_locked_anchor,
            infer_topic_key,
            should_apply_timing_contract,
        )

        intent_category = context.get("intent", {}).get("category", "general") if isinstance(context.get("intent"), dict) else "general"
        if should_apply_timing_contract(mode=intent_mode, category=intent_category, question=user_question):
            topic_key = infer_topic_key(user_question, category=intent_category)
            locked = get_locked_anchor(context.get("extracted_context"), topic_key)
            if locked:
                prompt_parts.append(format_timing_contract_lock_block(locked, rerank=compare_verdict_to_anchor(locked, None)))
            elif str(intent_category or "").lower() in {"career", "job", "promotion", "business"} or str(topic_key).startswith("career"):
                prompt_parts.append(
                    career_timing_prompt_for_topic(
                        topic_key, category=intent_category, question=user_question
                    )
                )
            prompt_parts.append(PREDICTION_ANCHOR_META_INSTRUCTION.strip())
    except Exception:
        pass
    prompt_parts.append(f"{history_text}\nCURRENT QUESTION: {user_question}")
    prompt_parts.append(final_check)
    prompt_parts.append(NEXT_ACTION_META_INSTRUCTION.strip())
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
### Nakshatra Insights: Star Shakti and mansion themes (no remedy dump).
### Timing & Guidance: Specific monthly roadmap for next 6-12 months (priorities/cautions only—not remedies).
[FINAL THOUGHTS CARD]: Outlook anchored in classical text authority (cite BPHS, Saravali, or Phaladeepika).
"""
