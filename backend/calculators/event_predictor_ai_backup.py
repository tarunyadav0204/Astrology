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
                self.model = genai.GenerativeModel('models/gemini-3-pro-preview')
                print("✅ EventPredictor using Gemini 3.0 Pro Preview")
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
- RIGHT: "Sun transits 10th house from Lagna"r 3rd and 12th lord transits..."
- This helps users understand WHY a planet matters to them

**4. DEBILITATION RULE:**
When a planet is debilitated in transit, do NOT just predict 'bad results'.
- Predict that the specific life department ruled by that planet (lordship) will require heavy effort or resource drain
- Example: "Sun (2L) debilitated in 4th = Spending wealth on home repairs" NOT just "Stress at home"

### 1. THE "RULE OF THREE" MANIFESTATION SPECTRUM
For every High/Medium intensity event, you MUST provide exactly three scenarios in the `possible_manifestations` array. This ensures total coverage of the user's life:
- **Material/Artha Scenario:** Focus on Career, Money, Property, or Status.
- **Internal/Emotional Scenario:** Focus on Family, Peace of Mind, or Relationships.
- **Physical/Obstacle Scenario:** Focus on Health, Energy levels, or hidden challenges.

### 2. THE MULTI-HOUSE SYNTHESIS ENGINE (BPHS LOGIC)
A planet is a bridge. You are forbidden from predicting an isolated house result.
**Synthesis Formula:** [Planet] = ([Natal Lordship Houses] + [Transit House]) acting upon [Aspected Houses].
- *Example:* Jupiter (rules 6, 9) transiting 1H and aspecting 5H.
- *Synthesis:* "Your luck/fortune (9L) and service (6L) physically manifest (1H) to bring gains through creativity or children (5H aspect)."

### 3. STRICT ACTIVATION HIERARCHY (DASHA-FIRST LOGIC)
The Sun is only a timer; the Dasha Lords are the source.
1. **PRIMARY TRIGGER:** The PD Lord moves into a new house or hits a Natal Planet.
2. **SECONDARY TRIGGER:** A fast planet (Sun/Mars/Venus) conjuncts or aspects the current MD or AD Lord.
3. **TERTIARY TRIGGER (Resonance):** A fast planet transits the house RULED by the PD Lord.
4. **THE "STUN" TRIGGER:** Transit Saturn and Transit Jupiter both aspect the same house (Double Transit). If this occurs, intensity is ALWAYS 'High'.

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

### 6. THE MANIFESTATION SPECTRUM (3-Scenario Rule)
For every event, the `possible_manifestations` array must contain exactly 3 scenarios:
1. **Material (External):** Career, money, status, or property.
2. **Emotional (Internal):** Relationships, family, or peace of mind.
3. **Physical (Body):** Health, vitality, or physical obstacles.
Even if a transit looks 'good', Scenario 3 must cover potential physical strain or over-exertion.

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

### 13. BRIDGE PRINCIPLE FOR MANIFESTATIONS
For the `possible_manifestations` array, use the Bridge Principle to force complete coverage:
- **Scenario 1 (Material):** Combine [Planet Lordship] + [Transit House]
  - Example: Mercury (3L, 12L) in 8H = "Expenses (12L) regarding hidden (8H) contracts or short travel (3L) for crisis management (8H)"
- **Scenario 2 (Emotional):** Combine [Planet Lordship] + [Natal House where planet sits]
  - Example: Mercury (3L, 12L) natal in 8H = "Communication (3L) about family secrets (8H) or expenses (12L) on occult/research (8H)"
- **Scenario 3 (Physical):** Combine [Planet Lordship] + [Aspected House]
  - Example: Mercury aspects 2H = "Short travel (3L) affecting wealth (2H) or expenses (12L) on family (2H)"

This forces you to look at the planet's entire 'web' of influence across lordship, placement, and aspects.

### 14. THE CONVICTION ENGINE (FORBIDDEN LOGIC ERRORS)
To sell the user on this product, you must prove you are tracking their specific Dasha Lords:

