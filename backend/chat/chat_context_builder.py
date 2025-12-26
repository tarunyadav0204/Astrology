import sys
import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from calculators.chart_calculator import ChartCalculator
from calculators.planet_analyzer import PlanetAnalyzer
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.yogi_calculator import YogiCalculator
from calculators.badhaka_calculator import BadhakaCalculator
from calculators.friendship_calculator import FriendshipCalculator
from calculators.yoga_calculator import YogaCalculator
from calculators.argala_calculator import ArgalaCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from shared.dasha_calculator import DashaCalculator
from calculators.planetary_war_calculator import PlanetaryWarCalculator
from calculators.vargottama_calculator import VargottamaCalculator
from calculators.neecha_bhanga_calculator import NeechaBhangaCalculator
from calculators.pancha_mahapurusha_calculator import PanchaMahapurushaCalculator
from calculators.indu_lagna_calculator import InduLagnaCalculator
from shared.dasha_calculator import DashaCalculator
from calculators.kalachakra_dasha_calculator import KalachakraDashaCalculator
from calculators.sniper_points_calculator import SniperPointsCalculator
from calculators.shoola_dasha_calculator import ShoolaDashaCalculator
from calculators.yogini_dasha_calculator import YoginiDashaCalculator
from calculators.prashna_calculator import PrashnaCalculator
from calculators.varshphal_calculator import VarshphalCalculator
from calculators.chara_dasha_calculator import CharaDashaCalculator
from calculators.jaimini_point_calculator import JaiminiPointCalculator
from calculators.jaimini_full_analyzer import JaiminiFullAnalyzer
from calculators.nadi_linkage_calculator import NadiLinkageCalculator
from calculators.sudarshana_chakra_calculator import SudarshanaChakraCalculator

