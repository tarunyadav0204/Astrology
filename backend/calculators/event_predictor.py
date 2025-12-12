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
                    self.model = genai.GenerativeModel('models/gemini-2.5-flash')
                    print("✅ EventPredictor using Gemini 2.5 Flash")
                except:
                    self.model = genai.GenerativeModel('gemini-pro')

    async def predict_yearly_events(self, birth_data: Dict, year: int) -> Dict[str, Any]:
        try:
            # Calculate Age for Context
            birth_year = int(birth_data['date'].split('-')[0])
            current_age = year - birth_year
            
            raw_data = self._prepare_yearly_data(birth_data, year)
            
            # Pass Age to prompt generator for Desha Kala Patra logic
            prompt = self._create_prediction_prompt(raw_data, year, current_age)
            
            # Debug Log
            print(f"\n🔮 GEMINI PROMPT FOR {year} (Age: {current_age}):")
            print("=" * 80)
            print(prompt)
            print("=" * 80)
            
            ai_response = await self._get_ai_prediction_async(prompt)
            
            return {"year": year, "status": "success", **ai_response}
        except Exception as e:
            return {"year": year, "status": "error", "error": str(e), "macro_trends": [], "monthly_predictions": []}

    def _prepare_yearly_data(self, birth_data: Dict, year: int) -> str:
        """
        Compiles data with "Natal Resonance" checks and Explicit Aspect Hits.
        """
        # 1. Basic Calculation & Natal Map
        birth_obj = SimpleNamespace(**birth_data)
        d1_chart = self.chart_calc.calculate_chart(birth_obj)
        asc_sign = int(d1_chart['ascendant'] / 30)
        
        # --- FIX: CONVERT INDEX TO NAME ---
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                      'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        asc_name = sign_names[asc_sign]
        
        # 1a. Map Natal Positions & Nakshatra Lords
        natal_map = {}
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for p, data in d1_chart['planets'].items():
            if p in planet_names:
                house = int((data['sign'] - asc_sign) % 12) + 1
                nak_lord = self._get_nakshatra_lord(data['longitude'])
                natal_map[p] = {'sign': data['sign'], 'house': house, 'nak_lord': nak_lord, 'obj': data}

        # 1b. Identify Pre-Existing Natal Connections
        natal_links = []
        for p1 in planet_names:
            for p2 in planet_names:
                if p1 == p2: continue
                if natal_map[p1]['house'] == natal_map[p2]['house']:
                    natal_links.append(f"{p1}-{p2}")
        
        # 2. Divisional & SAV
        div_calc = DivisionalChartCalculator(d1_chart)
        d9_data = div_calc.calculate_divisional_chart(9)
        d10_data = div_calc.calculate_divisional_chart(10)
        av_calc = self.ashtakavarga_cls(birth_data, d1_chart)
        sav_data = av_calc.calculate_sarvashtakavarga()
        
        sav_summary = []
        house_strength = {}
        for sign_idx, score in sav_data['sarvashtakavarga'].items():
            h = ((sign_idx - asc_sign) % 12) + 1
            house_strength[h] = "STRONG" if score > 30 else "WEAK" if score < 25 else "AVG"
            sav_summary.append(f"H{h}:{score}")
        
        # 3. Monthly Loop with RESONANCE CHECK
        monthly_data = []
        
        # Vedic Aspects Definitions
        vedic_aspects = {
            'Sun': [7], 'Moon': [7], 'Mars': [4, 7, 8], 'Mercury': [7],
            'Jupiter': [5, 7, 9], 'Venus': [7], 'Saturn': [3, 7, 10], 'Rahu': [5, 7, 9], 'Ketu': [5, 7, 9]
        }

        for month in range(1, 13):
            sample_date = datetime(year, month, 15)
            
            # Dasha
            dashas = self.dasha_calc.calculate_current_dashas(birth_data, sample_date)
            dasha_str = f"Dasha: {dashas['mahadasha']['planet']} >> {dashas['antardasha']['planet']} >> {dashas['pratyantardasha']['planet']}"
            
            transits = []
            for planet in planet_names:
                if planet not in ['Sun', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Venus', 'Mercury']: continue
                
                pos = self.transit_calc.get_planet_position(sample_date, planet)
                if pos is not None:
                    t_house = self.transit_calc.calculate_house_from_longitude(pos, d1_chart['ascendant'])
                    t_nak_lord = self._get_nakshatra_lord(pos)
                    
                    # --- RESONANCE CHECKS ---
                    resonance_tags = []
                    
                    # 1. Nadi Resonance
                    if t_nak_lord == natal_map[planet]['nak_lord']:
                        resonance_tags.append("NADI RETURN")
                    
                    # 2. Natal Aspect Retrigger
                    for np, ndata in natal_map.items():
                        if ndata['house'] == t_house:
                            resonance_tags.append(f"CONJ NATAL {np}")
                            if f"{planet}-{np}" in natal_links:
                                resonance_tags.append(f"**TRIGGERING NATAL PROMISE {planet}-{np}**")
                    
                    # 3. Transit Aspects (TARGET HOUSES)
                    aspect_houses = []
                    if planet in vedic_aspects:
                        for asp in vedic_aspects[planet]:
                            if asp == 1: continue
                            # Calculate target house relative to transit house
                            target_h = ((t_house + asp - 2) % 12) + 1
                            aspect_houses.append(str(target_h))
                            
                            # Check Natal Planets in Aspect
                            for np, ndata in natal_map.items():
                                if ndata['house'] == target_h:
                                    resonance_tags.append(f"ASPECTS NATAL {np}")
                    
                    # Format String
                    hits_str = f"[HITS: {','.join(aspect_houses)}]" if aspect_houses else ""
                    res_str = f" [{', '.join(resonance_tags)}]" if resonance_tags else ""
                    sav_str = f"[{house_strength.get(t_house, '')}]"
                    
                    transits.append(f"{planet}:H{t_house}{sav_str}{hits_str}{res_str}")

            monthly_data.append(f"Month {month}: {dasha_str} || {', '.join(transits)}")

        return f"""
NATAL CONTEXT: Ascendant {asc_name} (Index {asc_sign})
D9: {self._format_chart(d9_data['divisional_chart'])}
D10: {self._format_chart(d10_data['divisional_chart'])}
SAV: {', '.join(sav_summary)}

MONTHLY FORENSIC DATA (With Resonance & Hits):
{chr(10).join(monthly_data)}
"""

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
You are an expert Vedic Astrologer using the **"Natal Resonance" Method**.

Your Goal: Predict specific life events for {year}.

INPUT DATA:
{raw_data}

{life_stage_context}

### 1. THE "ALL-SIGNIFICATION" RULE
Do not limit a house to one meaning. Check ALL possibilities for every activated house.

* **12th House Activation:**
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

### 2. THE "ASPECT SCANNER" (Hidden Events)
* Look at the **[HITS: X, Y, Z]** tag. This lists houses aspected by the planet.
* **Sibling Rule:** If Saturn/Mars/Jupiter **HITS H3 or H11**, predict "Event concerning Sibling."
* **Injury Rule:** If Mars/Saturn/Rahu **HITS H8 or H6**, predict "Injury/Health flare-up."

### 3. THE "DASHA" DRIVER
* **The PD Lord is KING.** Whatever house the PD Lord sits in OR ASPECTS (check HITS) becomes the main event.
* If PD Lord is Jupiter in 12H -> The 12th house event (Travel/Expense) IS the prediction.

### OUTPUT JSON:
Predict **multiple distinct events** per month (e.g., one for Travel, one for Family, one for Health).

NOTE: The focus_areas shown below are examples only. Use any relevant life domains based on the astrological data (Career, Health, Finance, Relationships, Family, Travel, Property, Spirituality, Education, Legal, Business, Creativity, Social, etc.).

{{
    "macro_trends": ["Trend 1", "Trend 2", "Trend 3"],
    "monthly_predictions": [
        {{
            "month_id": 1,
            "focus_areas": ["Career", "Health", "Finance", "Relationships", "Family", "Travel", "Property", "Spirituality"],
            "events": [
                {{
                    "type": "Event Type",
                    "prediction": "Detailed prediction citing the Aspect/Hit (e.g., 'Because Saturn aspects House 11 [HITS: 11]...')",
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
            if not self.model: raise Exception("No API Key")
            safety = [{"category": c, "threshold": "BLOCK_NONE"} for c in 
                     ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", 
                      "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            
            resp = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"}, safety_settings=safety)
            return resp.text

        try:
            resp_text = await asyncio.to_thread(run_sync_gemini)
            
            print(f"\n🤖 GEMINI RESPONSE:")
            print("=" * 80)
            print(resp_text)
            print("=" * 80)
            
            return json.loads(resp_text)
        except Exception as e:
            print(f"AI Error: {e}")
            return {"macro_trends": [], "monthly_predictions": []}