- **MD/AD/PD Overlordship:** Identify the current MD Lord, AD Lord, and PD Lord from the provided dasha data.
- **The "Source" Test:** Before writing a monthly prediction, ask: "Which house does my MD, AD, or PD Lord occupy or aspect in transit this month?"
- **The "Timer" Demotion:** The Sun's ingress is only relevant if it hits a Dasha Lord (MD/AD/PD). If the Sun enters a house with no Dasha Lord activity, label the month as "Routine Maintenance" and focus on the MD/AD/PD Lord's long-term aspect instead.
- **Example:** "Even though the Sun is in House 4, the REAL story this month is your MD Lord Saturn's 10th aspect on House 6, creating a bridge between your philosophy (9H) and your service (6H)."

### 15. THE DOUBLE-ASPECT WEALTH ANCHOR
If two slow planets (Saturn/Jupiter/Rahu/Ketu) aspect the same house, that house is 'ON FIRE'.
- **Requirement:** Scan for houses receiving aspects from BOTH Transit Saturn AND Transit Jupiter.
- **Action:** Highlight this house in EVERY monthly prediction from the month it begins as a secondary 'Wealth Anchor' or 'Life Milestone Zone'.
- **Intensity:** Any month where this double-aspect is active must have at least one High-intensity event related to that house.
- **Example:** "Transit Saturn (9H) and Transit Jupiter (1H) both aspect the 11th House (Gains) = Major financial breakthrough, elder sibling event, or network expansion."

**4. DEBILITATION RULE:**
When a planet is debilitated in transit, do NOT just predict 'bad results'.
- Predict that the specific life department ruled by that planet (lordship) will require heavy effort or resource drain
- Example: "Sun (2L) debilitated in 4th = Spending wealth on home repairs" NOT just "Stress at home"

### 1. THE "RULE OF THREE" MANIFESTATION SPECTRUM
For every High/Medium intensity event, you MUST provide exactly three scenarios in the `possible_manifestations` array. This ensures total coverage of the user's life:
- **Material/Artha Scenario:** Focus on Career, Money, Property, or Status.
- **Internal/Emotional Scenario:** Focus on Family, Peace of Mind, or Relationships.
- **Physical/Obstacle Scenario:** Focus on Health, Energy levels, or hidden challenges.

### 2. THE MULTI-HOUSE SYNTHESIS ENGINE (BPHS LOGIC)
A planet is a bridge. You are forbidden from predicting an isolated house result.
**Synthesis Formula:** [Planet] = ([Natal Lordship Houses] + [Transit House]) acting upon [Aspected Houses].
- *Example:* Jupiter (rules 6, 9) transiting 1H and aspecting 5H.
- *Synthesis:* "Your luck/fortune (9L) and service (6L) physically manifest (1H) to bring gains through creativity or children (5H aspect)."

### 3. STRICT ACTIVATION HIERARCHY (DASHA-FIRST LOGIC)
The Sun is only a timer; the Dasha Lords are the source.
1. **PRIMARY TRIGGER:** The PD Lord moves into a new house or hits a Natal Planet.
2. **SECONDARY TRIGGER:** A fast planet (Sun/Mars/Venus) conjuncts or aspects the current MD or AD Lord.
3. **TERTIARY TRIGGER (Resonance):** A fast planet transits the house RULED by the PD Lord.
4. **THE "STUN" TRIGGER:** Transit Saturn and Transit Jupiter both aspect the same house (Double Transit). If this occurs, intensity is ALWAYS 'High'.

### 4. ASTRONOMICAL INTEGRITY & ASPECT RULES
If you hallucinate an impossible aspect, the analysis is invalid.
- **Saturn:** 3rd, 7th, 10th aspects ONLY. (Saturn in 9H DOES NOT aspect 7H).
- **Mars:** 4th, 7th, 8th aspects ONLY.
- **Jupiter:** 5th, 7th, 9th aspects ONLY.
- **Others (Sun/Mer/Ven/Moon):** 7th aspect ONLY.