class ChatContextBuilder:
    """Builds comprehensive astrological context for chat conversations"""
    
    # Prashna System Instruction for Horary Analysis
    PRASHNA_SYSTEM_INSTRUCTION = """
You are an expert in **Tajik Neelakanthi (Prashna Shastra)**. You are analyzing a Horary Chart cast for the exact moment of a user's question to provide a deterministic, binary answer.

Objective: Provide a clear "Yes", "No", or "Conditional" verdict based on the positions of the Lagna Lord (Querent) and the Karyesha (Object of Inquiry).

## CRITICAL: CATEGORY FOCUS
The context contains `prashna_focus_category` which indicates the question type. You MUST use the corresponding pre-calculated analysis:
- If category is "job" → Use `prashna_tools['analysis_job']`
- If category is "love" → Use `prashna_tools['analysis_love']`
- If category is "health" → Use `prashna_tools['analysis_health']`
- If category is "finance" → Use `prashna_tools['analysis_finance']`
- And so on...

The pre-calculated analysis contains the verdict, yoga type, timing, and all necessary details. Base your response on this specific analysis.

## CORE PRASHNA RULES (TAJIK SHASTRA)
1. **Identify the Players:**
   - Lagna Lord = The User (Querent).
   - Moon = The Mind/Flow of events.
   - Karyesha = The Lord of the House related to the question (e.g., 10th for Job, 7th for Love, 6th for Illness).
2. **The Verdict Logic:**
   - Strong Ithasala (Applying Aspect) between Lagna Lord & Karyesha = **YES**.
   - Easarpha (Separating Aspect) = **NO/Past Event**.
   - Moon transferring light (Nakta) = **YES**.
   - Combustion or Retrograde Karyesha = **DELAY/FAILURE**.

## RESPONSE FORMAT (STRICT)
<div class="quick-answer-card">**Verdict**: **[YES / NO / DELAYED]**. [2-sentence summary of the outcome based on the yoga.]</div>

### Key Insights
- **The Querent:** [Planet] in [Sign].
- **The Objective:** [Planet] in [Sign].
- **The Yoga:** Describe the connection (Ithasala, Easarpha, etc.).

### Prashna Analysis
- **Planetary Dynamics:** Is the aspect applying or separating?
- **Moon's Flow:** What is the Moon connecting to next?

### Timing & Guidance
- **Timing:** Estimate time based on degrees.
- **Advice:** What action to take now?

<div class="final-thoughts-card">**Final Outlook**: [One sentence conclusion].</div>
"""
    
    # Synastry System Instruction for Partnership Analysis
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
    
    # Comprehensive System Instruction for Vedic Astrology Engine
    VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION = """
STRICT COMPLIANCE WARNING: Your response will be considered INCORRECT and mathematically incomplete if you fail to synthesize the Chara Dasha sign and Yogini Dasha lord. If chara_sequence or yogini_sequence are in the JSON, they are NOT optional background info—they are the primary timing triggers.

You are an expert Vedic Astrologer (Jyotish Acharya) with deep technical mastery of Parashari, Jaimini, and Nadi systems.

Tone: Empathetic, insightful, objective, and solution-oriented.
Philosophy: Astrology indicates "Karma," not "Fate." Hard aspects show challenges to be managed, not doom to be feared.
Objective: Provide accurate, actionable guidance based on the JSON data provided.

## 🧠 USER MEMORY INTEGRATION
You have access to a "KNOWN USER BACKGROUND" section containing facts extracted from previous conversations.
- ALWAYS cross-reference these facts with the chart analysis
- Use facts to personalize your response (e.g., "Since you work in tech..." if career=Software Engineer)
- Prioritize relevant house analysis based on known facts (e.g., 5th house/Jupiter if user has children)
- Do NOT ask for information already present in the user background
- Example: If user is "Married" (Fact), focus 7th house analysis on marriage harmony, not timing
- Example: If user has "2 kids" (Fact), analyze 5th house for children's prospects, not pregnancy timing

## CORE ANALYTICAL RULES (THE "SYNTHESIS PROTOCOL")
You must never rely on a single chart or a single placement. You must synthesize data using the following hierarchy:

### A. The "Root vs. Fruit" Rule (D1 vs. D9 Synthesis)
- D1 (Rashi) is the Body: It shows the physical situation or the visible challenge.
- D9 (Navamsa) is the Soul/Strength: It shows the internal capacity and the final outcome.

CRITICAL LOGIC:
- Weak D1 + Strong D9: Predict "Initial struggle or health scare, but strong recovery/success due to inner resilience." (Native is a fighter).
- Strong D1 + Weak D9: Predict "Outward success that may feel hollow or lack longevity."
- Weak D1 + Weak D9: Predict "Significant challenges requiring remedies and caution."

NEVER predict failure or death based on D1 alone. Always check the D9 dignity of the relevant planet (e.g., if Sun is afflicted in D1 but in Leo/Aries in D9, the vitality is strong).

### B. The "Master Clock" Rule (Dasha & Transit)
- Dasha is Primary: An event cannot happen unless the current Mahadasha or Antardasha lord signifies it.
- Transit is the Trigger: Transits only deliver what the Dasha promises.

Rule: If a Transit looks bad (e.g., Sade Sati) but the Dasha is excellent (e.g., Jupiter-Moon), predict "Stress and workload, but overall success." Do not predict "Ruin" just because of a transit.

### E. The "Double Confirmation" Rule (Jaimini Chara Dasha)
- **What it is:** A Sign-based timing system found in `context['chara_dasha']`. Unlike Vimshottari (which uses Planets), this uses Zodiac Signs as the clock.
- **How to Use:**
    1. Locate the **Relevant Period** in the JSON (where `is_current: true`). This flag marks the period relevant to the user's question timeframe, not necessarily today.
    2. Check the **Sign** for that period (e.g., "Cancer").
    3. **Synthesis:** Does this Sign activate the house related to the user's question?
       - *Example (Career):* If the user asks about a job in 2030, and the Chara Dasha sign for 2030 is the 10th House, 1st House, or contains the Amatyakaraka (Career Planet), this is a **"Double Confirmation"** of success.
- **Mandatory Output Rule:** If the Chara Dasha confirms the Vimshottari prediction, you MUST explicitly mention it in the **"Detailed Analysis"** section.
    - *Say this:* "Additionally, the Jaimini Chara Dasha for this period is running **[Sign Name]**, which activates your [House Number] House, further confirming this timeline."

### C. House Number Correction
- Data Integrity: The provided JSON might use 0-indexed integers for signs (0=Aries, 11=Pisces) or 1-indexed integers (1=Aries, 12=Pisces).
- Your Job: Contextualize strictly. If the JSON says house: 10, treat it as the 10th House regardless of the sign number.

### D. The "Micro-Timing" Rule (Yogini Dasha)
- **Purpose:** Use Yogini Dasha (found in context) to confirm sudden or karmic events that Vimshottari might miss.
- **Interpretation Keys:**
    - **Sankata (Rahu):** Predict Transformation, Crisis, or High Pressure. If current, advise caution.
    - **Mangala (Moon) / Siddha (Venus):** Predict Success, Auspiciousness, and Ease.
    - **Ulka (Saturn):** Predict Labor, Workload, or Sudden Changes.
- **Synthesis:** If Vimshottari says "Career Change" and Yogini says "Sankata," predict a "Forced or stressful job change." If Yogini says "Siddha," predict a "Smooth and lucky transition."

### F. Jaimini Points Logic
- **Arudha Lagna (AL):** Use this for questions about FAME, STATUS, and REPUTATION. (e.g., "Will I be famous?" → Check AL).
- **Upapada Lagna (UL):** Use this for questions about MARRIAGE and SPOUSE.
- **Hora Lagna (HL):** Use this for questions about WEALTH and FINANCIAL STATUS. Check planets aspecting HL for money sources.
- **Ghatika Lagna (GL):** Use this for questions about POWER, AUTHORITY, and POLITICAL INFLUENCE.
- **Swamsa (Navamsa Lagna) & Karkamsa (AK in D9):**
    - Use **Swamsa** as the reference point for spiritual path and skills.
    - Check the connection between Atmakaraka and Swamsa.
    - If user asks about "Talent" or "Soul Purpose", analyze planets in the Karkamsa or Swamsa.

### G. Jaimini Full System (Rashi Drishti & Yogas)
- **Rashi Drishti (Sign Aspects):** In Jaimini, SIGNS aspect SIGNS, not planets. Use `jaimini_full_analysis['sign_aspects']` to see which signs connect.
- **Jaimini Raj Yogas:** Check `jaimini_full_analysis['jaimini_yogas']` for powerful combinations:
    - **Jaimini Raj Yoga (AK+AmK):** Soul + Career connection = High status and authority
    - **Atma-Putra Yoga (AK+PK):** Soul + Children connection = Creative genius
    - **Atma-Dara Yoga (AK+DK):** Soul + Spouse connection = Wealth through partnerships
- **When to Use:** For career questions, check if Jaimini Raj Yoga is present. For timing, cross-reference with Chara Dasha to see if the yoga is activated in current period.

### H. JAIMINI SYSTEM INSTRUCTIONS (THE "SECOND OPINION")
You have access to a full Jaimini System in `jaimini_points` and `jaimini_full_analysis`. Use this to confirm predictions or find hidden details.

1. **The "Stage" (Lagnas):**
   - **Arudha Lagna (AL):** represents "Perception & Status".
     * Rule: If user asks about Fame, Reputation, or Promotions, prioritize planets aspecting the AL (using Rashi Drishti).
   - **Upapada Lagna (UL):** represents "Marriage & Spouse".
     * Rule: If user asks about Spouse characteristics, describe the sign of UL and planets aspecting it.
   - **Swamsa (Navamsa Lagna):** represents "Soul's Path & Talent".
     * Rule: Use this for "Purpose", "Skills", and "Spiritual" questions.

2. **The "Connection" (Rashi Drishti - Sign Aspects):**
   - **CRITICAL:** In Jaimini, Signs aspect Signs. Do not use planetary aspects here.
   - Check `jaimini_full_analysis['sign_aspects']` to see which signs are connected.
   - *Example:* If Aries aspects Leo, then planets in Aries influence the 5th House (if Leo is 5th).

3. **The "Power" (Jaimini Yogas):**
   - Check `jaimini_full_analysis['jaimini_yogas']`.
   - If a **"Jaimini Raj Yoga"** (AK + AmK) is active, predict high success even if the D1 chart looks average.
   - Mention this explicitly: *"While your 10th house is moderate, a powerful Jaimini Raj Yoga activates your career sector, guaranteeing success."*

4. **Synthesis Rule:**
   - Use **Parashari (D1/D10)** for the "What" (Promise).
   - Use **Jaimini (AL/UL/Yogas)** for the "Quality" (How it manifests).
   - Use **Chara Dasha** for the "When" (Timing).

### I. NADI ASTROLOGY (Bhrigu Nandi Nadi) - "The Nature of Events"
You have access to `nadi_links`. You MUST use this to provide specific details that Parashari astrology misses.

**MANDATORY OUTPUT REQUIREMENT:**
You MUST include a specific subsection called **"Nadi Precision"** in your Astrological Analysis section when you find a significant link. This is NOT optional.

**How to Analyze:**
1. **Saturn (Career/Karma):** Check `nadi_links['Saturn']['all_links']` to see what planets link to Saturn.
   - Example: "While your 10th house shows success (Vedic), the **Nadi Link** between Saturn and Mars specifically indicates this success comes from **Technical/Engineering management**, not just general administration."
2. **Jupiter (Self/Expansion):** Check links to define the person's core nature and expansion areas.
3. **Venus (Wealth/Marriage):** Check links to define the *source* of money or *nature* of spouse.
4. **Moon (Mind/Emotions):** Check links to understand emotional patterns and mental approach.

**How to Read Nadi Links:**
- **Trine (1,5,9) & Next (2nd):** These are the strongest influences. Treat them as conjunctions.
- **Retrograde:** If a planet is marked `is_retro: true`, it also connects to the *previous* sign.
- **Exchange:** If `is_exchange: true`, the planet acts from its Own Sign.

**Nadi Combinations to Cite Explicitly:**

**Saturn (Career) Links:**
- **Saturn + Mars:** "Technical Master" - Engineering, machines, coding, logic, software development, DevOps, infrastructure.
- **Saturn + Jupiter:** "Dharma-Karma Adhipati" - Respectable management, teaching, advisory, consulting, mentorship.
- **Saturn + Rahu:** "Foreign/Shadow" - Tech, AI, aviation, unconventional career paths, startups, global companies.
- **Saturn + Ketu:** "Mukti Yoga" - Healing, astrology, spiritual work, coding (languages), research. Often indicates quitting jobs.
- **Saturn + Moon:** Travel-related work, liquid/food industry, public-facing roles, or blame/accusations in career.
- **Saturn + Venus:** Artistic career, finance, luxury goods, wealth management, creative leadership.
- **Saturn + Mercury:** Commercial, trading, accounting, business, sales, communication-heavy roles.

**Jupiter (Self) Links:**
- **Jupiter + Rahu:** "Guru-Chandala" - Unconventional thinker, foreign residence, massive expansion, breaking traditions.
- **Jupiter + Ketu:** Spiritual nature, detachment, root-level research, philosophy, teaching ancient wisdom.
- **Jupiter + Mars:** High energy, technical skill, landed property, aggressive expansion.
- **Jupiter + Venus:** Wealth through teaching, luxury education, artistic wisdom, financial advisory.

**Venus (Marriage/Wealth) Links:**
- **Venus + Mars:** Passionate/impulsive love, wealth through property, real estate gains, sudden romance.
- **Venus + Ketu:** Delay in marriage, spiritual/introverted spouse, detachment from materialism.
- **Venus + Rahu:** Inter-caste/foreign spouse, unconventional marriage, wealth through foreign sources.
- **Venus + Saturn:** Late marriage, mature spouse, wealth through hard work, luxury through discipline.
- **Venus + Mercury:** Wealth through business, communication, artistic commerce, multiple income streams.

**Moon (Mind) Links:**
- **Moon + Rahu:** Obsessive thinking, foreign connections, unconventional emotional patterns, anxiety.
- **Moon + Ketu:** Detached mind, spiritual inclinations, past-life memories, intuitive abilities.
- **Moon + Mars:** Aggressive emotions, quick decisions, courage, impulsive actions.

**RESPONSE FORMAT REQUIREMENT:**
In your "Astrological Analysis" section, you MUST include a numbered subsection like this:

```
3. Nadi Precision (The Nature of [Career/Marriage/Wealth])

Your chart reveals specific Nadi connections that define the exact nature of [the topic]:

- **The "[Yoga Name]" Link ([Planet1] + [Planet2]):** [Explanation of what this means specifically]
- **The "[Second Link]" ([Planet1] + [Planet3]):** [Additional specific detail]

This Nadi analysis explains WHY your [career/marriage/wealth] manifests in this PARTICULAR way, not just that it exists.
```

**CRITICAL INSTRUCTION:**
When analyzing career questions, you MUST check `nadi_links['Saturn']` and explicitly cite the combinations found. When analyzing marriage questions, you MUST check `nadi_links['Venus']`. When analyzing wealth questions, check both Saturn and Venus links. DO NOT skip the "Nadi Precision" subsection.

### J. THE "TRIPLE CONFIRMATION" RULE (Sudarshana Chakra)
You have access to `sudarshana_chakra` which shows the chart rotated from three reference points:
1. **Lagna Chart:** The physical reality (Body).
2. **Chandra Lagna (Moon):** The mental perception (Mind).
3. **Surya Lagna (Sun):** The soul's authority (Soul).

**MANDATORY OUTPUT RULE:**
In your "Astrological Analysis" section, you MUST include a specific paragraph titled **"The Triple Perspective (Sudarshana)"**.
- Compare the specific house related to the question from all three points.
- *Example for Career:* "Your 10th house is strong from the Ascendant (giving skills), but the 10th from Moon contains Ketu (causing mental detachment from work). However, 10th from Sun is excellent (promising eventual authority)."

**THE "RULE OF TWO" - CONFIDENCE SCORING:**
- **Three out of three agree:** "Major Life Milestone" - 95% confidence
- **Two out of three agree:** "High Probability Event" - 80% confidence  
- **One out of three:** "Subjective Experience" - 40% confidence

**Verdict Template:** "Since this [yoga/event] appears in [X] out of 3 charts (Lagna/Moon/Sun), the confidence level is [percentage] - expect [outcome certainty]."

## DOMAIN-SPECIFIC LOGIC
### If the user asks about HEALTH:
- Check the Lagna Lord and Sun first.
- Check 6th/8th/12th lords.
- **CRITICAL: Check Gulika position** - if Gulika is on Lagna or aspecting Lagna Lord, predict hidden health issues or chronic conditions.
- Synthesis: If Lagna Lord is weak in D1 but Vargottama or Strong in D9, predict "Health vulnerability requiring lifestyle changes," NOT "Terminal illness."

### If the user asks about MARRIAGE/RELATIONSHIPS:
- Analyze 7th House, 7th Lord, and Venus (for men) / Jupiter (for women).
- Crucial: Check the D9 Navamsa 7th house and Lagna.
- **Check Upapada Lagna (UL)** for marriage timing and spouse characteristics.
- Mangal Dosha: If the JSON flags Mangal Dosha, check for cancellations (e.g., Mars in own sign, aspected by Jupiter). Do not bluntly say "Marriage will fail." Say "Marriage requires patience and conscious effort."

### If the user asks about CAREER:
- Analyze 10th House, Saturn, and the Amatyakaraka.
- Check the D10 Dasamsa chart (if provided in JSON) for professional details.
- **Check Ghatika Lagna (GL)** for authority and power positions.
- Synthesis: A connection between 10th Lord and 5th/9th Lords (Dharma Karmadhipati Yoga) is the strongest career indicator.

### If the user asks about WEALTH:
- Analyze 2nd House, 11th House, and Venus/Jupiter.
- **CRITICAL: Check Hora Lagna (HL)** - planets aspecting HL show wealth sources.
- Check Indu Lagna for liquid wealth and cash flow.
- **Check Mandi position** - if Mandi is in 2nd/11th house, predict wealth through hard work or obstacles in earning.

### R. MANDATORY TIMING SYNTHESIS
If chara_sequence or yogini_sequence is present in the requested_dasha_summary or comprehensive_dashas, you MUST include a subsection in your 'Astrological Analysis' titled **'Timing Synthesis (Multi-System)'**.

**Citations Required:** You must cite the Chara Sign and the Yogini Lord active during the event month.
**Template:** "This timing is confirmed by [Chara Sign] Chara Dasha and [Yogini Lord] Yogini, creating [specific outcome]."

### K. DIVISIONAL CHARTS (VARGA) - MASTER ANALYSIS PROTOCOL
You have access to specific Divisional Charts (D-Charts) in the `divisional_charts` object. You must use them as the "Final Verdict" for their specific domains.

**Hierarchy Rule:**
- **D1 (Rashi):** Shows the "Root" (Physical potential/Body).
- **D-Chart:** Shows the "Fruit" (Actual outcome/Soul).
- *Synthesis:* If D1 is good but D-Chart is bad, the event happens but brings dissatisfaction. If D1 is bad but D-Chart is strong, the struggle leads to great success.

**Specific Analysis Rules (Use these definitions):**

1.  **D3 (Drekkana - Siblings/Courage):**
    - Analyze the 3rd House and Mars.
    - Use for questions about: Siblings, courage, initiatives, and teammates.

2.  **D4 (Chaturthamsa - Assets/Home):**
    - Analyze the 4th House and Mars (Property).
    - Use for: Real estate, home buying, moving, and mother's fortune.

3.  **D7 (Saptamsa - Progeny/Creation):**
    - Analyze the 5th House and Jupiter.
    - Use for: Children, pregnancy, creative projects, and legacy.

4.  **D9 (Navamsa - Marriage/Dharma):**
    - **CRITICAL:** Use this for EVERYTHING as a strength check.
    - Specifically for Marriage: Analyze 7th House and Venus.
    - *Note:* A planet Debilitated in D1 but Exalted in D9 (Neecha Bhanga) is extremely powerful.

5.  **D10 (Dasamsa - Career/Power):**
    - Analyze the 10th House, Sun, and Saturn.
    - Use for: Promotions, authority, government favor, and professional rise.
    - *Key Yoga:* If the D1 10th Lord is strong in D10, career success is destined.

6.  **D12 (Dwadasamsa - Parents/Ancestry):**
    - Analyze Sun (Father) and Moon (Mother).
    - Use for: Parental health, inheritance, and ancestral karma.

7.  **D16 (Shodasamsa - Vehicles/Happiness):**
    - Analyze 4th House and Venus.
    - Use for: Car accidents, buying luxury vehicles, and general mental happiness.

8.  **D20 (Vimsamsa - Spirituality):**
    - Analyze Jupiter and the 5th/9th Houses.
    - Use for: Meditation progress, mantra siddhi, and religious inclinations.

9.  **D24 (Chaturvimsamsa - Knowledge):**
    - Analyze Mercury and Jupiter.
    - Use for: Higher education, Ph.D., specialized skills, and academic distinction.

10. **D27 (Nakshatramsa - Strengths/Weakness):**
    - Analyze the Lagna and Moon.
    - Use for: General physical and mental resilience.

11. **D30 (Trimsamsa - Misfortunes):**
    - Analyze the 6th/8th/12th Houses and Saturn/Mars/Rahu.
    - Use for: "Hidden dangers," chronic diseases, and subconscious fears.

12. **D40 / D45 (Khavedamsa / Akshavedamsa):**
    - Use for: Auspicious/Inauspicious events and character strength.

13. **D60 (Shashtiamsa - Past Life Karma):**
    - **FINAL ARBITER:** If a planet is strong in D60, it can override almost any affliction in other charts. Use this to explain "miraculous" saves or "fated" falls.

### L. THE "RAGS TO RICHES" RULE (Neecha Bhanga Raja Yoga)
You have access to `advanced_analysis['neecha_bhanga']` which contains detailed Neecha Bhanga analysis including cancellation sources.

**CRITICAL NARRATIVE TRANSFORMATION:**
When you find a planet with Neecha Bhanga (debilitation cancellation), you MUST reframe it as a "Rags to Riches" story:

**Instead of saying:** "Your Sun is weak in Libra."
**You MUST say:** "Your Sun in Libra creates a powerful Neecha Bhanga Raja Yoga - you will face massive initial setbacks in career/authority, but this very failure becomes the platform for a legendary rise to exceptional status."

**MANDATORY SOURCE ANALYSIS:**
You MUST identify and explain the cancellation source for specific guidance:
- **Cancelled by Exalted Moon:** "Success comes through mother figures, property, or emotional intelligence"
- **Cancelled by Own Lord:** "Self-reliance and personal effort create the turnaround"
- **Cancelled by Exalted Jupiter:** "Wisdom, teaching, or spiritual guidance leads to recovery"
- **Cancelled by Conjunction:** "Partnership or collaboration becomes the key to transformation"

**Template:** "Your [Planet] debilitation is cancelled by [Source], meaning your rise comes specifically through [Source's domain]. The deeper the initial fall, the higher the eventual rise."

### M. THE "ASHTAKAVARGA GATEKEEPER" RULE (Transit Filtering)
You have access to `ashtakavarga_filter` data in each transit activation which shows house strength.

**CRITICAL PREDICTION FILTER:**
A planet transiting a traditionally good house (e.g., Jupiter in 11th) can FAIL to deliver if that house has low Ashtakavarga points.

**Mandatory Ashtakavarga Cross-Check:**
- **28+ points:** "Exceptional results - transit delivers outstanding benefits"
- **25-27 points:** "Good results - transit delivers as promised"
- **22-24 points:** "Moderate results - some benefits but also obstacles"
- **19-21 points:** "Weak results - transit struggles to deliver"
- **Below 19 points:** "Disappointing results - despite good planetary position, house lacks strength to manifest benefits"

**Template for Weak Ashtakavarga:**
"While [Planet] transits your [House]th house (traditionally beneficial), the Ashtakavarga shows only [X] points, indicating the house lacks strength to fully manifest the promised benefits. Expect [modified prediction] rather than [traditional expectation]."

**This prevents the #1 complaint: Promising a 'Great Year' that becomes mediocre.**

### N. THE "KARMIC TRIGGER" RULE (Progressive Nadi Transits)
You have access to `karmic_triggers` in transit activations which identifies exact conjunctions by slow-moving planets.

**CRITICAL TIMING PRECISION:**
When Saturn/Rahu/Jupiter transits within 0-3° of a natal planet, it "triggers" that planet's karma for 2.5 years (Saturn) or 1 year (Jupiter).

**Karmic Trigger Identification:**
- **Saturn Trigger:** Life-changing transformation, karmic lessons, permanent changes
- **Rahu Trigger:** Sudden elevation, foreign connections, unconventional breakthroughs  
- **Jupiter Trigger:** Dharmic expansion, wisdom gains, spiritual/educational milestones

**Mandatory Karmic Trigger Analysis:**
When you find a karmic trigger, you MUST predict the EXACT MONTH of the life-changing event:

**Template:** "[Transit Planet] will trigger your natal [Natal Planet] in [Exact Month Year], creating a [specific karmic event]. This is not just a transit - it's a karmic activation that will permanently alter your [life area] for the next [duration]."

**This enables month-level precision instead of general yearly windows.**

### O. THE "BHAVAT BHAVAM" RULE (House from House Analysis)
You have access to `bhavat_bhavam` data when questions involve relatives' fortunes.

**CRITICAL PERSPECTIVE SHIFT:**
When analyzing relatives' matters, you MUST shift the lagna perspective using Bhavat Bhavam principle.

**Relative House Mapping:**
- **Spouse (7th house):** Husband/Wife questions
- **Father (9th house):** Father-related questions  
- **Mother (4th house):** Mother-related questions
- **Children (5th house):** Son/Daughter questions
- **Siblings (3rd house):** Brother/Sister questions

**Topic Analysis from Relative's Perspective:**
- **Career/Business:** 10th house from relative's house
- **Health:** 6th house from relative's house
- **Wealth:** 2nd house from relative's house
- **Marriage:** 7th house from relative's house

**Mandatory Bhavat Bhavam Template:**
"For your [relative]'s [topic], I analyze the [calculated house]th house, which represents the [topic] from your [relative]'s perspective (the [offset]th house from the [relative house]th house)."

**Example:** "How is my husband's business?" → Analyze 4th house (10th from 7th)

### P. THE "DASHA CONFLICT" RULE (Vimshottari vs Yogini Nuances)
You have access to `dasha_conflicts` which identifies disagreements between Vimshottari and Yogini systems.

**CRITICAL NUANCE DETECTION:**
The most stunning predictions happen when Vimshottari and Yogini dashas disagree - this creates complex, nuanced outcomes.

**Conflict Types:**
- **Benefic Planet + Difficult Yogini:** Good results through stress/unconventional means
- **Malefic Planet + Auspicious Yogini:** Challenges lead to unexpected positive outcomes

**Mandatory Conflict Analysis:**
When dasha conflicts are detected, you MUST explain the nuanced prediction:

**Template:** "While your Vimshottari [Planet] dasha promises [expected result], the current [Yogini] Yogini indicates [contrasting influence]. This means [nuanced prediction combining both influences]."

**Examples:**
- Venus Dasha + Sankata Yogini: "Marriage/relationship through stressful circumstances or cultural gaps"
- Saturn Dasha + Siddha Yogini: "Hard work leads to unexpected recognition and success"

**This prevents generic predictions and adds sophisticated astrological depth.**

### Q. THE "PREDICTION MATRIX" RULE (High-Impact Convergences)
You have access to `prediction_matrix` which identifies exceptional periods where multiple rules intersect.

**CRITICAL CONVERGENCE DETECTION:**
When multiple astrological factors align, predictions become "stunning" in accuracy:

**Life Pivot Points:** Karmic Trigger + High Ashtakavarga + Maximum Dasha Significance
**Rags to Riches Activation:** Neecha Bhanga Planet + Current Dasha Alignment

**Mandatory Matrix Analysis:**
When high-impact convergences are detected, you MUST highlight them prominently:

**Template:** "EXCEPTIONAL CONVERGENCE DETECTED: [Type] with [Confidence Level] - [Specific Reason]. This is not ordinary astrology - multiple systems confirm a [life-changing outcome]."

## ETHICAL GUARDRAILS (STRICT COMPLIANCE)

## ETHICAL GUARDRAILS (STRICT COMPLIANCE)
- NO DEATH PREDICTIONS: Never predict the exact date of death or use words like "Fatal end." Use phrases like "Critical health period," "End of a cycle," or "Period of high physical vulnerability."
- NO MEDICAL DIAGNOSIS: Do not name specific diseases (e.g., "Cancer," "Diabetes") unless the user mentions them. Use astrological body parts (e.g., "Sensitive stomach," "blood-related issues").
- FEAR REDUCTION RULE: In the "Quick Answer" section, if D1 is negative but D9 is positive, you are FORBIDDEN from using words like "Critical," "Severe," "Danger," or "Crisis." Instead, use "Significant," "Important," "Sensitive," or "Transformative." Save the detailed risk analysis for the "Astrological Analysis" section only.
- EMPOWERMENT: Always end with a "Path Forward" or "Remedy" (e.g., meditation, charitable acts related to the afflicted planet).
- SIMPLE LANGUAGE IN QUICK ANSWER: Start with "Based on your birth chart and upcoming planetary movements:" Use everyday language like 'career opportunities', 'family matters', 'health concerns', 'financial gains'. Avoid astrological jargon, planet names without context, or technical terms.

## RESPONSE FORMAT STRUCTURE
For every user query, structure your response exactly as follows:

**Quick Answer**: MANDATORY FORMAT - You MUST follow this exact template:
"[CONTEXT SENTENCE about current period]. [HEADLINE PREDICTION with specific dates/events]. [PROTECTION SENTENCE mentioning D9/inner strength]. [ACTION SENTENCE with immediate step]."

**CRITICAL INSTRUCTION (THE "BUBBLE-UP" RULE):**
If your detailed analysis reveals ANY specific date, event, or warning, it MUST appear in the Quick Answer.
- ❌ FORBIDDEN: "You will have career changes soon." 
- ✅ REQUIRED: "You will see a major career shift between **March 15-April 20, 2025** due to Jupiter-Mars alignment."

**TEMPLATE ENFORCEMENT:**
Sentence 1 (Context): "The current [time period] indicates..."
Sentence 2 (Headline): "Specifically, expect [exact event] between [exact dates]..."
Sentence 3 (Protection): "However, your D9 Navamsa shows [strength/resilience]..."
Sentence 4 (Action): "Focus on [specific action] to [specific outcome]."

**VALIDATION CHECKLIST - Your Quick Answer FAILS if it lacks:**
□ Specific dates (month-year minimum)
□ Specific events (not vague terms like "changes")
□ D9/Navamsa strength mention
□ Actionable step

**Key Insights**: 3-4 bullet points highlighting the Strength (D9) and the Challenge (D1).
- **The Jaimini/Yogini Confirmation:** [MANDATORY bullet using specific terms like 'Aquarius Period' or 'Sankata Vibe' from the data]

**Detailed Analysis**:
- **The Promise (Chart Analysis):** Planetary positions and Yogas.
- **The Master Clock (Vimshottari):** What the main Dasha indicates.
- **Timing Synthesis (Multi-System):** [MANDATORY] You MUST cite the Chara Sign and Yogini Lord from the JSON here. Format: "This is confirmed by [Sign] Chara Dasha and [Lord] Yogini."
- **The Triple Perspective (Sudarshana):** [MANDATORY] Cross-check the event from Moon (Mind) and Sun (Soul).
- **The Micro-Timing (Yogini Confirmation):** Cross-check the Vimshottari prediction.
- **The Synthesis:** How D9 modifies the final outcome.

**Practical Guidance**: Actionable advice or cautions.

**Final Thoughts**: Summary and outlook.
"""
    
    # Class-level constants
    NAKSHATRA_NAMES = [
        'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
        'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
        'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
        'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
        'Uttara Bhadrapada', 'Revati'
    ]
    
    def __init__(self):
        self.static_cache = {}  # Cache static chart data
        self.dynamic_cache = {}  # Cache dynamic context data
    
    def build_synastry_context(self, native_birth_data: Dict, partner_birth_data: Dict, user_question: str = "", intent_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Build dual-chart context for partnership/compatibility analysis"""
        return {
            'analysis_type': 'synastry',
            'native': self.build_complete_context(native_birth_data, user_question, None, None, intent_result),
            'partner': self.build_complete_context(partner_birth_data, user_question, None, None, intent_result)
        }
    
    def build_annual_context(self, birth_data: Dict, target_year: int, user_question: str = "", intent_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Builds context with BOTH Birth Chart (Base) and Varshphal (Overlay)."""
        print(f"📅 Building Annual Context for Year: {target_year}")
        
        base_context = self.build_complete_context(birth_data, user_question, None, None, intent_result)
        
        chart_calc = ChartCalculator({})
        vp_calc = VarshphalCalculator(chart_calc)
        
        try:
            varshphal_data = vp_calc.calculate_varshphal(birth_data, target_year)
            
            base_context['analysis_type'] = 'annual_forecast'
            base_context['focus_year'] = target_year
            base_context['varshphal'] = {
                'muntha': varshphal_data['muntha'],
                'year_lord': varshphal_data['year_lord'],
                'mudda_dasha': varshphal_data['mudda_dasha']
            }
        except Exception as e:
            print(f"❌ Varshphal calculation failed: {e}")
            base_context['analysis_error'] = f"Annual calculation failed: {str(e)}"
            
        return base_context
    
    def build_prashna_context(self, user_location_data: Dict, user_question: str, category: str = 'general') -> Dict[str, Any]:
        """Build Horary (Prashna) context based on CURRENT time and User's Location."""
        from types import SimpleNamespace
        from calculators.panchang_calculator import PanchangCalculator
        import time
        import json
        
        prashna_start = time.time()
        print(f"\n{'='*80}")
        print(f"🔮 PRASHNA CONTEXT BUILDING STARTED")
        print(f"{'='*80}")
        print(f"Question: {user_question}")
        print(f"Category: {category}")
        print(f"Location: {user_location_data}")
        
        # 1. Get "Right Now" Data
        now = datetime.now()
        prashna_data = {
            'name': 'Prashna',
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M'),
            'latitude': user_location_data.get('latitude', 28.6139),
            'longitude': user_location_data.get('longitude', 77.2090),
            'timezone': user_location_data.get('timezone', 'Asia/Kolkata'),
            'place': user_location_data.get('place', 'Query Location')
        }
        print(f"\n⏰ Question Time: {prashna_data['date']} {prashna_data['time']}")
        
        # 2. Calculate the Chart for NOW
        chart_start = time.time()
        prashna_obj = SimpleNamespace(**prashna_data)
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(prashna_obj)
        chart_time = time.time() - chart_start
        print(f"✅ Chart calculation: {chart_time:.3f}s")
        
        # 3. Add Sign Names
        chart_data_enriched = self._add_sign_names_to_chart_copy(chart_data)
        print(f"✅ Chart enrichment complete")
        
        # 4. Run the Physics Engine (Tajik Aspects)
        tajik_start = time.time()
        prashna_calc = PrashnaCalculator(chart_data_enriched)
        print(f"\n🔬 TAJIK PHYSICS ENGINE INITIALIZED")
        print(f"Lagna: {chart_data_enriched.get('ascendant', 0):.2f}°")
        print(f"Lagna Lord: {prashna_calc.lagna_lord_name}")
        
        # 5. Pre-calculate multiple categories for Gemini to choose from
        print(f"\n📊 CALCULATING PRASHNA TOOLS...")
        categories_to_calc = ['job', 'love', 'health', 'wealth', 'lost_item', 'travel', 'property', 'education']
        prashna_tools = {}
        
        for cat in categories_to_calc:
            cat_start = time.time()
            analysis = prashna_calc.analyze_question(cat)
            cat_time = time.time() - cat_start
            prashna_tools[f'analysis_{cat}'] = analysis
            
            # Log focused category with full details
            if cat == category:
                print(f"\n⭐ FOCUSED CATEGORY: {cat.upper()}")
                print(f"   Verdict: {analysis['verdict']}")
                print(f"   Confidence: {analysis['confidence']}")
                print(f"   Summary: {analysis['summary']}")
                print(f"   Yoga: {analysis['analysis']['yoga']['name']} ({analysis['analysis']['yoga']['aspect']})")
                print(f"   Timing: {analysis['timing']['prediction']}")
                print(f"   Calculation time: {cat_time:.3f}s")
            else:
                print(f"   {cat}: {analysis['verdict']} ({cat_time:.3f}s)")
        
        tajik_time = time.time() - tajik_start
        print(f"\n✅ All Tajik calculations: {tajik_time:.3f}s")
        
        # 6. Get current panchang
        panchang_start = time.time()
        pc = PanchangCalculator()
        current_panchang = pc.calculate_birth_panchang(prashna_data)
        panchang_time = time.time() - panchang_start
        print(f"✅ Panchang calculation: {panchang_time:.3f}s")
        
        # 7. Build the Context Payload
        context = {
            'analysis_type': 'prashna',
            'prashna_focus_category': category,
            'question_time': prashna_data,
            'd1_chart': chart_data_enriched,
            'prashna_tools': prashna_tools,
            'current_panchang': current_panchang
        }
        
        total_time = time.time() - prashna_start
        context_size = len(json.dumps(context, default=str))
        
        print(f"\n✅ PRASHNA CONTEXT COMPLETE")
        print(f"Total time: {total_time:.3f}s")
        print(f"Context size: {context_size:,} characters")
        print(f"{'='*80}\n")
        
        return context
    
    def build_complete_context(self, birth_data: Dict, user_question: str = "", target_date: Optional[datetime] = None, requested_period: Optional[Dict] = None, intent_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Build complete astrological context for chat"""
        import time
        import json
        
        context_start_time = time.time()
        print(f"\n⏱️ CONTEXT PREPARATION STARTED")
        
        # Create birth hash for caching
        birth_hash = self._create_birth_hash(birth_data)
        
        # Get static data (cached)
        static_start_time = time.time()
        if birth_hash not in self.static_cache:
            print(f"   📊 Building static context (not cached)...")
            self.static_cache[birth_hash] = self._build_static_context(birth_data)
        else:
            print(f"   ✅ Using cached static context")
        static_context = self.static_cache[birth_hash]
        static_time = time.time() - static_start_time
        print(f"   Static context time: {static_time:.2f}s")
        
        # Dynamic Cache Key (birth_hash + current_date + requested_period + intent_result)
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        period_str = json.dumps(requested_period, sort_keys=True) if requested_period else "none"
        intent_str = json.dumps(intent_result, sort_keys=True) if intent_result else "none"
        dynamic_cache_key = f"{birth_hash}_{current_date_str}_{period_str}_{intent_str}"
        
        # Check Dynamic Cache
        dynamic_start_time = time.time()
        if dynamic_cache_key not in self.dynamic_cache:
            print(f"   🔄 Calculating fresh dynamic context...")
            self.dynamic_cache[dynamic_cache_key] = self._build_dynamic_context(birth_data, user_question, target_date, requested_period, intent_result)
        else:
            print(f"   ✅ Using cached dynamic context")
        
        dynamic_context = self.dynamic_cache[dynamic_cache_key]
        dynamic_time = time.time() - dynamic_start_time
        print(f"   Dynamic context time: {dynamic_time:.2f}s")
        
        total_context_time = time.time() - context_start_time
        print(f"⏱️ TOTAL CONTEXT PREPARATION TIME: {total_context_time:.2f}s")
        
        # Combine contexts and apply minification
        full_context = {
            **static_context,
            **dynamic_context
        }
        
        # Filter divisional charts based on intent router recommendations
        if intent_result and intent_result.get('divisional_charts'):
            requested_chart_codes = intent_result['divisional_charts']
            print(f"🎯 Filtering divisional charts for Gemini: {requested_chart_codes}")
            
            # Map codes to chart names
            chart_name_mapping = {
                'D3': 'd3_drekkana', 'D4': 'd4_chaturthamsa', 'D7': 'd7_saptamsa',
                'D9': 'd9_navamsa', 'D10': 'd10_dasamsa', 'D12': 'd12_dwadasamsa',
                'D16': 'd16_shodasamsa', 'D20': 'd20_vimsamsa', 'D24': 'd24_chaturvimsamsa',
                'D27': 'd27_nakshatramsa', 'D30': 'd30_trimsamsa', 'D40': 'd40_khavedamsa',
                'D45': 'd45_akshavedamsa', 'D60': 'd60_shashtiamsa'
            }
            
            # Filter to only requested charts
            filtered_divisional_charts = {}
            all_charts = full_context.get('divisional_charts', {})
            
            for code in requested_chart_codes:
                chart_name = chart_name_mapping.get(code)
                if chart_name and chart_name in all_charts:
                    filtered_divisional_charts[chart_name] = all_charts[chart_name]
                    print(f"   ✅ Including {code} ({chart_name})")
            
            # Always ensure D9 is included (required for analysis)
            if 'd9_navamsa' not in filtered_divisional_charts and 'd9_navamsa' in all_charts:
                filtered_divisional_charts['d9_navamsa'] = all_charts['d9_navamsa']
                print(f"   ✅ Added mandatory D9 Navamsa")
            
            full_context['divisional_charts'] = filtered_divisional_charts
            print(f"📊 Sending {len(filtered_divisional_charts)} divisional charts to Gemini")
        else:
            print(f"📊 No filtering - sending all {len(full_context.get('divisional_charts', {}))} divisional charts")
        
        # Apply minification before returning
        return self._minify_data(full_context)
    
    def _build_static_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build static chart context (cached per birth data)"""
        
        # Calculate birth chart using existing API endpoint logic
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        
        # Initialize analyzers
        planet_analyzer = PlanetAnalyzer(chart_data, birth_obj)
        divisional_calc = DivisionalChartCalculator(chart_data)
        chara_karaka_calc = CharaKarakaCalculator(chart_data)
        yogi_calc = YogiCalculator(chart_data)
        badhaka_calc = BadhakaCalculator(chart_data)
        friendship_calc = FriendshipCalculator()
        yoga_calc = YogaCalculator(birth_obj, chart_data)
        argala_calc = ArgalaCalculator(chart_data)
        
        # Initialize Ashtakavarga calculator
        from calculators.ashtakavarga import AshtakavargaCalculator
        ashtakavarga_calc = AshtakavargaCalculator(birth_data, chart_data)
        
        # Initialize Panchang calculator
        from calculators.panchang_calculator import PanchangCalculator
        panchang_calc = PanchangCalculator()
        panchang_calc.birth_data = birth_data
        
        # Advanced calculators
        planetary_war_calc = PlanetaryWarCalculator(chart_data)
        vargottama_calc = VargottamaCalculator(chart_data, {})
        neecha_bhanga_calc = NeechaBhangaCalculator(chart_data, {})
        pancha_mahapurusha_calc = PanchaMahapurushaCalculator(chart_data)
        indu_lagna_calc = InduLagnaCalculator(chart_data)
        
        # Extract and validate ascendant information
        ascendant_degree = chart_data.get('ascendant', 0)
        ascendant_sign_num = int(ascendant_degree / 30)
        ascendant_sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                               'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        ascendant_sign_name = ascendant_sign_names[ascendant_sign_num]
        
        # Validate ascendant calculation
        try:
            from utils.chart_validator import validate_ascendant_calculation
            validation = validate_ascendant_calculation(birth_data, ascendant_degree)
            ascendant_validation_note = f"Validation: {'PASSED' if validation['is_valid'] else 'FAILED'} - Difference: {validation['difference_degrees']:.4f}°"
        except Exception as e:
            ascendant_validation_note = f"Validation unavailable: {str(e)}"
        
        # Build comprehensive context
        context = {
            # Basic chart
            "birth_details": {
                "name": birth_data.get('name'),
                "date": birth_data.get('date'),
                "time": birth_data.get('time'),
                "place": birth_data.get('place', birth_data.get('name', 'Unknown')),
                "latitude": birth_data.get('latitude'),
                "longitude": birth_data.get('longitude')
            },
            
            # Validated ascendant information
            "ascendant_info": {
                "degree": ascendant_degree,
                "sign_number": ascendant_sign_num + 1,
                "sign_name": ascendant_sign_name,
                "exact_degree_in_sign": ascendant_degree % 30,
                "note": "This is the calculated Sidereal/Vedic ascendant using Swiss Ephemeris with Lahiri Ayanamsa",
                "validation": ascendant_validation_note,
                "formatted": f"{ascendant_sign_name} {ascendant_degree % 30:.2f}°"
            },
            
            "d1_chart": self._add_sign_names_to_chart_copy(chart_data)
        }
        
        # Calculate divisional charts with dignity analysis
        # Cache ALL standard charts to prevent stale cache issues when topics change
        requested_charts = [
            'D1', 'D3', 'D4', 'D7', 'D9', 'D10', 'D12', 'D16', 
            'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60'
        ]
        print(f"📊 Calculating ALL Divisional Charts for Cache (prevents topic-switch bugs)...")
        
        divisional_charts = {}
        
        # Calculate all divisional charts for robust caching
        for chart_code in requested_charts:
            if chart_code == 'D1':
                continue  # Already included as d1_chart
            
            try:
                chart_number = int(chart_code[1:])  # Extract number from D9, D10, etc.
                chart_data = divisional_calc.calculate_divisional_chart(chart_number)
                chart_data = self._add_sign_names_to_divisional_chart(chart_data)
                
                # Map to standard names
                chart_name_mapping = {
                    3: 'd3_drekkana',
                    4: 'd4_chaturthamsa', 
                    7: 'd7_saptamsa',
                    9: 'd9_navamsa',
                    10: 'd10_dasamsa',
                    12: 'd12_dwadasamsa',
                    16: 'd16_shodasamsa',
                    20: 'd20_vimsamsa',
                    24: 'd24_chaturvimsamsa',
                    27: 'd27_nakshatramsa',
                    30: 'd30_trimsamsa',
                    40: 'd40_khavedamsa',
                    45: 'd45_akshavedamsa',
                    60: 'd60_shashtiamsa'
                }
                
                chart_name = chart_name_mapping.get(chart_number, f'd{chart_number}')
                divisional_charts[chart_name] = chart_data
                print(f"   ✅ Calculated {chart_code} ({chart_name})")
                
            except Exception as e:
                print(f"   ❌ Failed to calculate {chart_code}: {e}")
                continue
        
        # Update advanced calculators with divisional charts
        vargottama_calc = VargottamaCalculator(chart_data, divisional_charts)
        neecha_bhanga_calc = NeechaBhangaCalculator(chart_data, divisional_charts)
        
        # Initialize D9 analyzer for separate analysis (use D9 from divisional_charts)
        d9_chart_for_analysis = divisional_charts.get('d9_navamsa')
        if d9_chart_for_analysis:
            d9_data_structure = d9_chart_for_analysis.get('divisional_chart', d9_chart_for_analysis)
            d9_planet_analyzer = PlanetAnalyzer(d9_data_structure, birth_obj)
        else:
            d9_planet_analyzer = None
        
        # Calculate Chara Karakas
        karaka_data = chara_karaka_calc.calculate_chara_karakas()
        
        # Calculate Jaimini Points
        # FIX: Extract the planet name string explicitly to prevent "unhashable type: dict" error
        atmakaraka_data = karaka_data['chara_karakas'].get('Atmakaraka', {})
        atmakaraka_planet = atmakaraka_data.get('planet')  # e.g., "Sun"
        
        # Initialize with the planet name string, not the dictionary object
        jaimini_calc = JaiminiPointCalculator(
            chart_data, 
            divisional_charts['d9_navamsa'], 
            atmakaraka_planet
        )
        
        # Run Full Jaimini Analysis
        jaimini_analyzer = JaiminiFullAnalyzer(chart_data, karaka_data)
        jaimini_report = jaimini_analyzer.get_jaimini_report()
        
        # Calculate Nadi Links
        nadi_calc = NadiLinkageCalculator(chart_data)
        nadi_links = nadi_calc.get_nadi_links()
        
        # Calculate Sudarshana Chakra (Triple Perspective)
        sudarshana_calc = SudarshanaChakraCalculator(chart_data)
        sudarshana_data = sudarshana_calc.get_sudarshana_view()
        
        context.update({
            # Key divisional charts
            "divisional_charts": divisional_charts,
            
            # Jaimini Points
            "jaimini_points": jaimini_calc.calculate_jaimini_points(),
            
            # Full Jaimini Analysis
            "jaimini_full_analysis": jaimini_report,
            
            # Nadi Links
            "nadi_links": nadi_links,
            
            # Sudarshana Chakra
            "sudarshana_chakra": sudarshana_data,
            
            # Planetary analysis
            "planetary_analysis": {},  # D1 (Rashi)
            "d9_planetary_analysis": {},  # D9 (Navamsa)
            
            # Special points
            "special_points": {
                "badhaka_lord": badhaka_calc.get_badhaka_lord(int(chart_data.get('ascendant', 0) / 30))
            },
            
            # Relationships
            "relationships": {
                "argala_analysis": argala_calc.calculate_argala_analysis()
            },
            
            # Yogas
            "yogas": yoga_calc.calculate_all_yogas(),
            
            # Chara Karakas
            "chara_karakas": karaka_data,
            
            # Advanced Analysis
            "advanced_analysis": {
                "planetary_wars": planetary_war_calc.get_war_summary(),
                "vargottama_positions": vargottama_calc.get_vargottama_summary(),
                "neecha_bhanga": neecha_bhanga_calc.get_neecha_bhanga_summary(),
                "pancha_mahapurusha": pancha_mahapurusha_calc.get_pancha_mahapurusha_summary()
            },
            
            # Ashtakavarga Analysis
            "ashtakavarga": {
                "d1_rashi": {
                    "sarvashtakavarga": ashtakavarga_calc.calculate_sarvashtakavarga(),
                    "bhinnashtakavarga": {
                        planet: ashtakavarga_calc.calculate_individual_ashtakavarga(planet)
                        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
                    },
                    "lagna_analysis": ashtakavarga_calc.get_ashtakavarga_analysis('lagna')
                },
                "d9_navamsa": self._calculate_d9_ashtakavarga(divisional_charts.get('d9_navamsa'), birth_data) if 'd9_navamsa' in divisional_charts else {}
            },
            
            # Birth Panchang
            "birth_panchang": panchang_calc.calculate_birth_panchang(birth_data),
            
            # Add InduLagna analysis to context
            **indu_lagna_calc.get_indu_lagna_analysis(),
            
            # Sniper Points (Critical for sudden events/health crises)
            "sniper_points": SniperPointsCalculator(
                chart_data,
                divisional_calc.calculate_divisional_chart(3),
                divisional_calc.calculate_divisional_chart(9)
            ).get_all_sniper_points()
        })
        
        # Add planetary analysis for both D1 and D9
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for planet in planets:
            # D1 Analysis (existing)
            try:
                full_analysis = planet_analyzer.analyze_planet(planet)
                context["planetary_analysis"][planet] = self._filter_planetary_analysis(full_analysis, chart_calc)
            except Exception as e:
                continue
            
            # D9 Analysis (new)
            if d9_planet_analyzer:
                try:
                    d9_full = d9_planet_analyzer.analyze_planet(planet)
                    context["d9_planetary_analysis"][planet] = self._filter_planetary_analysis(d9_full, chart_calc)
                except Exception as e:
                    continue
        
        return context
    
    def _filter_planetary_analysis(self, full_analysis: Dict, chart_calc: ChartCalculator) -> Dict:
        """Filter planetary analysis to keep only raw data, remove text bloat and friendship matrix redundancy"""
        return {
            'basic_info': {
                'planet': full_analysis['basic_info']['planet'],
                'sign': full_analysis['basic_info']['sign'],
                'sign_name': full_analysis['basic_info'].get('sign_name'),
                'house': full_analysis['basic_info']['house'],
                'degree': full_analysis['basic_info']['degree'],
                'longitude': full_analysis['basic_info']['longitude'],
                'nakshatra': full_analysis['basic_info']['nakshatra'],
                'nakshatra_pada': self._get_nakshatra_pada(full_analysis['basic_info']['longitude']),
                'avastha': chart_calc.get_baladi_avastha(
                    full_analysis['basic_info']['planet'],
                    full_analysis['basic_info']['degree'],
                    full_analysis['basic_info']['sign']
                )
            },
            'dignity_analysis': {
                'dignity': full_analysis['dignity_analysis']['dignity'],
                'functional_nature': full_analysis['dignity_analysis']['functional_nature'],
                'strength_multiplier': full_analysis['dignity_analysis']['strength_multiplier']
            },
            'strength_analysis': {
                'shadbala_rupas': full_analysis['strength_analysis']['shadbala_rupas'],
                'shadbala_points': full_analysis['strength_analysis']['shadbala_points'],
                'shadbala_grade': full_analysis['strength_analysis']['shadbala_grade']
            },
            'house_position_analysis': {
                'house_number': full_analysis['house_position_analysis']['house_number'],
                'house_types': full_analysis['house_position_analysis']['house_types']
            },
            'conjunctions': {
                'has_conjunctions': full_analysis['conjunctions']['has_conjunctions'],
                'conjunction_count': full_analysis['conjunctions']['conjunction_count'],
                'conjunctions': [{
                    'planet': c['planet'],
                    'type': c['type'],
                    'orb': c['orb']
                } for c in full_analysis['conjunctions']['conjunctions']]
            },
            'combustion_status': {
                'is_combust': full_analysis['combustion_status']['is_combust'],
                'is_cazimi': full_analysis['combustion_status']['is_cazimi'],
                'status': full_analysis['combustion_status']['status']
            },
            'retrograde_analysis': {
                'is_retrograde': full_analysis['retrograde_analysis']['is_retrograde']
            },
            'aspects_received': {
                'has_aspects': full_analysis['aspects_received']['has_aspects'],
                'aspect_count': full_analysis['aspects_received']['aspect_count'],
                'aspects': [{
                    'aspecting_planet': a['aspecting_planet'],
                    'aspect_type': a['aspect_type'],
                    'effect_score': a.get('effect_score', 0)
                } for a in full_analysis['aspects_received']['aspects']]
            },
            'overall_assessment': {
                'overall_strength_score': full_analysis['overall_assessment']['overall_strength_score'],
                'classical_grade': full_analysis['overall_assessment']['classical_grade']
            }
            # Removed friendship_analysis - massive redundancy eliminated
        }
    
    def _build_dynamic_context(self, birth_data: Dict, user_question: str, target_date: Optional[datetime], requested_period: Optional[Dict] = None, intent_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Build dynamic context based on question and date"""
        
        context = {}
        
        # Always include current dashas
        dasha_calc = DashaCalculator()
        context['current_dashas'] = dasha_calc.calculate_current_dashas(birth_data)
        
        # Add Maraka analysis for relatives (both Mahadasha and Antardasha)
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        asc_sign = int(chart_data['ascendant'] / 30)
        
        relatives = {
            "Mother": (asc_sign + 3) % 12,        # 4th
            "Father": (asc_sign + 8) % 12,        # 9th
            "Spouse": (asc_sign + 6) % 12,        # 7th
            "First_Child": self._get_child_lagna(asc_sign, 1, method='bhavat_bhavam'),
            "Second_Child": self._get_child_lagna(asc_sign, 2, method='bhavat_bhavam'),
            "Third_Child": self._get_child_lagna(asc_sign, 3, method='bhavat_bhavam')
        }
        
        # Get BOTH Dasha Lords
        md_planet = context['current_dashas'].get('mahadasha', {}).get('planet')
        ad_planet = context['current_dashas'].get('antardasha', {}).get('planet')
        
        # Analyze Maraka Status for BOTH
        context['current_dashas']['maraka_analysis'] = {}
        
        if md_planet:
            context['current_dashas']['maraka_analysis']['mahadasha_lord'] = {}
            for rel_name, rel_lagna in relatives.items():
                status = self._check_relative_maraka(md_planet, rel_lagna, chart_data)
                context['current_dashas']['maraka_analysis']['mahadasha_lord'][rel_name] = status

        if ad_planet:
            context['current_dashas']['maraka_analysis']['antardasha_lord'] = {}
            for rel_name, rel_lagna in relatives.items():
                status = self._check_relative_maraka(ad_planet, rel_lagna, chart_data)
                context['current_dashas']['maraka_analysis']['antardasha_lord'][rel_name] = status
        
        # Add Kalchakra dasha
        kalchakra_calc = KalachakraDashaCalculator()
        context['kalchakra_dasha'] = kalchakra_calc.calculate_kalchakra_dasha(birth_data)
        
        # Add Shoola Dasha (Jaimini longevity system)
        shoola_calc = ShoolaDashaCalculator(chart_data)
        context['shoola_dasha'] = shoola_calc.calculate_shoola_dasha(birth_data)
        
        # Add Yogini Dasha
        yogini_calc = YoginiDashaCalculator()
        moon_lon = chart_data['planets']['Moon']['longitude']
        context['yogini_dasha'] = yogini_calc.calculate_current_yogini(birth_data, moon_lon, target_date)
        
        # Add Dasha Conflict Analysis
        context['dasha_conflicts'] = self._analyze_dasha_conflicts(
            context['current_dashas'], 
            context['yogini_dasha']
        )
        
        # Add Chara Dasha (Jaimini) with DYNAMIC TARGETING
        try:
            from datetime import datetime
            birth_hash = self._create_birth_hash(birth_data)
            chart_data = self.static_cache[birth_hash]['d1_chart']
            chara_calc = CharaDashaCalculator(chart_data)
            dob_dt = datetime.strptime(birth_data['date'], '%Y-%m-%d')
            
            # Calculate full sequence
            full_chara_data = chara_calc.calculate_dasha(dob_dt)
            
            # Determine focus date (PRIORITY ORDER)
            focus_date = datetime.now()
            
            # PRIORITY 1: Intent Router (User's explicit question: "How is 2028?")
            if intent_result and intent_result.get('transit_request'):
                req = intent_result['transit_request']
                year = req.get('startYear') or req.get('start_year')
                if year:
                    focus_date = datetime(int(year), 1, 1)
            
            # PRIORITY 2: Explicit Target Date (Backend override/Annual mode)
            elif target_date:
                focus_date = target_date
            
            # PRIORITY 3: Gemini Requested Period (Tool call/Drill-down)
            elif requested_period:
                year = requested_period.get('startYear') or requested_period.get('start_year')
                if year:
                    focus_date = datetime(int(year), 1, 1)
            
            # Update is_current flag based on focus date
            for period in full_chara_data['periods']:
                p_start = datetime.strptime(period['start_date'], "%Y-%m-%d")
                p_end = datetime.strptime(period['end_date'], "%Y-%m-%d")
                period['is_current'] = p_start <= focus_date < p_end
                if period['is_current']:
                    period['note'] = "ACTIVE PERIOD for User Question"
            
            context['chara_dasha'] = full_chara_data
        except Exception as e:
            print(f"Chara Dasha calculation error: {e}")
        
        # Add specific date dashas if requested
        if target_date:
            context['target_date_dashas'] = dasha_calc.calculate_dashas_for_date(target_date, birth_data)
        
        # Add house lordship mapping
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        context['house_lordships'] = self._get_house_lordships(ascendant_sign)
        

        
        # Add transit data availability info with enhanced methodology
        current_year = datetime.now().year
        context['transit_data_availability'] = {
            "current_period": f"{current_year}-{current_year + 2} (2 years)",
            "available_range": "1900-2100",
            "can_request": True,
            "request_format": "Include JSON in your response: {\"requestType\": \"transitRequest\", \"startYear\": 2027, \"endYear\": 2028, \"specificMonths\": [\"January\", \"February\", \"March\"], \"detailed_dashas\": true}",
            "note": "You can request specific periods for detailed timing analysis using JSON format. Set detailed_dashas: true for Sookshma/Prana levels in short-term analysis",
            "comprehensive_analysis_methodology": {
                "principle": "Events manifest when dasha planets recreate natal relationships through transits, activating ALL connected house significations",
                "mandatory_analysis_steps": [
                    "1. Identify ALL houses involved: transit house + natal house + lordship houses of both planets",
                    "2. Combine ALL house significations to determine possible life areas affected", 
                    "3. Consider planetary natures (benefic/malefic) to determine positive/negative outcomes",
                    "4. CRITICAL: If a planet rules a Dusthana (6th, 8th, 12th) and transits that same house, interpret it as an intensification of that house's themes (e.g., health issues, transformation, expenses) rather than just 'benefic protection', even if the planet is natural benefic like Jupiter",
                    "5. Synthesize with dasha context for timing and intensity",
                    "6. Predict SPECIFIC life events, not general philosophical statements"
                ],
                "critical_transit_rules": {
                    "exit_rule": "CRITICAL TRANSIT RULE: If a Dasha Lord flagged as a 'Maraka' transits the 12th House (House of Exit) relative to the person, interpret this as 'Departure', 'Final Release', or 'End of Life Cycle', not just financial loss. This is often the trigger for death.",
                    "dasha_chhidra_rule": "TIMING RULE: If a malefic Antardasha (e.g., Mars-Rahu) is ending within 1-2 months, prioritize this 'Dasha Transition Period' as the most likely time for a critical event, even if later transits look stronger. The end of a malefic period is a classic trigger.",
                    "trigger_planet_rule": "TRIGGER RULE: In a Maraka period, the event often manifests when the Sun or Mars transits the 12th, 8th, or 1st house. Check the monthly transit data for these specific triggers."
                },
                "example_analysis": "Mars (lord 5th,10th, natal 2nd) transits 6th aspecting natal Sun (9th house, lord 1st): Houses involved = 1st,2nd,5th,6th,9th,10th = self,wealth,children,health,father,career. Possible events: health issues affecting father, career conflicts requiring courage, children's education expenses, property disputes, work-related stress affecting family finances.",
                "quick_answer_requirements": {
                    "must_include": "4-6 SPECIFIC life events with exact dates from transit periods - predict MORE events by combining house meanings",
                    "event_examples": "Property purchase opportunity, job promotion, relationship milestone, health checkup needed, father's travel for medical treatment, children's achievement ceremony, financial gain through work, legal matter resolution, vehicle purchase, educational course enrollment, long distance travel for work, family medical expenses, etc.",
                    "avoid_generic_terms": "Do NOT use vague terms like 'good period', 'challenges', 'growth'. Use specific event predictions.",
                    "house_synthesis_mandatory": "MUST combine multiple house meanings: 2nd+10th = career income, 4th+7th = home with spouse, 6th+9th = father's health + long travel = father's medical travel, 5th+12th = children's expenses, 3rd+9th = communication with father/mentor, 1st+6th = personal health from work, 6th+9th = service-related long travel, health issues requiring travel, father's work problems, etc.",
                    "comprehensive_event_prediction": "For each transit, predict events from ALL house combinations, not just obvious ones. Example: 6th+9th houses = father's health issues, father's work problems, long travel for medical treatment, legal issues with father, father's service to others, health expenses, work-related travel, educational travel, spiritual journey for healing, etc.",
                    "laymen_summary_mandatory": {
                        "purpose": "Quick Answer section MUST provide a clear, simple summary for non-astrologers",
                        "format": "Write as if explaining to someone who knows nothing about astrology",
                        "requirements": [
                            "Start with: 'Based on your birth chart and upcoming planetary movements:'",
                            "List 2-3 specific life events with exact date ranges",
                            "Place Key Insights section IMMEDIATELY after Quick Answer section",
                            "Use proper markdown: ## Key Insights (with double newline before content)",
                            "Format Key Insights as: ## Key Insights\n\n• Point 1\n• Point 2\n• Point 3"
                            "Explain WHY these events are likely (in simple terms)",
                            "End with: 'These predictions are based on the detailed astrological analysis below.'"
                        ],
                        "example_format": "Based on your birth chart and upcoming planetary movements: Between Jan 15-Mar 20, 2025, you're likely to have a property purchase opportunity through career advancement, as your career planet activates your wealth sector. From Feb 5-25, 2025, expect father's health to need attention with possible travel for treatment, creating family expenses. These predictions are based on the detailed astrological analysis below.",
                        "forbidden_in_summary": [
                            "Astrological jargon (houses, aspects, dashas, transits)",
                            "Planet names without context",
                            "Technical terms like 'benefic', 'malefic', 'conjunction'",
                            "Philosophical or spiritual language"
                        ],
                        "required_language": "Use everyday language: 'career opportunities', 'family matters', 'health concerns', 'financial gains', 'relationship changes', 'property matters', 'travel plans', etc."
                    },

                },
                "instruction": "MANDATORY: For ALL timing questions, request transit data using JSON format. After receiving transit data, provide comprehensive analysis using ALL house significations. RESPONSE MUST HAVE EXACTLY 6 MAIN SECTIONS IN THIS ORDER: 1) Quick Answer paragraph 2) ## Key Insights 3) ## Astrological Analysis (with sub-sections) 4) ## Nakshatra Insights 5) ## Timing & Guidance 6) ## Final Thoughts. Use standard markdown formatting only.",

            }
        }
        
        # Calculate transit data if requested by Intent Router or Gemini
        transit_request = None
        print(f"\n🔍 TRANSIT REQUEST DEBUG:")
        print(f"   intent_result type: {type(intent_result)}")
        print(f"   intent_result exists: {intent_result is not None}")
        print(f"   intent_result value: {intent_result}")
        if intent_result:
            print(f"   needs_transits: {intent_result.get('needs_transits')}")
            print(f"   transit_request exists: {'transit_request' in intent_result}")
            if 'transit_request' in intent_result:
                print(f"   transit_request: {intent_result['transit_request']}")
        print(f"   requested_period: {requested_period}")
        
        if intent_result and intent_result.get('needs_transits') and intent_result.get('transit_request'):
            transit_request = intent_result['transit_request']
            print(f"\n🎯 INTENT ROUTER REQUESTED TRANSITS: {transit_request['startYear']}-{transit_request['endYear']}")
        elif requested_period:
            transit_request = requested_period
            print(f"\n🎯 GEMINI REQUESTED TRANSITS: {requested_period}")
        else:
            print(f"\n❌ NO TRANSIT REQUEST DETECTED - intent_result: {intent_result}, requested_period: {requested_period}")
        
        
        print(f"\n🎯 FINAL TRANSIT REQUEST: {transit_request}")
        if transit_request:
            import time
            transit_start_time = time.time()
            
            # Handle both formats: Intent Router uses 'startYear', old format uses 'start_year'
            start_year = transit_request.get('startYear') or transit_request.get('start_year', current_year)
            end_year = transit_request.get('endYear') or transit_request.get('end_year', current_year + 2)
            year_range = end_year - start_year
            print(f"\n🎯 TRANSIT PERIOD: {start_year}-{end_year} ({year_range} years)")
            print(f"⏱️ TRANSIT CALCULATION STARTED")
            
            # Get static context for ashtakavarga data
            birth_hash = self._create_birth_hash(birth_data)
            static_context = self.static_cache.get(birth_hash, {})
            
            try:
                init_start = time.time()
                print(f"📊 Initializing RealTransitCalculator...")
                real_calc = RealTransitCalculator()
                init_time = time.time() - init_start
                print(f"   Initialization time: {init_time:.2f}s")
                
                aspects_start = time.time()
                print(f"🔍 Finding real aspects for birth data...")
                all_aspects = real_calc.find_real_aspects(birth_data)
                
                # OPTIMIZATION: Only process major transits (slow-moving planets)
                major_planets = ['Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Mars']
                aspects = [a for a in all_aspects if a['transit_planet'] in major_planets]
                
                aspects_time = time.time() - aspects_start
                print(f"   Found {len(all_aspects)} total aspects, filtered to {len(aspects)} major aspects in {aspects_time:.2f}s")
                print(f"   Optimization: Skipped fast movers (Sun, Moon, Mercury, Venus) to reduce compute load")
                
                transit_activations = []
                
                for i, aspect in enumerate(aspects):
                    # print(f"   Processing aspect {i+1}/{len(aspects)}: {aspect['transit_planet']} -> {aspect['natal_planet']}")
                    # print(f"     Aspect details: {aspect}")
                    try:
                        timeline = real_calc.calculate_aspect_timeline(aspect, start_year, year_range, birth_data)
                        # print(f"     Timeline periods found: {len(timeline)}")
                        
                        for j, period in enumerate(timeline):
                            # print(f"     Period {j+1}: {period['start_date']} to {period['end_date']}")
                            # print(f"       Transit house: {period.get('transit_house')}, Natal house: {period.get('natal_house')}")
                            # print(f"       Conjunct planets: {period.get('conjunct_natal_planets', [])}")
                            # print(f"       All aspects cast: {len(period.get('all_aspects_cast', []))} aspects")
                            
                            # Log each aspect cast
                            for aspect_cast in period.get('all_aspects_cast', []):
                                # print(f"         {aspect_cast['aspect_type']} -> House {aspect_cast['target_house']} (planets: {aspect_cast['target_planets']})")
                                pass
                            
                            # Add dasha correlation for this transit period
                            start_date_obj = datetime.strptime(period['start_date'], '%Y-%m-%d')
                            end_date_obj = datetime.strptime(period['end_date'], '%Y-%m-%d')
                            
                            # Get all 5 Vimshottari dasha levels for this period
                            dasha_periods = dasha_calc.get_dasha_periods_for_range(
                                birth_data, start_date_obj, end_date_obj
                            )
                            
                            # Get Chara Dasha periods for this range - use existing context data
                            chara_periods_for_range = []
                            try:
                                # Use the Chara Dasha data already calculated in the context
                                existing_chara = context.get('chara_dasha', {}).get('periods', [])
                                for chara_period in existing_chara:
                                    p_start = datetime.strptime(chara_period['start_date'], "%Y-%m-%d")
                                    p_end = datetime.strptime(chara_period['end_date'], "%Y-%m-%d")
                                    
                                    # Check if chara period overlaps with transit period
                                    if (p_start <= end_date_obj and p_end >= start_date_obj):
                                        chara_periods_for_range.append({
                                            'mahadasha_sign': chara_period.get('sign_name', chara_period.get('sign', 'Unknown')),
                                            'antardasha_sign': chara_period.get('sign', 'Unknown'),  # Use 'sign' key for antardasha
                                            'start_date': chara_period['start_date'],
                                            'end_date': chara_period['end_date'],
                                            'is_active': chara_period.get('is_current', False)
                                        })
                            except Exception as e:
                                print(f"DEBUG: Chara transit loop error: {e}")
                            
                            # Get Yogini Dasha periods for this range - calculate for specific transit period
                            yogini_periods_for_range = []
                            try:
                                yogini_calc = YoginiDashaCalculator()
                                moon_lon = chart_data['planets']['Moon']['longitude']
                                
                                # Calculate Yogini dasha for the specific transit start date
                                transit_yogini = yogini_calc.calculate_current_yogini(birth_data, moon_lon, start_date_obj)
                                if transit_yogini and 'antardasha' in transit_yogini:
                                    y_info = {
                                        'mahadasha': transit_yogini['mahadasha'].get('name', 'Unknown'),
                                        'antardasha': transit_yogini['antardasha'].get('name', 'Unknown'),
                                        'vibe': transit_yogini['antardasha'].get('vibe', 'Neutral'),
                                        'start_date': transit_yogini['antardasha'].get('start', ''),
                                        'end_date': transit_yogini['antardasha'].get('end', '')
                                    }
                                    yogini_periods_for_range.append(y_info)
                            except Exception as e:
                                print(f"DEBUG: Yogini transit loop error: {e}")
                            
                            # Analyze dasha significance
                            significance = self._analyze_dasha_transit_significance(
                                aspect['transit_planet'], aspect['natal_planet'], dasha_periods
                            )
                            
                            # Determine dasha levels based on intent or period length
                            dasha_levels = self._get_required_dasha_levels(intent_result, year_range)
                            
                            # Create comprehensive dasha data for this transit period
                            comprehensive_dasha_data = {
                                'vimshottari_periods': [
                                    self._filter_dasha_levels(d, dasha_levels) for d in dasha_periods
                                ],
                                'chara_periods': chara_periods_for_range,
                                'yogini_periods': yogini_periods_for_range,
                                'dasha_levels_included': dasha_levels
                            }
                            
                            transit_activations.append({
                                **period,
                                'transit_planet': aspect['transit_planet'],
                                'natal_planet': aspect['natal_planet'],
                                'aspect_number': aspect['aspect_number'],
                                'comprehensive_dashas': comprehensive_dasha_data,
                                'dasha_significance': significance,
                                'ashtakavarga_filter': self._apply_ashtakavarga_filter(
                                    period.get('transit_house'), 
                                    aspect['transit_planet'], 
                                    static_context.get('ashtakavarga', {})
                                ),
                                'karmic_triggers': self._detect_karmic_triggers(
                                    aspect['transit_planet'],
                                    period,
                                    chart_data
                                )
                            })
                    except Exception as aspect_error:
                        # print(f"     ❌ Error calculating timeline: {aspect_error}")
                        # import traceback
                        # traceback.print_exc()
                        pass
                        continue
                
                context['transit_activations'] = transit_activations
                
                # Add standalone dasha summary for entire period (covers quiet periods)
                context['requested_dasha_summary'] = self._build_standalone_dasha_summary(
                    birth_data, start_year, end_year, chart_data, context, intent_result, year_range
                )
                
                # Add logging to measure data size impact
                import json
                context_json = json.dumps(transit_activations)
                print(f"🔍 TRANSIT DATA SIZE: {len(context_json)} characters")
                print(f"🔍 TRANSIT COUNT: {len(transit_activations)}")
                
                # Sample first transit for inspection
                if transit_activations:
                    sample = transit_activations[0]
                    sample_json = json.dumps(sample)
                    print(f"🔍 SAMPLE TRANSIT SIZE: {len(sample_json)} characters")
                    
                    # Log comprehensive dasha structure
                    comp_dashas = sample.get('comprehensive_dashas', {})
                    vims_count = len(comp_dashas.get('vimshottari_periods', []))
                    chara_count = len(comp_dashas.get('chara_periods', []))
                    yogini_count = len(comp_dashas.get('yogini_periods', []))
                    
                    print(f"🔍 COMPREHENSIVE DASHA DATA:")
                    print(f"   Vimshottari periods: {vims_count}")
                    print(f"   Chara periods: {chara_count}")
                    print(f"   Yogini periods: {yogini_count}")
                    
                    if vims_count > 0:
                        sample_vims = comp_dashas['vimshottari_periods'][0]
                        print(f"   Sample Vimshottari: {sample_vims['mahadasha']}-{sample_vims['antardasha']}-{sample_vims['pratyantardasha']}")
                
                # Validate transit data integrity
                self._validate_transit_data(transit_activations)
                
                total_transit_time = time.time() - transit_start_time
                print(f"⏱️ TOTAL TRANSIT CALCULATION TIME: {total_transit_time:.2f}s")
                print(f"📊 TRANSIT DATA SENT TO GEMINI:")
                print(f"   Period: {start_year}-{end_year}")
                print(f"   Total activations: {len(transit_activations)}")
                print(f"   Enhanced with: All 5 Vimshottari levels + Chara Dasha + Yogini Dasha")
                for i, activation in enumerate(transit_activations[:3]):
                    comp_dashas = activation.get('comprehensive_dashas', {})
                    vims_count = len(comp_dashas.get('vimshottari_periods', []))
                    print(f"     {i+1}. {activation['transit_planet']} -> {activation['natal_planet']} ({activation['start_date']} to {activation['end_date']}) - {vims_count} dasha periods")
                if len(transit_activations) > 3:
                    print(f"     ... and {len(transit_activations) - 3} more")
                
                # Add comprehensive transit analysis instructions
                context['comprehensive_transit_analysis'] = {
                    "mandatory_approach": "For each transit activation, analyze ALL connected houses and predict MULTIPLE specific life events by combining house meanings",
                    "analysis_steps": [
                        "1. Identify transit planet's natal house + lordship houses",
                        "2. Identify natal planet's house + lordship houses", 
                        "3. Note the transit house where activation occurs",
                        "4. List ALL significations from each house (use complete house meanings provided)",
                        "5. Create event combinations by mixing house significations (e.g., 6th+9th = father's health + long travel = father's medical travel)",
                        "6. Apply planetary natures (benefic/malefic) for outcome polarity",
                        "7. Predict MINIMUM 3-5 specific events per transit activation, not just 1-2"
                    ],
                    "forbidden_approaches": [
                        "Generic philosophical statements about planetary influences",
                        "Vague terms like 'challenges', 'growth', 'good period'",
                        "Single house analysis ignoring lordships and connections",
                        "Theoretical discussions without specific event predictions"
                    ]
                }
                
                # Log transit data being sent
                # print(f"📊 TRANSIT DATA SENT TO GEMINI:")
                # print(f"   Period: {start_year}-{end_year}")
                # print(f"   Total activations: {len(transit_activations)}")
                # for i, activation in enumerate(transit_activations[:5]):
                #     print(f"     {i+1}. {activation['transit_planet']} -> {activation['natal_planet']} ({activation['start_date']} to {activation['end_date']})")
                # if len(transit_activations) > 5:
                #     print(f"     ... and {len(transit_activations) - 5} more")
                    
            except Exception as e:
                total_transit_time = time.time() - transit_start_time
                print(f"❌ Error calculating transit activations after {total_transit_time:.2f}s: {e}")
                import traceback
                traceback.print_exc()
                context['transit_activations'] = []
                
        # Add transit optimization flag
        if intent_result and intent_result.get('needs_transits'):
            context['transit_optimization'] = {
                "source": "intent_router",
                "pre_calculated": True,
                "eliminates_second_call": True
            }
        elif requested_period:
            context['transit_optimization'] = {
                "source": "gemini_request", 
                "pre_calculated": False,
                "second_call_required": True
            }
        
        # Add period focus instructions if this is for a specific period
        if hasattr(self, '_selected_period_data'):
            context['selected_period_focus'] = {
                "period_data": self._selected_period_data,
                "response_format": "event_prediction_focused",
                "instruction": "Focus ONLY on specific event predictions for the selected period. Use the response_format_for_period_predictions template. Skip general chart analysis sections."
            }
        
        # Add Bhavat Bhavam analysis if question involves relatives
        bhavat_bhavam_analysis = self._detect_and_analyze_bhavat_bhavam(user_question, context)
        if bhavat_bhavam_analysis:
            context['bhavat_bhavam'] = bhavat_bhavam_analysis
        
        # Add Prediction Matrix for high-impact overlaps
        context['prediction_matrix'] = self._build_prediction_matrix(context)
        
        # ESSENTIAL STRUCTURE ONLY
        context['RESPONSE_STRUCTURE_REQUIRED'] = {
            "sections_in_order": [
                "Quick Answer (paragraph)",
                "## Key Insights (with 'Jaimini/Yogini Confirmation' bullet)",
                "## Astrological Analysis",
                "   ### The Promise (Natal/Divisional)",
                "   ### Timing Synthesis (Vimshottari + Chara + Yogini) [MANDATORY: Cite the JSON signs/lords here]",
                "## Nakshatra Insights",
                "## Timing & Guidance",
                "## Final Thoughts"
            ],
            "formatting": "Standard markdown only: ## for headers, - for bullets",
            "critical_requirements": [
                "NEVER use HTML entities like &#39; or &amp; - use plain text apostrophes and ampersands",
                "ALL section headers MUST start with ## followed by space",
                "Use standard bullet points with - or • symbols only",
                "No special Unicode symbols like ◆ or ▸",
                "In Astrological Analysis section: start new paragraph for each major topic"
            ]
        }
        
        return context
    
    def set_selected_period(self, period_data: Dict):
        """Set selected period for focused predictions"""
        self._selected_period_data = period_data
    
    def _create_birth_hash(self, birth_data: Dict) -> str:
        """Create unique hash for birth data"""
        import hashlib
        birth_string = f"{birth_data.get('date')}_{birth_data.get('time')}_{birth_data.get('latitude')}_{birth_data.get('longitude')}"
        return hashlib.sha256(birth_string.encode()).hexdigest()
    
    def _analyze_dasha_transit_significance(self, transit_planet: str, natal_planet: str, dasha_periods: List[Dict]) -> str:
        """Analyze the significance of transit based on current dasha periods"""
        # print(f"         Analyzing significance for {transit_planet} -> {natal_planet}")
        
        if not dasha_periods:
            # print(f"         No dasha periods provided, returning moderate")
            return "moderate"
        
        max_significance = "moderate"
        
        # Check if transit planet or natal planet is in any dasha level
        for i, period in enumerate(dasha_periods):
            active_planets = [
                period.get('mahadasha'),
                period.get('antardasha'), 
                period.get('pratyantardasha'),
                period.get('sookshma'),
                period.get('prana')
            ]
            
            # print(f"         Period {i+1} active planets: {active_planets}")
            
            transit_in_dasha = transit_planet in active_planets
            natal_in_dasha = natal_planet in active_planets
            
            # print(f"         {transit_planet} in dasha: {transit_in_dasha}, {natal_planet} in dasha: {natal_in_dasha}")
            
            if transit_in_dasha and natal_in_dasha:
                # print(f"         Both planets in dasha - MAXIMUM significance")
                max_significance = "maximum"
            elif transit_in_dasha or natal_in_dasha:
                if max_significance != "maximum":
                    # print(f"         One planet in dasha - HIGH significance")
                    max_significance = "high"
        
        # print(f"         Final significance: {max_significance}")
        return max_significance
    
    def get_high_significance_periods(self, birth_data: Dict, years_ahead: int = 2, selected_year: int = None) -> List[Dict]:
        """Get high-significance event periods for the next specified years"""
        current_year = datetime.now().year
        
        if selected_year:
            start_year = selected_year
            end_year = selected_year + 1
        else:
            start_year = current_year
            end_year = current_year + years_ahead
        
        # Build context with transit data
        context = self.build_complete_context(
            birth_data, "", None, 
            requested_period={'start_year': start_year, 'end_year': end_year}
        )
        
        # Extract high-significance periods with enhanced data
        periods = []
        dasha_calc = DashaCalculator()
        
        for activation in context.get('transit_activations', []):
            if activation['dasha_significance'] in ['high', 'maximum']:
                # Get overlapping dasha periods for this specific transit period
                start_date_obj = datetime.strptime(activation['start_date'], '%Y-%m-%d')
                end_date_obj = datetime.strptime(activation['end_date'], '%Y-%m-%d')
                
                overlapping_dashas = dasha_calc.get_dasha_periods_for_range(
                    birth_data, start_date_obj, end_date_obj
                )
                
                # Get the actual aspect number from the activation data (already calculated correctly)
                aspect_number = activation.get('aspect_number')
                transit_house = activation.get('transit_house')
                natal_house = activation.get('natal_house')
                
                # Validate aspect against planet's capabilities
                transit_planet = activation['transit_planet']
                valid_aspects = {
                    'Sun': [1, 7],
                    'Moon': [1, 7], 
                    'Mars': [1, 4, 7, 8],
                    'Mercury': [1, 7],
                    'Jupiter': [1, 5, 7, 9],
                    'Venus': [1, 7],
                    'Saturn': [1, 3, 7, 10],
                    'Rahu': [1, 5, 7, 9],
                    'Ketu': [1, 5, 7, 9]
                }
                
                # Only include if aspect is valid for this planet
                if aspect_number not in valid_aspects.get(transit_planet, []):
                    continue
                
                # Find which dasha the transit planet will be in during this period
                transit_planet_dashas = []
                for dasha in overlapping_dashas:
                    if dasha['mahadasha'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Mahadasha',
                            'planet': transit_planet,
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                    elif dasha['antardasha'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Antardasha', 
                            'planet': transit_planet,
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                    elif dasha['pratyantardasha'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Pratyantardasha',
                            'planet': transit_planet, 
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                    elif dasha['sookshma'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Sookshma',
                            'planet': transit_planet,
                            'start_date': dasha['start_date'], 
                            'end_date': dasha['end_date']
                        })
                    elif dasha['prana'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Prana',
                            'planet': transit_planet,
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                

                
                # Calculate life areas affected by this transit
                life_areas = self._calculate_life_areas(
                    activation['transit_planet'],
                    activation['natal_planet'], 
                    transit_house,
                    natal_house,
                    context.get('house_lordships', {})
                )
                
                # Convert heavy dasha objects to lightweight strings for period data
                lightweight_transit_planet_dashas = [
                    f"{p.get('type', '')}: {p.get('planet', '')}"
                    for p in transit_planet_dashas
                ]
                
                periods.append({
                    'id': f"{activation['transit_planet']}-{activation['natal_planet']}-{activation['start_date']}",
                    'label': f"{activation['start_date']} to {activation['end_date']}: {activation['transit_planet']}→{activation['natal_planet']}",
                    'start_date': activation['start_date'],
                    'end_date': activation['end_date'],
                    'transit_planet': activation['transit_planet'],
                    'natal_planet': activation['natal_planet'],
                    'significance': activation['dasha_significance'],
                    'life_areas': life_areas,
                    'period_data': {
                        **activation,
                        'aspect_number': aspect_number,
                        # Remove 'overlapping_dashas' entirely (redundant)
                        'transit_planet_dashas': lightweight_transit_planet_dashas,
                        'life_areas': life_areas
                    }
                })
                

        
        # Sort by date
        periods.sort(key=lambda x: x['start_date'])
        

        return periods[:20]  # Return top 20 periods
    
    def _get_nakshatra_pada(self, longitude):
        """Calculate Nakshatra Pada from longitude with high precision"""
        # Normalize longitude (handle 360.0 or >360 cases)
        longitude = longitude % 360
        
        # Exact division: 360 degrees / 27 nakshatras
        nakshatra_span = 360 / 27
        
        # Calculate position (0-based index)
        absolute_position = longitude / nakshatra_span
        
        # Get nakshatra index (0 to 26)
        nakshatra_index = int(absolute_position)
        
        # Calculate pada (1 to 4)
        fractional_part = absolute_position - nakshatra_index
        pada = int(fractional_part * 4) + 1
        
        # Safety check for index bounds
        if nakshatra_index >= 27:
            nakshatra_index = 26
            
        return {
            'nakshatra': self.NAKSHATRA_NAMES[nakshatra_index],
            'nakshatra_id': nakshatra_index + 1,
            'pada': pada,
            'formatted': f"{self.NAKSHATRA_NAMES[nakshatra_index]} ({pada})"
        }
    
    def _calculate_d9_ashtakavarga(self, d9_chart, birth_data):
        """Calculate Ashtakavarga for D9 Navamsa chart"""
        try:
            from calculators.ashtakavarga import AshtakavargaCalculator
            # Access the correct nested structure
            d9_chart_data = d9_chart.get('divisional_chart', d9_chart)
            d9_ashtakavarga_calc = AshtakavargaCalculator(birth_data, d9_chart_data)
            
            return {
                "sarvashtakavarga": d9_ashtakavarga_calc.calculate_sarvashtakavarga(),
                "bhinnashtakavarga": {
                    planet: d9_ashtakavarga_calc.calculate_individual_ashtakavarga(planet)
                    for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
                },
                "navamsa_analysis": d9_ashtakavarga_calc.get_ashtakavarga_analysis('navamsa')
            }
        except Exception as e:
            return {"error": f"D9 Ashtakavarga calculation failed: {e}"}
    
    def _get_house_lordships(self, ascendant_sign: int) -> Dict:
        """Get house lordships based on ascendant sign"""
        # Sign lordships (0=Aries, 1=Taurus, etc.)
        sign_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        
        house_lordships = {}
        for house in range(1, 13):
            # Calculate which sign rules this house
            house_sign = (ascendant_sign + house - 1) % 12
            lord = sign_lords[house_sign]
            
            if lord not in house_lordships:
                house_lordships[lord] = []
            house_lordships[lord].append(house)
        
        return house_lordships
    
    def _calculate_life_areas(self, transit_planet: str, natal_planet: str, transit_house: int, natal_house: int, house_lordships: Dict) -> List[str]:
        """Calculate life areas affected by transit activation"""
        
        # Comprehensive house signification mapping for all life areas
        house_areas = {
            1: ["Self", "Health", "Personality", "Appearance", "Vitality", "Leadership", "Independence", "Identity"],
            2: ["Wealth", "Family", "Speech", "Values", "Food", "Savings", "Possessions", "Financial Security", "Material Assets"],
            3: ["Siblings", "Courage", "Communication", "Short Travel", "Efforts", "Neighbors", "Writing", "Media", "Skills", "Hobbies"],
            4: ["Home", "Mother", "Education", "Property", "Vehicles", "Happiness", "Domestic Life", "Real Estate", "Comfort", "Inner Peace"],
            5: ["Children", "Creativity", "Intelligence", "Romance", "Speculation", "Entertainment", "Sports", "Gambling", "Love Affairs", "Pregnancy"],
            6: ["Health Issues", "Enemies", "Service", "Daily Work", "Debts", "Diseases", "Employment", "Medical Treatment", "Competition", "Pets"],
            7: ["Marriage", "Partnerships", "Business", "Spouse", "Public Relations", "Contracts", "Legal Matters", "Cooperation", "Negotiations"],
            8: ["Transformation", "Occult", "Longevity", "Inheritance", "Accidents", "Research", "Surgery", "Insurance", "Taxes", "Joint Resources"],
            9: ["Fortune", "Dharma", "Higher Learning", "Father", "Spirituality", "Long Travel", "Philosophy", "Religion", "Foreign Countries", "Teaching"],
            10: ["Career", "Reputation", "Authority", "Public Image", "Government", "Profession", "Status", "Recognition", "Boss", "Fame"],
            11: ["Gains", "Friends", "Aspirations", "Elder Siblings", "Income", "Fulfillment", "Social Networks", "Hopes", "Profits", "Community"],
            12: ["Losses", "Spirituality", "Foreign Lands", "Expenses", "Isolation", "Moksha", "Hospitals", "Meditation", "Charity", "Liberation"]
        }
        
        affected_houses = set()
        
        # Add primary houses
        if transit_house:
            affected_houses.add(transit_house)
        if natal_house:
            affected_houses.add(natal_house)
        
        # Add lordship houses
        if transit_planet in house_lordships:
            affected_houses.update(house_lordships[transit_planet])
        if natal_planet in house_lordships:
            affected_houses.update(house_lordships[natal_planet])
        
        # Convert to life areas and prioritize
        life_areas = []
        priority_houses = [transit_house, natal_house] if transit_house and natal_house else []
        
        # Add primary areas first (top 2 from each priority house)
        for house in priority_houses:
            if house in house_areas:
                house_significations = house_areas[house][:2]  # Take top 2 significations
                for area in house_significations:
                    if area not in life_areas:
                        life_areas.append(area)
        
        # Add secondary areas from lordships (1 from each house)
        for house in sorted(affected_houses):
            if house in house_areas and house not in priority_houses:
                area = house_areas[house][0]  # Take primary signification
                if area not in life_areas and len(life_areas) < 4:
                    life_areas.append(area)
        
        return life_areas[:4]  # Return top 4 most relevant areas
    
    def _add_sign_names_to_chart_copy(self, chart_data: Dict) -> Dict:
        """Create copy of chart data with sign names to prevent Gemini 0-based vs 1-based indexing confusion"""
        import copy
        chart_copy = copy.deepcopy(chart_data)
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Add sign names to all planets in d1_chart
        if 'planets' in chart_copy:
            for planet_name, planet_data in chart_copy['planets'].items():
                if 'sign' in planet_data:
                    sign_index = planet_data['sign']
                    planet_data['sign_name'] = sign_names[sign_index]
        
        # Add sign names to bhav_chalit chart
        if 'bhav_chalit' in chart_copy and 'planets' in chart_copy['bhav_chalit']:
            for planet_name, planet_data in chart_copy['bhav_chalit']['planets'].items():
                if 'sign' in planet_data:
                    sign_index = planet_data['sign']
                    planet_data['sign_name'] = sign_names[sign_index]
        
        return chart_copy
    
    def _get_child_lagna(self, ascendant_sign: int, child_number: int, method: str = 'bhavat_bhavam') -> int:
        """
        Calculates the Derived Lagna (Sign Index 0-11) for the Nth child.
        
        Args:
            ascendant_sign (int): Native's Lagna (0=Aries, 1=Taurus...)
            child_number (int): 1 for 1st child, 2 for 2nd, etc.
            method (str): 
                'sibling' = 5th, 7th, 9th (Standard Parashara - 3rd from previous)
                'bhavat_bhavam' = 5th, 9th, 1st (Deep Reflection - 5th from previous)
        
        Returns:
            int: The sign index (0-11) for that child's Lagna.
        """
        if child_number < 1: return ascendant_sign
        
        # 1. Start at the 5th House (Index + 4)
        # This is the universal house for the 1st Child
        child_lagna = (ascendant_sign + 4) % 12
        
        # 2. If looking for 2nd, 3rd, etc., apply the jump
        if child_number > 1:
            if method == 'sibling':
                # Jump 3 houses (Index + 2) for each subsequent child
                # 1st=5th, 2nd=7th, 3rd=9th...
                jump = 2
            else:
                # 'bhavat_bhavam' (The one that worked for the death prediction)
                # Jump 5 houses (Index + 4) for each subsequent child
                # 1st=5th, 2nd=9th, 3rd=1st...
                jump = 4
                
            # Apply jumps
            total_jump = jump * (child_number - 1)
            child_lagna = (child_lagna + total_jump) % 12
            
        return child_lagna
    
    def _check_relative_maraka(self, planet_name: str, relative_lagna_sign: int, chart_data: Dict) -> str:
        """
        Checks if a planet is a Maraka (Killer) for a relative's Lagna.
        """
        if planet_name not in chart_data['planets']: return "Neutral"
        
        # 1. Calculate Maraka Houses (2nd and 7th from Relative)
        maraka_house_2 = (relative_lagna_sign + 1) % 12  # 2nd Sign
        maraka_house_7 = (relative_lagna_sign + 6) % 12  # 7th Sign
        
        # 2. Get Lordships of the Planet
        sign_lords = {0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 
                      5: 'Mercury', 6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 
                      10: 'Saturn', 11: 'Jupiter'}
        
        is_maraka_lord = False
        if sign_lords[maraka_house_2] == planet_name: is_maraka_lord = True
        if sign_lords[maraka_house_7] == planet_name: is_maraka_lord = True
        
        # 3. Check Placement (Is it sitting in 2nd or 7th?)
        p_sign = chart_data['planets'][planet_name]['sign']
        is_in_maraka_house = (p_sign == maraka_house_2) or (p_sign == maraka_house_7)
        
        if is_maraka_lord and is_in_maraka_house:
            return "Strong Maraka Influence (Requires Remedies)"
        elif is_maraka_lord:
            return "Maraka Activation (Sensitivity)"
        elif is_in_maraka_house:
            return "Maraka Placement (Stress)"
            
        return "Safe"
    
    def _minify_data(self, data: Any) -> Any:
        """Recursively rounds floats to 2 decimal places to save tokens"""
        if isinstance(data, dict):
            return {k: self._minify_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._minify_data(i) for i in data]
        elif isinstance(data, float):
            return round(data, 2)
        return data
    
    def _apply_ashtakavarga_filter(self, transit_house: int, transit_planet: str, ashtakavarga_data: Dict) -> Dict:
        """Apply Ashtakavarga filter to transit predictions"""
        if not transit_house or not ashtakavarga_data:
            return {'status': 'no_data', 'strength': 'unknown'}
        
        # Get Bhinnashtakavarga for the transiting planet
        d1_ashtakavarga = ashtakavarga_data.get('d1_rashi', {})
        bhinnashtakavarga = d1_ashtakavarga.get('bhinnashtakavarga', {})
        planet_ashtakavarga = bhinnashtakavarga.get(transit_planet, {})
        
        if not planet_ashtakavarga:
            return {'status': 'no_planet_data', 'strength': 'unknown'}
        
        # Get points for the transit house (convert 1-12 to 0-11 indexing)
        house_index = (transit_house - 1) % 12
        house_points = planet_ashtakavarga.get('house_points', [])
        
        if len(house_points) <= house_index:
            return {'status': 'no_house_data', 'strength': 'unknown'}
        
        points = house_points[house_index]
        
        # Ashtakavarga strength classification (Classical thresholds)
        if points >= 28:
            strength = 'excellent'
            prediction_modifier = 'exceptional_results'
        elif points >= 25:
            strength = 'good'
            prediction_modifier = 'good_results'
        elif points >= 22:
            strength = 'moderate'
            prediction_modifier = 'mixed_results'
        elif points >= 19:
            strength = 'weak'
            prediction_modifier = 'limited_results'
        else:
            strength = 'very_weak'
            prediction_modifier = 'disappointing_results'
        
        # Special handling for malefic transits with high points
        malefic_planets = ['Saturn', 'Mars', 'Rahu', 'Ketu']
        if transit_planet in malefic_planets and points >= 28:
            prediction_modifier = 'challenging_but_manageable'
            strength = f'{strength}_with_support'
        
        return {
            'status': 'calculated',
            'points': points,
            'strength': strength,
            'prediction_modifier': prediction_modifier,
            'house': transit_house,
            'planet': transit_planet,
            'interpretation': self._get_ashtakavarga_interpretation(points, transit_planet, transit_house)
        }
    
    def _get_ashtakavarga_interpretation(self, points: int, planet: str, house: int) -> str:
        """Get interpretation based on Ashtakavarga points"""
        if points >= 28:
            return f"{planet} transit through {house}th house has exceptional Ashtakavarga support ({points} points) - expect outstanding results"
        elif points >= 25:
            return f"{planet} transit through {house}th house has good Ashtakavarga support ({points} points) - expect positive outcomes"
        elif points >= 22:
            return f"{planet} transit through {house}th house has moderate Ashtakavarga support ({points} points) - expect mixed results"
        elif points >= 19:
            return f"{planet} transit through {house}th house has weak Ashtakavarga support ({points} points) - results may be limited"
        else:
            return f"{planet} transit through {house}th house has very weak Ashtakavarga support ({points} points) - expect disappointing results despite good planetary position"
    
    def _detect_karmic_triggers(self, transit_planet: str, period: Dict, natal_chart: Dict) -> Dict:
        """Detect karmic triggers when slow planets conjunct natal planets within 3 degrees"""
        if transit_planet not in ['Saturn', 'Rahu', 'Jupiter']:
            return {'status': 'not_applicable', 'triggers': []}
        
        if not natal_chart.get('planets'):
            return {'status': 'no_natal_data', 'triggers': []}
        
        triggers = []
        conjunct_planets = period.get('conjunct_natal_planets', [])
        
        # For each conjunct planet, check if it's a precise karmic trigger
        for natal_planet in conjunct_planets:
            if natal_planet not in natal_chart['planets']:
                continue
            
            # Get natal planet longitude
            natal_longitude = natal_chart['planets'][natal_planet].get('longitude', 0)
            
            # Calculate trigger details
            trigger_type = self._get_karmic_trigger_type(transit_planet, natal_planet)
            duration = self._get_karmic_duration(transit_planet)
            
            triggers.append({
                'transit_planet': transit_planet,
                'natal_planet': natal_planet,
                'natal_longitude': natal_longitude,
                'trigger_type': trigger_type,
                'duration': duration,
                'karmic_theme': self._get_karmic_theme(transit_planet, natal_planet),
                'life_area': self._get_karmic_life_area(natal_planet),
                'intensity': 'maximum',  # Exact conjunctions are always maximum intensity
                'prediction_template': f"{transit_planet} triggers natal {natal_planet} - {trigger_type}"
            })
        
        return {
            'status': 'calculated' if triggers else 'no_triggers',
            'total_triggers': len(triggers),
            'triggers': triggers,
            'interpretation': self._get_karmic_trigger_interpretation(triggers, period)
        }
    
    def _get_karmic_trigger_type(self, transit_planet: str, natal_planet: str) -> str:
        """Get karmic trigger type based on planet combination"""
        combinations = {
            ('Saturn', 'Sun'): 'Authority Transformation',
            ('Saturn', 'Moon'): 'Emotional Maturation', 
            ('Saturn', 'Mars'): 'Disciplined Action',
            ('Saturn', 'Mercury'): 'Communication Mastery',
            ('Saturn', 'Jupiter'): 'Wisdom Through Hardship',
            ('Saturn', 'Venus'): 'Relationship Restructuring',
            ('Rahu', 'Sun'): 'Sudden Fame/Recognition',
            ('Rahu', 'Moon'): 'Mental Breakthrough',
            ('Rahu', 'Mars'): 'Explosive Action',
            ('Rahu', 'Mercury'): 'Innovative Communication',
            ('Rahu', 'Jupiter'): 'Unconventional Wisdom',
            ('Rahu', 'Venus'): 'Unusual Relationships',
            ('Jupiter', 'Sun'): 'Leadership Expansion',
            ('Jupiter', 'Moon'): 'Emotional Wisdom',
            ('Jupiter', 'Mars'): 'Righteous Action',
            ('Jupiter', 'Mercury'): 'Teaching/Learning',
            ('Jupiter', 'Venus'): 'Dharmic Relationships',
            ('Jupiter', 'Saturn'): 'Structured Growth'
        }
        return combinations.get((transit_planet, natal_planet), f'{transit_planet}-{natal_planet} Activation')
    
    def _get_karmic_duration(self, transit_planet: str) -> str:
        """Get karmic effect duration"""
        durations = {
            'Saturn': '2.5 years',
            'Rahu': '1.5 years', 
            'Jupiter': '1 year'
        }
        return durations.get(transit_planet, '1 year')
    
    def _get_karmic_theme(self, transit_planet: str, natal_planet: str) -> str:
        """Get karmic theme for the trigger"""
        themes = {
            'Saturn': 'Discipline, Responsibility, Permanent Change',
            'Rahu': 'Innovation, Foreign Elements, Sudden Elevation',
            'Jupiter': 'Expansion, Wisdom, Dharmic Growth'
        }
        return themes.get(transit_planet, 'Transformation')
    
    def _get_karmic_life_area(self, natal_planet: str) -> str:
        """Get life area affected by natal planet"""
        areas = {
            'Sun': 'Authority, Career, Father, Government',
            'Moon': 'Mind, Emotions, Mother, Public',
            'Mars': 'Energy, Property, Siblings, Competition',
            'Mercury': 'Communication, Business, Learning, Travel',
            'Jupiter': 'Wisdom, Children, Spirituality, Teaching',
            'Venus': 'Relationships, Wealth, Arts, Luxury',
            'Saturn': 'Service, Discipline, Longevity, Karma'
        }
        return areas.get(natal_planet, 'General Life')
    
    def _get_karmic_trigger_interpretation(self, triggers: List[Dict], period: Dict) -> str:
        """Get interpretation for karmic triggers"""
        if not triggers:
            return 'No karmic triggers detected in this period'
        
        if len(triggers) == 1:
            trigger = triggers[0]
            return f"KARMIC TRIGGER: {trigger['transit_planet']} activates your natal {trigger['natal_planet']}, creating {trigger['trigger_type']} lasting {trigger['duration']}"
        else:
            return f"MULTIPLE KARMIC TRIGGERS: {len(triggers)} planetary activations create a major life transformation period lasting up to 2.5 years"
    
    def _detect_and_analyze_bhavat_bhavam(self, user_question: str, base_context: Dict) -> Optional[Dict]:
        """Detect if question involves relatives and apply Bhavat Bhavam analysis"""
        if not user_question:
            return None
        
        question_lower = user_question.lower()
        
        # Relative detection patterns
        relative_patterns = {
            'spouse': {'keywords': ['husband', 'wife', 'spouse', 'partner'], 'house': 7},
            'father': {'keywords': ['father', 'dad', 'papa'], 'house': 9},
            'mother': {'keywords': ['mother', 'mom', 'mama'], 'house': 4},
            'children': {'keywords': ['child', 'son', 'daughter', 'kids'], 'house': 5},
            'siblings': {'keywords': ['brother', 'sister', 'sibling'], 'house': 3},
            'elder_sibling': {'keywords': ['elder brother', 'elder sister'], 'house': 11}
        }
        
        # Topic detection patterns
        topic_patterns = {
            'career': {'keywords': ['job', 'career', 'business', 'work', 'profession'], 'house_offset': 9},  # 10th from relative
            'health': {'keywords': ['health', 'illness', 'disease', 'medical'], 'house_offset': 5},  # 6th from relative
            'wealth': {'keywords': ['money', 'wealth', 'income', 'finance'], 'house_offset': 1},  # 2nd from relative
            'marriage': {'keywords': ['marriage', 'wedding', 'relationship'], 'house_offset': 6},  # 7th from relative
            'children': {'keywords': ['children', 'pregnancy', 'kids'], 'house_offset': 4}  # 5th from relative
        }
        
        detected_relative = None
        detected_topic = None
        
        # Detect relative
        for relative, data in relative_patterns.items():
            if any(keyword in question_lower for keyword in data['keywords']):
                detected_relative = {'name': relative, 'house': data['house']}
                break
        
        # Detect topic
        for topic, data in topic_patterns.items():
            if any(keyword in question_lower for keyword in data['keywords']):
                detected_topic = {'name': topic, 'house_offset': data['house_offset']}
                break
        
        if not detected_relative or not detected_topic:
            return None
        
        # Calculate Bhavat Bhavam house
        relative_house = detected_relative['house']
        topic_offset = detected_topic['house_offset']
        bhavat_bhavam_house = ((relative_house + topic_offset - 2) % 12) + 1
        
        return {
            'detected': True,
            'relative': detected_relative['name'],
            'relative_house': relative_house,
            'topic': detected_topic['name'],
            'topic_offset': topic_offset,
            'bhavat_bhavam_house': bhavat_bhavam_house,
            'analysis_instruction': f"Analyze {detected_topic['name']} of {detected_relative['name']} by examining the {bhavat_bhavam_house}th house (which is the {topic_offset}th house from the {relative_house}th house)",
            'example': f"Question about {detected_relative['name']}'s {detected_topic['name']} → Look at {bhavat_bhavam_house}th house"
        }
    
    def _analyze_dasha_conflicts(self, vimshottari_dasha: Dict, yogini_dasha: Dict) -> Dict:
        """Analyze conflicts between Vimshottari and Yogini dasha systems"""
        if not vimshottari_dasha or not yogini_dasha:
            return {'status': 'insufficient_data', 'conflicts': []}
        
        # Get current periods
        vims_maha = vimshottari_dasha.get('mahadasha', {}).get('planet')
        vims_antar = vimshottari_dasha.get('antardasha', {}).get('planet')
        yogini_period = yogini_dasha.get('current_yogini', {}).get('yogini')
        
        if not vims_maha or not yogini_period:
            return {'status': 'missing_periods', 'conflicts': []}
        
        conflicts = []
        
        # Analyze Mahadasha vs Yogini conflict
        maha_conflict = self._detect_planet_yogini_conflict(vims_maha, yogini_period)
        if maha_conflict:
            conflicts.append({
                'type': 'mahadasha_yogini',
                'vimshottari_planet': vims_maha,
                'yogini_period': yogini_period,
                'conflict_nature': maha_conflict,
                'prediction_impact': self._get_conflict_prediction_impact(vims_maha, yogini_period, maha_conflict)
            })
        
        # Analyze Antardasha vs Yogini conflict
        if vims_antar:
            antar_conflict = self._detect_planet_yogini_conflict(vims_antar, yogini_period)
            if antar_conflict:
                conflicts.append({
                    'type': 'antardasha_yogini',
                    'vimshottari_planet': vims_antar,
                    'yogini_period': yogini_period,
                    'conflict_nature': antar_conflict,
                    'prediction_impact': self._get_conflict_prediction_impact(vims_antar, yogini_period, antar_conflict)
                })
        
        return {
            'status': 'analyzed',
            'total_conflicts': len(conflicts),
            'conflicts': conflicts,
            'interpretation': self._get_dasha_conflict_interpretation(conflicts)
        }
    
    def _detect_planet_yogini_conflict(self, planet: str, yogini: str) -> Optional[str]:
        """Detect conflict between planet nature and yogini nature"""
        # Planet natures
        benefic_planets = ['Jupiter', 'Venus', 'Moon', 'Mercury']
        malefic_planets = ['Saturn', 'Mars', 'Rahu', 'Ketu', 'Sun']
        
        # Yogini natures
        auspicious_yoginis = ['Siddha', 'Mangala', 'Pingala']
        inauspicious_yoginis = ['Sankata', 'Ulka', 'Dhanya']
        
        planet_nature = 'benefic' if planet in benefic_planets else 'malefic'
        yogini_nature = 'auspicious' if yogini in auspicious_yoginis else 'inauspicious'
        
        # Detect conflicts
        if planet_nature == 'benefic' and yogini_nature == 'inauspicious':
            return 'benefic_planet_difficult_yogini'
        elif planet_nature == 'malefic' and yogini_nature == 'auspicious':
            return 'malefic_planet_auspicious_yogini'
        
        return None
    
    def _get_conflict_prediction_impact(self, planet: str, yogini: str, conflict_type: str) -> str:
        """Get prediction impact based on dasha conflict"""
        impacts = {
            'benefic_planet_difficult_yogini': f"{planet} promises positive results, but {yogini} Yogini indicates stress, delays, or unconventional circumstances",
            'malefic_planet_auspicious_yogini': f"{planet} indicates challenges, but {yogini} Yogini suggests unexpected support or positive outcomes through difficulties"
        }
        return impacts.get(conflict_type, f"Complex interaction between {planet} and {yogini}")
    
    def _get_dasha_conflict_interpretation(self, conflicts: List[Dict]) -> str:
        """Get overall interpretation of dasha conflicts"""
        if not conflicts:
            return "Vimshottari and Yogini dashas are aligned - expect straightforward manifestation of planetary results"
        
        if len(conflicts) == 1:
            conflict = conflicts[0]
            return f"DASHA CONFLICT DETECTED: {conflict['prediction_impact']} - expect nuanced results with mixed outcomes"
        else:
            return f"MULTIPLE DASHA CONFLICTS: {len(conflicts)} conflicting influences create a complex period requiring careful navigation"
    
    def _build_prediction_matrix(self, context: Dict) -> Dict:
        """Flags moments where multiple rules intersect for 'Stunning' accuracy"""
        triggers = []
        
        # Logic: If Karmic Trigger AND High Ashtakavarga AND Dasha Alignment
        for activation in context.get('transit_activations', []):
            karmic_status = activation.get('karmic_triggers', {}).get('status')
            ashtaka_points = activation.get('ashtakavarga_filter', {}).get('points', 0)
            dasha_significance = activation.get('dasha_significance')
            
            if (karmic_status == 'calculated' and 
                ashtaka_points > 28 and
                dasha_significance == 'maximum'):
                
                triggers.append({
                    "type": "LIFE_PIVOT_POINT",
                    "period": f"{activation['start_date']} to {activation['end_date']}",
                    "reason": "Karmic trigger aligned with powerful dasha and house strength",
                    "planets": f"{activation['transit_planet']} -> {activation['natal_planet']}",
                    "confidence": "95%_certainty"
                })
        
        # Check for Neecha Bhanga + Dasha alignment
        neecha_data = context.get('advanced_analysis', {}).get('neecha_bhanga', {})
        current_dasha = context.get('current_dashas', {})
        
        if neecha_data.get('neecha_bhanga_planets'):
            maha_planet = current_dasha.get('mahadasha', {}).get('planet')
            for nb_planet in neecha_data['neecha_bhanga_planets']:
                if nb_planet['planet'] == maha_planet and nb_planet['strength'] in ['Complete Cancellation', 'Strong Cancellation']:
                    triggers.append({
                        "type": "RAGS_TO_RICHES_ACTIVATION",
                        "period": "Current Mahadasha Period",
                        "reason": f"Neecha Bhanga {nb_planet['planet']} dasha creates legendary transformation",
                        "confidence": "90%_certainty"
                    })
        
        return {
            'total_triggers': len(triggers),
            'high_impact_periods': triggers,
            'interpretation': self._get_matrix_interpretation(triggers)
        }
    
    def _get_matrix_interpretation(self, triggers: List[Dict]) -> str:
        """Get interpretation for prediction matrix"""
        if not triggers:
            return "Standard astrological influences - no exceptional convergences detected"
        
        if len(triggers) == 1:
            trigger = triggers[0]
            return f"EXCEPTIONAL PERIOD DETECTED: {trigger['type']} with {trigger['confidence']} - {trigger['reason']}"
        else:
            return f"MULTIPLE LIFE-CHANGING CONVERGENCES: {len(triggers)} exceptional periods create a transformational phase"
    
    def _get_required_dasha_levels(self, intent_result: Optional[Dict], year_range: int) -> List[str]:
        """Determine required dasha levels based on intent and time period"""
        # Check if intent router specifically requests detailed dashas
        if intent_result and intent_result.get('detailed_dashas'):
            return ['mahadasha', 'antardasha', 'pratyantardasha', 'sookshma', 'prana']
        
        # Smart selection based on time period
        if year_range <= 1:  # 1 year or less - include all levels
            return ['mahadasha', 'antardasha', 'pratyantardasha', 'sookshma', 'prana']
        elif year_range <= 3:  # 2-3 years - first 4 levels
            return ['mahadasha', 'antardasha', 'pratyantardasha', 'sookshma']
        else:  # 4+ years - first 3 levels only
            return ['mahadasha', 'antardasha', 'pratyantardasha']
    
    def _filter_dasha_levels(self, dasha_period: Dict, required_levels: List[str]) -> Dict:
        """Filter dasha period to include only required levels"""
        filtered = {
            'start_date': dasha_period.get('start_date', ''),
            'end_date': dasha_period.get('end_date', '')
        }
        
        for level in required_levels:
            filtered[level] = dasha_period.get(level, '')
        
        return filtered
    
    def _build_standalone_dasha_summary(self, birth_data: Dict, start_year: int, end_year: int, chart_data: Dict, context: Dict, intent_result: Optional[Dict] = None, year_range: int = 1) -> Dict:
        """Build complete dasha summary for entire period to cover quiet periods"""
        from datetime import datetime, timedelta
        
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        
        dasha_calc = DashaCalculator()
        
        # Get all Vimshottari periods for the range
        vimshottari_periods = dasha_calc.get_dasha_periods_for_range(birth_data, start_date, end_date)
        
        # Determine required dasha levels
        dasha_levels = self._get_required_dasha_levels(intent_result, year_range)
        
        # DIRECT EXTRACTION - Chara Dasha
        chara_periods = []
        all_chara = context.get('chara_dasha', {}).get('periods', [])
        for p in all_chara:
            p_start = datetime.strptime(p['start_date'], "%Y-%m-%d")
            p_end = datetime.strptime(p['end_date'], "%Y-%m-%d")
            if p_start <= end_date and p_end >= start_date:
                chara_periods.append({
                    'mahadasha_sign': p.get('sign_name', p.get('sign', 'Unknown')),
                    'antardasha_sign': p.get('sign', 'Unknown'),  # Use 'sign' key for antardasha
                    'start_date': p['start_date'],
                    'end_date': p['end_date'],
                    'is_active': p.get('is_current', False)
                })
        
        # DIRECT CALCULATION - Yogini Dasha for requested period start
        yogini_periods = []
        try:
            yogini_calc = YoginiDashaCalculator()
            moon_lon = chart_data.get('planets', {}).get('Moon', {}).get('longitude', 0)
            y_data = yogini_calc.calculate_current_yogini(birth_data, moon_lon, start_date)
            if y_data and 'antardasha' in y_data:
                yogini_periods.append({
                    'mahadasha': y_data['mahadasha'].get('name', 'Unknown'),
                    'antardasha': y_data['antardasha'].get('name', 'Unknown'),
                    'vibe': y_data['antardasha'].get('vibe', 'Neutral'),
                    'start_date': y_data['antardasha'].get('start', ''),
                    'end_date': y_data['antardasha'].get('end', '')
                })
        except Exception as e:
            print(f"DEBUG: Yogini summary calculation error: {e}")
        
        return {
            'period_coverage': f"{start_year}-{end_year}",
            'vimshottari_sequence': [
                self._filter_dasha_levels(d, dasha_levels) for d in vimshottari_periods
            ],
            'chara_sequence': chara_periods,
            'yogini_sequence': yogini_periods,
            'dasha_levels_included': dasha_levels,
            'note': f'Dasha coverage with {len(dasha_levels)} levels for {year_range}-year period'
        }
    
    def _validate_transit_data(self, transit_activations: List[Dict]) -> None:
        """Ensure essential data is preserved after optimization"""
        for activation in transit_activations:
            # Check required fields exist
            assert 'transit_planet' in activation, "Missing transit_planet"
            assert 'natal_planet' in activation, "Missing natal_planet"
            assert 'start_date' in activation, "Missing start_date"
            assert 'end_date' in activation, "Missing end_date"
            assert 'comprehensive_dashas' in activation, "Missing comprehensive_dashas"
            
            # Check comprehensive_dashas structure
            dashas = activation['comprehensive_dashas']
            assert isinstance(dashas, dict), "comprehensive_dashas should be dict"
            assert 'vimshottari_periods' in dashas, "Missing vimshottari_periods"
            assert 'chara_periods' in dashas, "Missing chara_periods"
            assert 'yogini_periods' in dashas, "Missing yogini_periods"
            
            # Validate Vimshottari structure
            if dashas['vimshottari_periods']:
                vims_period = dashas['vimshottari_periods'][0]
                assert 'mahadasha' in vims_period, "Missing mahadasha in vimshottari_periods"
                assert 'antardasha' in vims_period, "Missing antardasha in vimshottari_periods"
        
        print(f"✅ Transit data validation passed for {len(transit_activations)} transits")
        return None
    
    def _add_sign_names_to_divisional_chart(self, divisional_chart: Dict) -> Dict:
        """Add sign names to divisional chart to prevent Gemini indexing confusion"""
        import copy
        chart_copy = copy.deepcopy(divisional_chart)
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Add sign names to divisional chart planets
        if 'divisional_chart' in chart_copy and 'planets' in chart_copy['divisional_chart']:
            for planet_name, planet_data in chart_copy['divisional_chart']['planets'].items():
                if 'sign' in planet_data:
                    sign_index = planet_data['sign']
                    planet_data['sign_name'] = sign_names[sign_index]
        
        return chart_copy