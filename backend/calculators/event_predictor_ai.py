from datetime import datetime, timedelta
from typing import Dict, List, Any
from types import SimpleNamespace
import calendar
import json
import asyncio
import os
import google.generativeai as genai
from calculators.divisional_chart_calculator import DivisionalChartCalculator

class EventPredictor:
    """
    AI-Powered Event Predictor using Grand Synthesis method.
    Implements "Natal-Transit Resonance" logic with Age-Based Context (Desha Kala Patra).
    """
    
    def __init__(self, chart_calculator, real_transit_calculator, dasha_calculator, ashtakavarga_calculator_cls):
        self.chart_calc = chart_calculator
        self.transit_calc = real_transit_calculator
        self.dasha_calc = dasha_calculator
        self.ashtakavarga_cls = ashtakavarga_calculator_cls
        
        # Initialize Gemini safely
        self.model = None
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                print("✅ EventPredictor using Gemini 2.0 Flash Exp")
            except:
                try:
                    self.model = genai.GenerativeModel('models/gemini-2.0-flash-exp')
                    print("✅ EventPredictor using Gemini 2.0 Flash Exp (fallback)")
                except:
                    self.model = genai.GenerativeModel('gemini-pro')
                    print("✅ EventPredictor using Gemini Pro (fallback)")

    async def predict_yearly_events(self, birth_data: Dict, year: int) -> Dict[str, Any]:
        try:
            print("\n" + "#"*100)
            print(f"🎯 STARTING YEARLY EVENT PREDICTION FOR {year}")
            print("#"*100)
            
            # Calculate Age for Context
            birth_year = int(birth_data['date'].split('-')[0])
            current_age = year - birth_year
            print(f"📊 Birth year: {birth_year}, Current age: {current_age}")
            
            print("\n🔄 Preparing yearly data...")
            raw_data = self._prepare_yearly_data(birth_data, year)
            print(f"✅ Yearly data prepared (length: {len(raw_data)} chars)")
            
            # Pass Age to prompt generator for Desha Kala Patra logic
            print("\n🔄 Creating prediction prompt...")
            prompt = self._create_prediction_prompt(raw_data, year, current_age)
            print(f"✅ Prompt created (length: {len(prompt)} chars)")
            
            print("\n🔄 Calling Gemini API...")
            ai_response = await self._get_ai_prediction_async(prompt)
            print(f"✅ Gemini API returned response")
            
            final_response = {"year": year, "status": "success", **ai_response}
            print(f"\n✅ PREDICTION COMPLETE FOR {year}")
            print(f"   - Final response keys: {list(final_response.keys())}")
            print("#"*100 + "\n")
            
            return final_response
            
        except Exception as e:
            print(f"\n❌ ERROR IN predict_yearly_events:")
            print(f"   - Error type: {type(e).__name__}")
            print(f"   - Error message: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"year": year, "status": "error", "error": str(e), "macro_trends": [], "monthly_predictions": []}

    def _prepare_yearly_data(self, birth_data: Dict, year: int) -> str:
        """
        Use ChatContextBuilder to get comprehensive astrological context.
        Returns JSON string with all divisional charts, yogas, dashas, and transits.
        """
        print(f"\n📊 Using ChatContextBuilder for comprehensive {year} analysis...")
        
        from chat.chat_context_builder import ChatContextBuilder
        
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (datetime, timedelta)):
                    return obj.isoformat()
                return super().default(obj)
        
        context_builder = ChatContextBuilder()
        
        # Get complete annual context with all divisional charts, yogas, dashas, transits
        full_context = context_builder.build_annual_context(
            birth_data=birth_data,
            target_year=year,
            user_question=f"Predict life events for {year}",
            intent_result={'mode': 'annual_prediction', 'category': 'yearly_events'}
        )
        
        print(f"✅ ChatContextBuilder returned context with keys: {list(full_context.keys())}")
        
        # Return as formatted JSON string for Gemini with datetime handling
        return json.dumps(full_context, indent=2, cls=DateTimeEncoder)

    def _create_prediction_prompt(self, raw_data: str, year: int, age: int) -> str:
        """
        Dynamically adjusts prompt based on User Age (Desha Kala Patra).
        """
        
        # 1. Determine Life Stage Context
        if age < 23:
            life_stage_context = """
**USER PROFILE: STUDENT (Education Phase)**
**INTERPRETATION RULES (Desha Kala Patra):**
* **5th House:** Primary signification is **EXAMS, GRADES, INTELLIGENCE**. (Secondary: Romance).
* **4th House:** Signifies **SCHOOLING/COLLEGE STUDY**.
* **9th House:** Signifies **HIGHER EDUCATION/ADMISSION/COLLEGE**.
* **11th House:** Signifies **EXAM RESULTS/ADMISSION SUCCESS**. (Not Salary).
* **6th House:** Signifies **COMPETITIVE EXAMS** (Not Divorce/Job).
* **10th House:** Signifies **ACADEMIC RANK/ACHIEVEMENT**.
"""
        elif age > 60:
            life_stage_context = """
**USER PROFILE: SENIOR (Retirement/Moksha Phase)**
**INTERPRETATION RULES (Desha Kala Patra):**
* **5th House:** Signifies **GRANDCHILDREN/MANTRA/DEVOTION**.
* **6th House:** Signifies **HEALTH ISSUES/DISEASE**.
* **1st House:** Signifies **VITALITY/LONGEVITY**.
* **12th House:** Signifies **HOSPITALS/SPIRITUAL RETREAT**.
"""
        else:
            life_stage_context = """
**USER PROFILE: CAREER/ADULT (Artha/Kama Phase)**
**INTERPRETATION RULES (Desha Kala Patra):**
* **5th House:** Signifies **CHILDREN/SPECULATION**.
* **10th House:** Signifies **CAREER/PROMOTION**.
* **11th House:** Signifies **WEALTH/SALARY/GAINS**.
* **7th House:** Signifies **MARRIAGE/BUSINESS PARTNERS**.
"""

        return f"""
You are an expert Vedic Astrologer predicting life events for {year}.

**COMPLETE ASTROLOGICAL CONTEXT (JSON FORMAT):**
The following JSON contains comprehensive astrological data:
- static_context: Birth chart (D1), all divisional charts (D2-D60 with house positions), yogas, planetary strengths, chara karakas, ashtakavarga
- dynamic_context: Year-long dasha periods, monthly transits, significant periods

**HOW TO USE THE DATA:**
- For career events: Check D1 10th house + D10 (dashamsha) + D24 (education)
- For marriage events: Check D1 7th house + D9 (navamsa) + D7 (children)
- For property events: Check D1 4th house + D4 (chaturthamsha) + D2 (wealth)
- For health events: Check D1 6th/8th house + D30 (trimshamsha diseases)
- For education events: Check D1 5th house + D24 (chaturvimshamsha)
- Use yogas, planetary strengths, and ashtakavarga scores for timing and intensity

```json
{raw_data}
```

{life_stage_context}

### CRITICAL: IDENTIFY THE YEAR'S TURNING POINT
**Before generating macro trends, identify the single most important planetary shift of the year.**

**Instructions:**
1. Scan all 12 months for major outer planet transits (Jupiter, Saturn, Rahu/Ketu sign changes)
2. Identify which transit will have the BIGGEST impact on the native's life
3. Label it as "The Year's Turning Point" in your macro_trends
4. Explain WHY the user's life will feel fundamentally different before and after this date
5. Specify the exact month when this pivot occurs

**Example Format:**
"The Year's Turning Point: Month 6 - Jupiter enters Cancer (your 10th house). Before this, career feels stagnant. After this, sudden promotions and recognition become possible. This is the dividing line of your year."

### CRITICAL RULES:

**1. CALENDAR INTEGRITY (MANDATORY):**
You MUST return exactly 12 month objects in the monthly_predictions array, covering January (month_id: 1) through December (month_id: 12).
- DO NOT skip months
- DO NOT re-index based on events found
- If a month has no major triggers, use the current Dasha Lords to predict routine maintenance activities for that month
- Each month_id must correspond to its calendar month (1=January, 2=February, etc.)

**2. DASHA INVIOLABILITY (FORBIDDEN TO VIOLATE):**
You are STRICTLY FORBIDDEN from changing the Dasha dates provided in the current_dashas context.
- DO NOT hallucinate dasha shifts
- DO NOT invent new dasha periods
- Use the provided dasha calendar EXACTLY as given
- If no trigger is found for the current PD Lord, look for triggers involving the AD Lord or MD Lord

**3. LORDSHIP INTEGRATION (ALWAYS STATE):**
ALWAYS state the planet's Natal Lordship before explaining its transit effect.
- Format: "Mercury as your 3rd and 12th lord transits..."
- This helps users understand WHY a planet matters to them

**4. DEBILITATION RULE:**
When a planet is debilitated in transit, do NOT just predict 'bad results'.
- Predict that the specific life department ruled by that planet (lordship) will require heavy effort or resource drain
- Example: "Sun (2L) debilitated in 4th = Spending wealth on home repairs" NOT just "Stress at home"

**5. DASHA LORD BRIDGE RULE (CRITICAL):**
When a Dasha Lord (MD/AD/PD) is hit by a transit, you MUST check ALL houses it rules natally, even if it sits in a different house.
- Example: If Transit Ketu crosses Natal Saturn, and Saturn rules the 7th house, you MUST predict effects on marriage/partnerships, NOT just the house Saturn sits in.
- Format: "Transit Ketu crosses Natal Saturn (7L, 8L) in 2nd house = Karmic obstruction affecting partnerships (7H) and sudden breaks in wealth (2H/8H)."

**6. VEDIC HOUSE COUNTING RULE (FORBIDDEN):**
NEVER count houses from a planetary cluster. This is Western astrology logic.
- ALWAYS count houses from the Lagna (Ascendant) or the current Dasha Lord's sign.
- WRONG: "Sun is 2nd from your natal cluster"
- RIGHT: "Sun transits 10th house from Lagna"

### 1. THE "RULE OF THREE" MANIFESTATION SPECTRUM
For every High/Medium intensity event, you MUST provide comprehensive scenarios in the `possible_manifestations` array:
- Include scenarios covering Material/Artha (Career, Money, Property, Status)
- Include scenarios covering Internal/Emotional (Family, Peace of Mind, Relationships)
- Include scenarios covering Physical/Obstacle (Health, Energy, Challenges)
- Add additional scenarios for ANY other house combinations you identify

**The goal is MAXIMUM COMPREHENSIVE coverage. Generate AS MANY manifestations as the house activations allow - there is NO UPPER LIMIT.**

### 2. THE MULTI-HOUSE SYNTHESIS ENGINE (BPHS LOGIC)
A planet is a bridge. You are forbidden from predicting an isolated house result.
**Synthesis Formula:** [Planet] = ([Natal Lordship Houses] + [Transit House]) acting upon [Aspected Houses].
- *Example:* Jupiter (rules 6, 9) transiting 1H and aspecting 5H.
- *Synthesis:* "Your luck/fortune (9L) and service (6L) physically manifest (1H) to bring gains through creativity or children (5H aspect)."

### 3. STRICT ACTIVATION HIERARCHY (DASHA-FIRST LOGIC)
The Sun is only a timer; the Dasha Lords are the source.
1. **PRIMARY TRIGGER:** The PD Lord moves into a new house or hits a Natal Planet.
2. **SECONDARY TRIGGER:** A fast planet (Sun/Mars/Venus) conjuncts or aspects the current MD, AD, or PD Lord.
3. **TERTIARY TRIGGER (Resonance):** A fast planet transits the house RULED by the MD, AD, or PD Lord.
4. **THE "STUN" TRIGGER:** Transit Saturn and Transit Jupiter both aspect the same house (Double Transit). If this occurs, intensity is ALWAYS 'High'.
5. **THE DOUBLE-ASPECT RULE:** If two slow planets (Saturn/Jupiter/Rahu/Ketu) aspect the same house, that house is 'ON FIRE'. Predict a major life milestone for that house, even if the Sun is not there.

### 4. THE "STUNNING" PATTERN DETECTOR (Year-Independent)
You are required to scan the provided transit data for the following "High-Certainty" patterns:

* **Pattern 1: The Double Transit (The King Maker):** Check if Transit Saturn and Transit Jupiter both aspect the same house at any point in the year.
    - If found: Label this as a "Major Financial/Life Anchor" in macro_trends.
    - Explain that when the two heavyweights focus on one house, concrete results are GUARANTEED.
* **Pattern 2: The Nodal Return/Reverse:** Check if Transit Rahu or Ketu is conjunct your Natal Rahu or Ketu.
    - This marks a "Karmic Reset" year.
* **Pattern 3: Dasha Chhidra (The Threshold):** If the user is in the last 3 months of a Mahadasha or Antardasha, predict "Sudden Endings/New Chapters."

### 5. MANDATORY TRIGGER REASONING (No Guesswork)
For every month, you must justify the prediction using this exact chain:
1. **Source:** Identify the Dasha Lord (MD/AD/PD) acting this month.
2. **Timer:** Identify the fast planet (Sun/Mars/etc.) hitting that Dasha Lord or its ruled house.
3. **Constraint:** You are strictly forbidden from giving Saturn an 11th aspect. Saturn aspects only 3, 7, and 10.
4. **Validation:** In the trigger_logic field, you MUST write the formula:
   "Trigger = [Fast Planet] @ [Degree] hitting [Natal/Dasha Point]."

**CRITICAL SUN DEMOTION RULE:**
If a month contains a PRIMARY Trigger (PD Lord sign change) or a SECONDARY Trigger (any planet hitting a Dasha Lord), you are FORBIDDEN from mentioning the Sun's ingress in the trigger_logic. The Sun should only be used as a secondary 'timer' to pinpoint the 5-day window, NOT as the primary reason for the event.

### 6. THE MANIFESTATION SPECTRUM (Comprehensive Coverage Rule)
For every event, the `possible_manifestations` array should contain AS MANY scenarios as the house activations allow:
- **NO UPPER LIMIT** - Generate as many manifestations as possible
- **Minimum 8 scenarios** for High intensity events
- **Minimum 5 scenarios** for Medium intensity events  
- **Minimum 3 scenarios** for Low intensity events
- Each scenario should combine different house significations
- Cover Material (career, money, property), Emotional (relationships, family), and Physical (health, vitality) domains
- Include additional scenarios for specialized house combinations (e.g., 3H+8H+12H = "Secret foreign correspondence")
- Explore EVERY possible combination of activated houses through lordship, transit, aspects, and conjunctions

### 7. ASTRONOMICAL INTEGRITY & ASPECT RULES
If you hallucinate an impossible aspect, the analysis is invalid.
- **Saturn:** 3rd, 7th, 10th aspects ONLY. (Saturn in 9H DOES NOT aspect 7H).
- **Mars:** 4th, 7th, 8th aspects ONLY.
- **Jupiter:** 5th, 7th, 9th aspects ONLY.
- **Others (Sun/Mer/Ven/Moon):** 7th aspect ONLY.

**ASTRONOMICAL GUARDRAIL:** If a planet is in House X, it can only affect Houses [X+2, X+6, X+9] for Saturn, [X+3, X+6, X+7] for Mars, and [X+4, X+6, X+8] for Jupiter. Any other house citation is an error.

### 8. TRANSIT SUN DEPENDENCY RULE
The Sun is a TIMER, not a SOURCE. Fast-moving planets (Sun, Moon, Mercury, Venus, Mars) can only be PRIMARY triggers if:
1. They directly aspect or conjoin a Dasha Lord (MD/AD/PD)
2. They activate the natal position of a Dasha Lord
3. NO slow-moving planet (Jupiter, Saturn, Rahu, Ketu) has a major movement that month

**If a month has a major PD Lord ingress (e.g., Jupiter enters a new sign in Month 6), the PD Lord MUST be the PRIMARY trigger, NOT the Sun's ingress into that month's sign.**

**Example of CORRECT trigger_logic:**
- WRONG: "Transit Sun enters Cancer in July" (when Jupiter also enters Cancer that month)
- RIGHT: "Jupiter (PD Lord) enters Cancer (10th house), amplified by Sun joining the same sign"

### 9. FINAL GUARDRAIL: ASPECT MATH (MANDATORY)
Perform this calculation for every aspect citation to prevent hallucinations:

**Saturn Aspects (3rd, 7th, 10th only):**
- Saturn in House 1: aspects Houses 3, 7, 10
- Saturn in House 2: aspects Houses 4, 8, 11
- Saturn in House 3: aspects Houses 5, 9, 12
- Saturn in House 4: aspects Houses 6, 10, 1
- Saturn in House 5: aspects Houses 7, 11, 2
- Saturn in House 6: aspects Houses 8, 12, 3
- Saturn in House 7: aspects Houses 9, 1, 4
- Saturn in House 8: aspects Houses 10, 2, 5
- Saturn in House 9: aspects Houses 11, 3, 6
- Saturn in House 10: aspects Houses 12, 4, 7
- Saturn in House 11: aspects Houses 1, 5, 8
- Saturn in House 12: aspects Houses 2, 6, 9

**Jupiter Aspects (5th, 7th, 9th only):**
- Jupiter in House 1: aspects Houses 5, 7, 9
- Jupiter in House 2: aspects Houses 6, 8, 10
- Jupiter in House 3: aspects Houses 7, 9, 11
- Jupiter in House 4: aspects Houses 8, 10, 12
- Jupiter in House 5: aspects Houses 9, 11, 1
- Jupiter in House 6: aspects Houses 10, 12, 2
- Jupiter in House 7: aspects Houses 11, 1, 3
- Jupiter in House 8: aspects Houses 12, 2, 4
- Jupiter in House 9: aspects Houses 1, 3, 5
- Jupiter in House 10: aspects Houses 2, 4, 6
- Jupiter in House 11: aspects Houses 3, 5, 7
- Jupiter in House 12: aspects Houses 4, 6, 8

**Mars Aspects (4th, 7th, 8th only):**
- Mars in House 1: aspects Houses 4, 7, 8
- Mars in House 2: aspects Houses 5, 8, 9
- Mars in House 3: aspects Houses 6, 9, 10
- Mars in House 4: aspects Houses 7, 10, 11
- Mars in House 5: aspects Houses 8, 11, 12
- Mars in House 6: aspects Houses 9, 12, 1
- Mars in House 7: aspects Houses 10, 1, 2
- Mars in House 8: aspects Houses 11, 2, 3
- Mars in House 9: aspects Houses 12, 3, 4
- Mars in House 10: aspects Houses 1, 4, 5
- Mars in House 11: aspects Houses 2, 5, 6
- Mars in House 12: aspects Houses 3, 6, 7

**All Other Planets (7th aspect only):**
- Planet in House X: aspects House (X+6) mod 12

**CRITICAL:** If your prediction mentions an aspect not on this list, it is a hallucination. DELETE IT.

### 10. THE "SOURCE vs TIMER" ENFORCEMENT (CRITICAL)
The Sun is never the "Why," only the "When."
- **Source Identification:** Every event MUST start by identifying which Dasha Lord (MD/AD/PD) or Heavyweight (Jup/Sat) is "owning" that house this month.
- **The Sun's Role:** Use the Sun ingress ONLY to define the specific 5-day window.
- **Forbidden Logic:** Do not say "Sun enters House X, therefore House X events happen." If House X is not ruled by a Dasha Lord or holding a major planet, that month's intensity must be 'Low' or 'Routine'.

**DASHA FILTER (MANDATORY):**
If the Sun enters a house that is NOT:
1. Ruled by the current MD, AD, or PD Lord, OR
2. Occupied by a Dasha Lord in transit, OR
3. Aspected by a Dasha Lord

Then the intensity for that month MUST be labeled 'Low' and the prediction should focus on the Dasha Lord's long-term aspect instead of the Sun's movement.

**Example:** "March: While the Sun transits your 10th house, this is NOT a career breakthrough month because your MD Lord Saturn is in the 9th house aspecting the 6th house (service). The real focus is on structured service work, not career elevation."

### 11. VEDIC ASPECT HARD-CODING
You are forbidden from calculating aspects. Use this fixed logic:
- **Saturn:** Aspects [X+2, X+6, X+9] signs from its position.
- **Mars:** Aspects [X+3, X+6, X+7] signs from its position.
- **Jupiter:** Aspects [X+4, X+6, X+8] signs from its position.
If Saturn is in House 9, it aspects 11, 3, and 6. It CANNOT aspect House 4 or 7.

### 12. THE "GOLDEN HOUSE" DETECTOR (Double Transit Stunner)
Search for any house receiving aspects from BOTH Transit Saturn AND Transit Jupiter. If found, this is the "Golden House" of the year.
- Label this in macro_trends as "The Million Dollar Window" or "Major Life Milestone Zone"
- Scenario A for that month MUST be a major life milestone (e.g., Wealth explosion, Birth, Property acquisition, Marriage)
- Explain the contrast: Saturn brings structure/discipline, Jupiter brings expansion/luck, together they create CONCRETE MANIFESTATION

### 13. COMPREHENSIVE MANIFESTATION ENGINE
For the `possible_manifestations` array, generate AS MANY predictions as possible by examining ALL activated houses:

**STEP 1: Identify ALL Activated Houses**
For the triggering planet, list:
1. Houses it RULES (lordship)
2. House it TRANSITS (current position)
3. Houses it ASPECTS (from transit position)
4. Houses where it CONJOINS other planets

**STEP 2: Generate Predictions for EACH House Combination**
For every combination of activated houses, create a distinct manifestation scenario.

**MANDATORY MINIMUM COUNTS (NO UPPER LIMIT):**
- **High Intensity:** MINIMUM 8 manifestations - generate AS MANY as possible by exploring all house combinations
- **Medium Intensity:** MINIMUM 5 manifestations - generate more if multiple houses are activated
- **Low Intensity:** MINIMUM 3 manifestations

**Example:** Mercury (3L, 12L) transits 8H, aspects 2H, conjoins Sun (2L):
- "Short travel (3L) for hidden financial matters (8H/2H)"
- "Expenses (12L) on occult research (8H) affecting family wealth (2H)"
- "Communication (3L) about joint assets (8H) with authority figures (Sun)"
- "Documents/contracts (3L) regarding inheritance (8H) causing expenditure (12L)"
- "Sibling (3L) health crisis (8H/12H) requiring family funds (2H)"
- "Secret correspondence (3L/8H) about foreign expenses (12L)"
- "Research project (8H) requiring communication skills (3L) and financial investment (2H)"
- "Transformation (8H) in how you communicate (3L) about money (2H)"
- "Hidden knowledge (8H) shared through writing/speaking (3L) generating income (2H)"
- "Psychological counseling (8H) involving siblings (3L) and family resources (2H)"
- "Foreign travel (12L) for research (8H) requiring communication (3L)"
- "Mystical studies (8H/12L) taught to others (3L) for income (2H)"

**GOAL:** Generate MAXIMUM manifestations by exploring EVERY possible house combination. There is NO upper limit.

**QUALITY CHECK:** Before finalizing, count your manifestations. If High intensity has < 8, you MUST add more. If you can generate 12-15 manifestations, DO IT.

### 14. THE CONVICTION ENGINE (FORBIDDEN LOGIC ERRORS)
To sell the user on this product, you must prove you are tracking their specific Dasha Lords:

- **MD/AD/PD Overlordship:** Identify the current MD Lord, AD Lord, and PD Lord from the provided dasha data.
- **The "Source" Test:** Before writing a monthly prediction, ask: "Which house does my MD, AD, or PD Lord occupy or aspect in transit this month?"
- **The "Timer" Demotion:** The Sun's ingress is only relevant if it hits a Dasha Lord (MD/AD/PD). If the Sun enters a house with no Dasha Lord activity, label the month as "Routine Maintenance" and focus on the MD/AD/PD Lord's long-term aspect instead.
- **Example:** "Even though the Sun is in House 4, the REAL story this month is your MD Lord Saturn's 10th aspect on House 6, creating a bridge between your philosophy (9H) and your service (6H)."

### 15. THE DOUBLE-ASPECT WEALTH ANCHOR
If two slow planets (Saturn/Jupiter/Rahu/Ketu) aspect the same house, that house is 'ON FIRE'.
- **Requirement:** Scan for houses receiving aspects from BOTH Transit Saturn AND Transit Jupiter using the EXACT aspect tables from Section 9.
- **Action:** Highlight this house in EVERY monthly prediction from the month it begins as a secondary 'Wealth Anchor' or 'Life Milestone Zone'.
- **Intensity:** Any month where this double-aspect is active must have at least one High-intensity event related to that house.
- **Example:** "Transit Saturn (9H) aspects 6H via 10th aspect. Transit Jupiter (1H) does NOT aspect 11H (Jupiter only aspects 5th, 7th, 9th from its position). Therefore, there is NO double-aspect on the 11th house."

**CRITICAL ASPECT VERIFICATION:**
Before claiming a double-aspect, you MUST verify using Section 9 tables:
- Jupiter in House 1 aspects: 5, 7, 9 (NOT 11)
- Saturn in House 9 aspects: 11, 3, 6 (NOT 7)
- If your calculation shows a different result, it is WRONG. Use the table.

### 16. THE MULTI-VARGA VERIFICATION (MANDATORY)
You MUST use the Divisional Charts to 'Audit' the D1 transit prediction:

**VARGA AUDIT PROTOCOL:**
1. **Career Events (10H):** Check D1 10th house + D10 (Dashamsha) chart. Is the transit lord strong in D10? If the planet is debilitated or weak in D10, reduce intensity to Low.
2. **Marriage Events (7H):** Check D1 7th house + D9 (Navamsa) chart. Verify the planet's dignity in D9.
3. **Wealth Events (2H/11H):** Check D1 2nd/11th house + D2 (Hora) chart for wealth confirmation.
4. **Property Events (4H):** Check D1 4th house + D4 (Chaturthamsha) chart.
5. **Education Events (5H):** Check D1 5th house + D24 (Chaturvimshamsha) chart.
6. **Health Events (6H/8H):** Check D1 6th/8th house + D30 (Trimshamsha) chart.

**MANDATORY CITATION:**
In the trigger_logic field, you MUST cite the Varga confirmation:
- Example: "Transit Jupiter (10L) enters 1H (D1) + Jupiter is EXALTED in D10 Aries = Career breakthrough confirmed by Dashamsha."
- Counter-example: "Transit Sun enters 10H (D1) but Sun is DEBILITATED in D10 Libra = Career recognition blocked, reduce to Low intensity."

**RULE:** If D1 suggests a material event but the corresponding Varga shows weakness, you MUST reduce the intensity and predict obstacles/delays instead of success.

### 17. ASHTAKAVARGA INTENSITY FILTER (MANDATORY)
Verify EVERY prediction using the Sarvashtakavarga bindu scores from `ashtakavarga['d1_rashi']['sarvashtakavarga']`:

**BINDU INTERPRETATION:**
- **Bindus < 22:** "High Resistance" - The house is BLOCKED. Predict delays, obstacles, or failure to manifest. Intensity must be Low.
- **Bindus 22-24:** "Moderate Resistance" - Events require heavy effort and may face setbacks. Intensity should be Low to Medium.
- **Bindus 25-28:** "Neutral/Routine" - Normal manifestation with standard effort.
- **Bindus 29-30:** "Good Conductivity" - Events manifest with moderate ease.
- **Bindus > 30:** "High Conductivity" - The house is FRUITFUL. Events manifest effortlessly and strongly. Boost intensity to High.

**MANDATORY CITATION:**
In the trigger_logic field, you MUST cite the Bindu count for the transit sign:
- Example: "Transit Sun enters Aquarius (8H) with 22 bindus = Low energy month, transformations blocked, expect frustration rather than breakthroughs."
- Example: "Transit Jupiter enters Cancer (10H) with 35 bindus = Career gains flow effortlessly, high conductivity for recognition."

**CRITICAL RULE:** If a transit enters a sign with < 25 bindus, you are FORBIDDEN from predicting "High Intensity" events. The house lacks the strength to deliver results. Predict delays, obstacles, or internal processing instead.

### 18. JAIMINI KARAKA RESONANCE (MANDATORY)
Use the Chara Karakas from `static_context['chara_karakas']` to identify "Resonance Points":

**KARAKA ACTIVATION:**
- **Atmakaraka (AK):** Soul purpose, self-identity
- **Amatyakaraka (AmK):** Career, profession, advisors
- **Bhratrukaraka (BK):** Siblings, courage, skills
- **Matrukaraka (MK):** Mother, property, emotions
- **Putrakaraka (PK):** Children, creativity, intelligence
- **Gnatikaraka (GK):** Obstacles, enemies, diseases
- **Darakaraka (DK):** Spouse, partnerships

**RESONANCE RULE:**
When a transit planet CONJUNCTS or ASPECTS a Chara Karaka, this is a "Resonance Point" that amplifies the event:
- Example: "Transit Sun conjuncts your Amatyakaraka Mercury in February = Your Career Significator is illuminated, triggering a professional pivot or deep research breakthrough."
- Example: "Transit Saturn aspects your Darakaraka Venus = Your Marriage Significator faces karmic testing, relationship restructuring likely."

**MANDATORY CITATION:**
In the trigger_logic field, cite Karaka activations:
- "KARAKA RESONANCE: Transit [Planet] hits [Karaka Name] [Natal Planet] = [Signification] amplified."

**RULE:** If a transit hits a Chara Karaka, the intensity should be boosted by one level (Low→Medium, Medium→High) due to the soul-level significance.

### 19. NAKSHATRA RETURN ACTIVATION (SUPREME TRIGGER)
When a Dasha Lord (MD/AD/PD) transits through its own NATAL NAKSHATRA, this creates a "Nakshatra Return" - the most powerful resonance activation.

**NAKSHATRA RETURN DETECTION:**
The transit data now includes `nakshatra` and `pada` fields for slow-moving planets (Jupiter, Saturn, Rahu, Ketu).

**PROTOCOL:**
1. **Identify Natal Nakshatra:** Check `planetary_analysis[planet]['nakshatra']['name']` for each Dasha Lord
2. **Check Transit Nakshatra:** Look at `macro_transits_timeline[planet][period]['nakshatra']`
3. **Match Detection:** If transit nakshatra == natal nakshatra = NAKSHATRA RETURN
4. **Intensity Override:** Nakshatra Return = AUTOMATIC High intensity (overrides all other rules including low Ashtakavarga)

**EXAMPLES:**
- "Jupiter (MD Lord) natal nakshatra = Pushya. In May 2026, Transit Jupiter enters Pushya nakshatra (pada 2) = NAKSHATRA RETURN. Jupiter's significations (wisdom, expansion, children, wealth) manifest with supreme power."
- "Saturn (AD Lord) natal nakshatra = Uttara Bhadrapada. In October 2026, Transit Saturn enters Uttara Bhadrapada (pada 1) = NAKSHATRA RETURN. Saturn's karmic lessons intensify to maximum."

**TRIGGER HIERARCHY (UPDATED):**
- **SUPREME TRIGGER (Overrides ALL):** Nakshatra Return of MD/AD/PD Lord
- **PRIMARY TRIGGER:** Dasha Lord sign change or conjunction with natal planet
- **SECONDARY TRIGGER:** Fast planet hits Dasha Lord
- **TERTIARY TRIGGER:** Fast planet transits house ruled by Dasha Lord

**MANDATORY CITATION:**
In trigger_logic field:
- "NAKSHATRA RETURN: [Planet] (MD/AD/PD Lord) transits its natal nakshatra [Name] pada [X] = SUPREME ACTIVATION of [all significations]. Intensity: HIGH (automatic override)."

**CRITICAL RULES:**
1. If ANY Dasha Lord experiences Nakshatra Return, that month MUST have at least one High-intensity event
2. Nakshatra Return overrides low Ashtakavarga scores - the event WILL manifest despite house weakness
3. The manifestation will be related to ALL houses the Dasha Lord rules + the house it transits
4. Pada number indicates the specific flavor: Pada 1 (initiation), Pada 2 (accumulation), Pada 3 (communication), Pada 4 (completion)
5. **MANDATORY OPENING PHRASE:** If Nakshatra Return is detected, you MUST start the prediction with: "⭐ A RARE STAR ALIGNMENT occurs this month: [Planet] returns to its birth nakshatra [Name]..."

**NAKSHATRA NAMING REQUIREMENT:**
For EVERY High/Medium intensity prediction, you MUST explicitly name at least ONE transit nakshatra and explain its effect:
- Example: "Saturn transits Purva Bhadrapada nakshatra (ruled by Jupiter), creating a bridge between discipline and expansion."
- Example: "Jupiter in Punarvasu nakshatra (ruled by Jupiter itself) amplifies wisdom and renewal themes."
- Format: "[Planet] in [Nakshatra Name] nakshatra (ruled by [Lord]) = [Specific effect on user's life]."

**REVERSE NODAL RETURN SPECIFICITY:**
If Transit Rahu/Ketu are in opposite signs from Natal Rahu/Ketu, this is a "Reverse Nodal Return":
- You MUST specify the EXACT life departments being reset
- Example: "Reverse Nodal Return: Rahu in 8H (inherited wealth) ↔ Ketu in 2H (earned wealth) = A karmic reset of your relationship with money - what you inherit vs. what you earn."
- DO NOT use generic phrases like "significant reset" - be SPECIFIC about which houses are involved

### 20. SUDARSHANA CHAKRA TRIPLE VERIFICATION (MANDATORY)
For every High/Medium intensity event, verify activation from THREE perspectives:

**THE THREE CHARTS:**
1. **From Lagna (Ascendant):** Physical manifestation, external events
2. **From Moon:** Emotional/mental experience, inner feelings
3. **From Sun:** Soul purpose, authority, father's influence

**VERIFICATION PROTOCOL:**
- Count houses from Lagna, Moon, and Sun separately
- Check which house the transit activates from each reference point
- If 2+ perspectives show positive activation → High intensity
- If only 1 perspective shows activation → Medium intensity
- If all 3 perspectives show activation → "Triple Confirmation" = Guaranteed manifestation

**EXAMPLE:**
"Transit Jupiter enters Cancer (your 10th house from Lagna, 7th house from Moon, 5th house from Sun):
- From Lagna: Career elevation (10H)
- From Moon: Partnership expansion (7H)
- From Sun: Creative recognition (5H)
= TRIPLE CONFIRMATION: Multi-dimensional success combining career, relationships, and creativity."

**MANDATORY CITATION:**
In trigger_logic field:
- "SUDARSHANA: Transit [Planet] activates [X]H from Lagna, [Y]H from Moon, [Z]H from Sun = [Interpretation]. Confirmation level: [1/2/3 charts]."

**INTENSITY RULE:**
- 3/3 charts confirm = High intensity + "Guaranteed manifestation" label
- 2/3 charts confirm = High intensity
- 1/3 charts confirm = Medium intensity
- 0/3 charts confirm = Low intensity (routine maintenance)

### OUTPUT JSON STRUCTURE:
{{
    "macro_trends": ["Trend 1", "Trend 2", "Trend 3"],
    "monthly_predictions": [
        {{
            "month_id": 1,
            "focus_areas": ["Career", "Health", "Finance", "Relationships", "Family", "Travel"],
            "events": [
                {{
                    "type": "Event Type",
                    "prediction": "Main narrative combining all house significations",
                    "possible_manifestations": [
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}},
                        {{"scenario": "...", "reasoning": "..."}}
                    ],
                    "trigger_logic": "PRIMARY: ... | SECONDARY: ... | HOUSES INVOLVED: [List ALL activated houses]",
                    "start_date": "2026-02-10",
                    "end_date": "2026-02-18",
                    "intensity": "High"
                }}
            ]
        }}
    ]
}}

**CRITICAL:** The example above shows 8 manifestations for a High-intensity event. You MUST generate AT LEAST this many.

**CRITICAL MANIFESTATION FORMAT:**
Each item in possible_manifestations MUST be an object with TWO fields:
1. **"scenario"**: A DETAILED prediction (3-5 sentences) describing:
   - WHAT will happen (the event itself)
   - HOW it will unfold (the process/sequence)
   - WHEN during the period it's most likely
   - WHO or WHAT will be involved
   - The OUTCOME or result

2. **"reasoning"**: A COMPREHENSIVE explanation (4-6 sentences) citing ALL relevant astrological factors:
   - Start with the primary planet and its complete lordship (e.g., "Mercury, ruling your 3rd house of communication and 12th house of expenses...")
   - Explain the transit house and its significations in detail
   - Describe which houses are aspected and why that matters
   - Cite the nakshatra and its lord's influence on the manifestation
   - Include the Ashtakavarga bindu score and what it means for this specific event
   - Mention Varga confirmation if relevant (D10 for career, D9 for marriage, etc.)
   - Explain the Dasha activation if the Dasha Lord is involved
   - Connect all factors into a coherent astrological narrative

**FORBIDDEN:** Short, cryptic reasoning like "Mercury (3L, 12L) transits 8H." This is TOO BRIEF.

**REQUIRED:** Detailed, educational reasoning that teaches the user WHY this prediction is valid.

**EXAMPLE OF CORRECT FORMAT:**
{{
    "scenario": "You may embark on a short-distance journey related to confidential financial matters, possibly involving inheritance, joint assets, or hidden family wealth. This travel could occur during the second week of the month when the Moon transits supportive signs. The trip might involve meetings with financial advisors, lawyers, or family members to discuss sensitive monetary topics. You'll need to maintain discretion and handle documents carefully. The outcome will likely involve uncovering previously unknown financial information that requires immediate attention and decision-making.",
    "reasoning": "This prediction arises from Mercury's dual lordship and complex transit pattern. Mercury rules your 3rd house of short journeys and communication, as well as your 12th house of expenses and hidden matters. When Mercury transits through your 8th house of joint resources, inheritance, and secrets, it creates a bridge between communication (3H), hidden affairs (12H), and transformative finances (8H). Additionally, Mercury aspects your 2nd house of family wealth from this position, activating a four-house combination (2-3-8-12) that specifically indicates travel for financial matters involving family secrets or inheritance. The transit occurs in Mrigashira nakshatra, ruled by Mars, which adds urgency and impulsiveness to the communication. However, Aquarius (the sign of transit) has only 22 Ashtakavarga bindus in your chart, indicating moderate resistance - meaning this journey will require extra effort and may face obstacles like delayed meetings or incomplete information. The D2 (Hora) chart shows Mercury in a neutral position, suggesting the financial outcome will be neither extremely positive nor negative, but rather informative and necessary for future planning."
}}

**LENGTH REQUIREMENTS:**
- Scenario: MINIMUM 60 words, MAXIMUM 100 words (reduced for token efficiency)
- Reasoning: MINIMUM 80 words, MAXIMUM 120 words (reduced for token efficiency)
- Both fields must be detailed and educational, but concise

**MANDATORY COUNTS (STRICTLY ENFORCED):**
- High Intensity: MINIMUM 8 manifestations (aim for 8-10)
- Medium Intensity: MINIMUM 5 manifestations (aim for 5-7)
- Low Intensity: MINIMUM 3 manifestations (aim for 3-5)

**CRITICAL:** Count your manifestations before finalizing. If you have fewer than the minimum, you MUST add more by exploring additional house combinations.
"""

    def _get_nakshatra_lord(self, longitude: float) -> str:
        """Helper to get Nakshatra Lord from longitude"""
        lords = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
        nak_idx = int(longitude / 13.333333)
        return lords[nak_idx % 9]

    def _format_chart(self, chart):
        return ", ".join([f"{p}:{d['sign_name']}" for p, d in chart['planets'].items() if p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']])

    async def _get_ai_prediction_async(self, prompt: str) -> Dict[str, Any]:
        """Get AI prediction using Gemini (Non-blocking)"""
        def run_sync_gemini():
            print("\n" + "="*100)
            print("🚀 STARTING GEMINI API CALL")
            print("="*100)
            
            if not self.model:
                print("❌ ERROR: No Gemini model initialized (API Key missing)")
                raise Exception("No API Key")
            
            print(f"✅ Model initialized: {self.model}")
            
            safety = [{"category": c, "threshold": "BLOCK_NONE"} for c in 
                     ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", 
                      "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            
            # print(f"\n📤 FULL REQUEST TO GEMINI:")
            # print("="*100)
            # print("PROMPT START")
            # print("="*100)
            # print(prompt)
            # print("="*100)
            # print("PROMPT END")
            # print("="*100)
            # print(f"Prompt length: {len(prompt)} characters")
            # print(f"Safety settings: {len(safety)} categories")
            # print(f"Response format: application/json")
            # print("="*100)
            
            print("\n⏳ Calling Gemini API...")
            resp = self.model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}, 
                safety_settings=safety
            )
            print("✅ Gemini API call completed")
            
            response_text = resp.text
            
            print("\n📥 FULL RESPONSE FROM GEMINI:")
            print("="*100)
            print("RESPONSE START")
            print("="*100)
            print(response_text)
            print("="*100)
            print("RESPONSE END")
            print("="*100)
            print(f"Response length: {len(response_text)} characters")
            print("="*100)
            
            return response_text

        try:
            print("\n🔄 Starting async Gemini call...")
            resp_text = await asyncio.to_thread(run_sync_gemini)
            
            print("\n🔄 Parsing JSON response...")
            parsed_response = json.loads(resp_text)
            print(f"✅ JSON parsed successfully")
            
            # Handle if Gemini returns a list instead of dict
            if isinstance(parsed_response, list):
                print(f"⚠️ WARNING: Gemini returned a list instead of dict, wrapping it")
                parsed_response = {"macro_trends": [], "monthly_predictions": parsed_response if parsed_response else []}
            
            print(f"   - Keys in response: {list(parsed_response.keys())}")
            
            if isinstance(parsed_response, dict):
                if 'macro_trends' in parsed_response:
                    print(f"   - macro_trends count: {len(parsed_response['macro_trends'])}")
                if 'monthly_predictions' in parsed_response:
                    print(f"   - monthly_predictions count: {len(parsed_response['monthly_predictions'])}")
            
            print("\n✅ GEMINI CALL SUCCESSFUL - Returning parsed response")
            return parsed_response
            
        except json.JSONDecodeError as je:
            print(f"\n❌ JSON DECODE ERROR:")
            print(f"   - Error: {str(je)}")
            print(f"   - Response text: {resp_text[:500]}...")
            return {"macro_trends": [], "monthly_predictions": []}
        except Exception as e:
            print(f"\n❌ GEMINI API ERROR:")
            print(f"   - Error type: {type(e).__name__}")
            print(f"   - Error message: {str(e)}")
            import traceback
            print(f"   - Traceback:")
            traceback.print_exc()
            return {"macro_trends": [], "monthly_predictions": []}