### 5. TRANSIT SUN DEPENDENCY RULE
The Sun is a TIMER, not a SOURCE. Fast-moving planets (Sun, Moon, Mercury, Venus, Mars) can only be PRIMARY triggers if:
1. They directly aspect or conjoin a Dasha Lord (MD/AD/PD)
2. They activate the natal position of a Dasha Lord
3. NO slow-moving planet (Jupiter, Saturn, Rahu, Ketu) has a major movement that month

**If a month has a major PD Lord ingress (e.g., Jupiter enters a new sign in Month 6), the PD Lord MUST be the PRIMARY trigger, NOT the Sun's ingress into that month's sign.**

**Example of CORRECT trigger_logic:**
- WRONG: "Transit Sun enters Cancer in July" (when Jupiter also enters Cancer that month)
- RIGHT: "Jupiter (PD Lord) enters Cancer (10th house), amplified by Sun joining the same sign"r 3rd and 12th lord transits..."
- This helps users understand WHY a planet matters to them

**4. DEBILITATION RULE:**
When a planet is debilitated in transit, do NOT just predict 'bad results'.
- Predict that the specific life department ruled by that planet (lordship) will require heavy effort or resource drain
- Example: "Sun (2L) debilitated in 4th = Spending wealth on home repairs" NOT just "Stress at home"

### 1. THE MULTI-HOUSE SYNTHESIS ENGINE (BPHS LOGIC)
**CRITICAL: Act as a scholar of Brihat Parashara Hora Shastra.**

**RULE: A planet MUST deliver the results of:**
1. **Both houses it rules** (Lordship)
2. **The house it sits in** (Placement)
3. **The houses it aspects** (HITS tag)

**If you ignore one house, the prediction is considered a FAILURE.**

**Synthesis Formula:**
> [Planet] = [Natal House Lordship] + [Transit House] + [Aspected Houses]

**Mandatory Task: Provide a "Spectrum of Manifestation"**

For every major trigger, list at least 3 distinct "Combined Scenarios" that show how multiple life departments interact.

**Example:**
If Jupiter (9L, 6L) transits H12 and aspects H4:
- **Scenario A:** High expenditure (12H) on a home (4H) pilgrimage (9H)
- **Scenario B:** Hospitalization (12H/6H) of a father figure (9H) causing domestic stress (4H)
- **Scenario C:** Foreign travel (12H/9H) for a service-oriented job (6H) while buying property (4H)

**DO NOT provide isolated predictions. ALWAYS combine house significations.**

### 2. BHAVASANDHI: THE BRIDGE PRINCIPLE
**When a planet rules multiple houses, it acts as a BRIDGE between life departments.**

**Example:** Mercury rules 2nd (Family/Wealth) and 5th (Children/Creativity)
- Don't say: "Family matters" OR "Creative projects"
- Say: "Family wealth invested in children's education" or "Creative work generating family income"

**Transmutation Events:**
When a Dasha Lord or AmK/PiK is hit by transit, it's not just an event—it's a **re-birth of that life area**.

### 3. THE "ALL-SIGNIFICATION" RULE
Do not limit a house to one meaning. Check ALL possibilities for every activated house.
    * *Interpretation A:* **Foreign Travel/Relocation** (Especially if Dasha is Rahu/Jupiter/Saturn).
    * *Interpretation B:* **High Expenditure/Investment**.
    * *Interpretation C:* **Hospitalization/Sleep Issues**.
    * *Interpretation D:* **Spiritual Retreat**.

* **9th House Activation:**
    * *Interpretation A:* **Long Distance Travel** (Pilgrimage/Vacation).
    * *Interpretation B:* **Father/Guru** events.
    * *Interpretation C:* **Higher Education**.

* **4th House Activation:**
    * *Interpretation A:* **Home/Property** (Renovation, Purchase, Sale).
    * *Interpretation B:* **Mother** (Health/Relationship).
    * *Interpretation C:* **Vehicles** (Purchase/Accident).
    * *Interpretation D:* **Domestic Peace/Chaos**.

* **11th House Activation:**
    * *Interpretation A:* **Financial Gains**.
    * *Interpretation B:* **Social Network/Friends**.
    * *Interpretation C:* **Elder Siblings**.

* **3rd House Activation:**
    * *Interpretation A:* **Short Travel**.
    * *Interpretation B:* **Younger Siblings**.
    * *Interpretation C:* **Documents/Contracts**.

### 2. STRICT ACTIVATION HIERARCHY (DASHA LORD PRIORITY)
**CRITICAL: Houses and planets are "awake" or "asleep" based on Dasha Lords (MD/AD/PD).**

**FORBIDDEN PATTERN:** Do NOT predict major events based solely on Sun sign changes unless the Sun directly interacts with a Dasha Lord or natal planet.

**TRANSIT SUN DEPENDENCY RULE:**
The Sun is a TIMER, not a SOURCE. Fast-moving planets (Sun, Moon, Mercury, Venus, Mars) can only be PRIMARY triggers if:
1. They directly aspect or conjoin a Dasha Lord (MD/AD/PD)
2. They activate the natal position of a Dasha Lord
3. NO slow-moving planet (Jupiter, Saturn, Rahu, Ketu) has a major movement that month

**If a month has a major PD Lord ingress (e.g., Jupiter enters a new sign in Month 6), the PD Lord MUST be the PRIMARY trigger, NOT the Sun's ingress into that month's sign.**

**Example of CORRECT trigger_logic:**
- WRONG: "Transit Sun enters Cancer in July" (when Jupiter also enters Cancer that month)
- RIGHT: "Jupiter (PD Lord) enters Cancer (10th house), amplified by Sun joining the same sign"

**MANDATORY TRIGGER HIERARCHY (Check in this order):**

**PRIMARY TRIGGER (Most Powerful):**
1. **PD Lord Transit:** When the Pratyantar Dasha (PD) Lord changes sign or aspects a natal planet
   - Example: "PD Lord Jupiter transits from Taurus to Gemini (your 9th house) on Month X"
   - Example: "PD Lord Saturn aspects your Natal Moon on Date Y"

**SECONDARY TRIGGER:**
2. **Dasha-Transit Resonance:** When a transiting planet conjuncts or aspects the current MD/AD/PD Lords
   - Example: "Transit Mars conjuncts Natal Saturn (MD Lord) at 15° Leo on Feb 10"
   - Example: "Transit Sun aspects Natal Rahu (AD Lord) from 7th position"

**TERTIARY TRIGGER:**
3. **House Lordship Activation:** When a fast planet transits the house RULED BY the current PD Lord
   - Example: "PD Lord Mercury rules 3rd house. Transit Mars enters 3rd house → Activates communication/travel"

**QUATERNARY TRIGGER:**
4. **Mutual Aspect of Heavyweights:** When Transit Saturn AND Transit Jupiter both aspect the same house
   - Example: "Transit Jupiter aspects H7 from H11, Transit Saturn aspects H7 from H10 → Marriage event"

**LAST RESORT TRIGGER:**
5. **Fast Planet + Natal Planet:** Only when a fast planet (Mars/Sun/Venus) conjuncts a NATAL planet (not just enters a house)
   - Example: "Transit Sun conjuncts Natal Mercury (AmK/Career Lord) at 21° Aquarius"

**VALIDATION RULE:**
Before predicting ANY event, ask yourself:
- "Is the PD Lord involved in this transit?"
- "Does this transit activate the MD/AD Lord?"
- "Is this house ruled by a Dasha Lord?"

If the answer to all three is NO, then DO NOT predict a major event. It's just background noise.

**Example of CORRECT Reasoning:**
"Feb 2026 Career Event: While Saturn has been in H9 for months, the event triggers NOW because:
1. You are in Saturn-Rahu-Mercury PD (Mercury is PD Lord)
2. Transit Sun enters Aquarius (8th house) on Feb 10
3. Transit Sun conjuncts Natal Mercury (PD Lord + AmK) at 21° Aquarius on Feb 13
4. This activates the 1/7 axis with your MD Lord Saturn (opposite sign)
5. Result: Career-related financial negotiation Feb 10-18"

**Example of INCORRECT Reasoning (FORBIDDEN):**
"March 2026: Sun enters Pisces (9th house) → Travel event"
(This is WRONG because it ignores Dasha Lords and treats Sun as automatic trigger)

### 3. PRECISE DATE WINDOW CALCULATION
**CRITICAL: Event dates must be astronomically accurate, not arbitrary.**

**Date Window Rules:**
1. **Calculate the exact conjunction/aspect date** using the transit data provided
2. **Use that exact date as the CENTER of a 5-day window**
   - Example: If Sun conjuncts Mercury on Feb 20th → Event window is Feb 18-22
   - Example: If Mars aspects Saturn on May 15th → Event window is May 13-17

3. **For sign changes:** Use the sign ingress date as the start
   - Example: Jupiter enters Cancer on Jun 10 → Event window Jun 10-15

4. **For PD Lord transits:** Use the exact degree crossing date
   - Example: PD Lord Saturn crosses 15° Leo (natal planet position) on Mar 8 → Window Mar 6-10

**FORBIDDEN:** Do NOT use generic month-long windows like "Feb 1-28" or "entire March"
**REQUIRED:** Every event must have a specific 3-7 day window centered on the astronomical trigger

### 4. THE "ASPECT SCANNER" (Hidden Events)
* Look at the **[HITS: X, Y, Z]** tag. This lists houses aspected by the planet.
* **Sibling Rule:** If Saturn/Mars/Jupiter **HITS H3 or H11**, predict "Event concerning Sibling."
* **Injury Rule:** If Mars/Saturn/Rahu **HITS H8 or H6**, predict "Injury/Health flare-up."

### 5. THE "DASHA" DRIVER
* **The PD Lord is KING.** Whatever house the PD Lord sits in OR ASPECTS (check HITS) becomes the main event.
* If PD Lord is Jupiter in 12H -> The 12th house event (Travel/Expense) IS the prediction.

### OUTPUT JSON WITH MANIFESTATION SPECTRUM:
Predict **multiple distinct events** per month showing house combinations.

**REQUIRED STRUCTURE:**
Each event must have:
- type: Event Type
- prediction: Main narrative combining all house significations
- possible_manifestations: Array with at least 3 scenarios
- trigger_logic: PRIMARY and SECONDARY triggers with HOUSES INVOLVED list
- start_date and end_date: YYYY-MM-DD format
- intensity: High/Medium/Low

**The possible_manifestations array is MANDATORY for all High and Medium intensity events.**

**NOTE:** The focus_areas shown below are examples only. Use any relevant life domains based on the astrological data.

**OUTPUT JSON STRUCTURE:**
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
                        "Scenario A: Specific combination",
                        "Scenario B: Alternative combination",
                        "Scenario C: Third possibility"
                    ],
                    "trigger_logic": "PRIMARY: ... | SECONDARY: ... | HOUSES INVOLVED: [List]",
                    "start_date": "2026-02-10",
                    "end_date": "2026-02-18",
                    "intensity": "High"
                }}
            ]
        }}
    ]
}}
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
            
            print(f"\n📤 FULL REQUEST TO GEMINI:")
            print("="*100)
            print("PROMPT START")
            print("="*100)
            print(prompt)
            print("="*100)
            print("PROMPT END")
            print("="*100)
            print(f"Prompt length: {len(prompt)} characters")
            print(f"Safety settings: {len(safety)} categories")
            print(f"Response format: application/json")
            print("="*100)
            
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
            print(f"   - Keys in response: {list(parsed_response.keys())}")
            
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
