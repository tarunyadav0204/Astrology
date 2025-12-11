from datetime import datetime, timedelta
from typing import Dict, List, Any
from types import SimpleNamespace
import calendar
import json
import asyncio
import os
import google.generativeai as genai
# Import safety setting types
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from calculators.divisional_chart_calculator import DivisionalChartCalculator

class EventPredictor:
    """
    AI-Powered Event Predictor using Grand Synthesis method.
    Combines Parashari Dasha, Nadi Transits, and Nakshatra precision.
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
            # Use same models as chat system
            try:
                self.model = genai.GenerativeModel('models/gemini-3-pro-preview')
                print("✅ EventPredictor using Gemini 3.0 Pro Preview")
            except Exception as e:
                try:
                    self.model = genai.GenerativeModel('models/gemini-2.5-flash')
                    print("✅ EventPredictor using Gemini 2.5 Flash")
                except Exception as e2:
                    print(f"❌ Failed to initialize Gemini models: {e}, {e2}")
        else:
            print("⚠️ GEMINI_API_KEY not found. Event predictions will fail.")

    async def predict_yearly_events(self, birth_data: Dict, year: int) -> Dict[str, Any]:
        """Generate AI-powered yearly predictions using Grand Synthesis method"""
        try:
            print(f"🔮 Starting prediction for {year}...")
            raw_data = self._prepare_yearly_data(birth_data, year)
            print(f"✅ Data preparation complete")
            
            prompt = self._create_prediction_prompt(raw_data, year)
            print(f"✅ Prompt creation complete")
            
            # Log what we're sending to Gemini
            print(f"\n🔮 GEMINI PROMPT FOR {year}:")
            print("=" * 80)
            print(prompt)
            print("=" * 80)
            
            ai_response = await self._get_ai_prediction_async(prompt)
            print(f"✅ AI response received: {len(str(ai_response))} characters")
            
            return {
                "year": year,
                "status": "success",
                **ai_response
            }
            
        except Exception as e:
            print(f"❌ PREDICTION ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "year": year,
                "status": "error",
                "error": str(e),
                "macro_trends": ["Unable to generate predictions at this time"],
                "monthly_predictions": []
            }

    def _prepare_yearly_data(self, birth_data: Dict, year: int) -> str:
        """
        Compiles forensic astrological data: D1, D9, D10, SAV Scores, Dashas, Transits.
        """
        # 1. Basic D1 Chart & Natal Positions
        birth_obj = SimpleNamespace(**birth_data)
        d1_chart = self.chart_calc.calculate_chart(birth_obj)
        asc_sign = int(d1_chart['ascendant'] / 30)
        
        # Create a map of Natal Planets for Conjunction checks
        natal_positions = {}
        for planet, data in d1_chart['planets'].items():
            sign = data['sign']
            if sign not in natal_positions:
                natal_positions[sign] = []
            natal_positions[sign].append(planet)
            
        # 2. Divisional Charts (Zoom Lens)
        div_calc = DivisionalChartCalculator(d1_chart)
        d9_data = div_calc.calculate_divisional_chart(9)
        d10_data = div_calc.calculate_divisional_chart(10)
        
        def format_div_positions(chart_data):
            return ", ".join([
                f"{p}: {d['sign_name']}"
                for p, d in chart_data['planets'].items()
                if p in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
            ])

        d9_summary = format_div_positions(d9_data['divisional_chart'])
        d10_summary = format_div_positions(d10_data['divisional_chart'])

        # 3. Ashtakavarga (Signal Strength)
        av_calc = self.ashtakavarga_cls(birth_data, d1_chart)
        sav_data = av_calc.calculate_sarvashtakavarga()
        sav_scores = sav_data['sarvashtakavarga']
        
        # Format scores by HOUSE relative to Ascendant
        sav_summary_list = []
        house_strength_map = {}
        
        for sign_idx, score in sav_scores.items():
            house_num = ((sign_idx - asc_sign) % 12) + 1
            strength = "WEAK" if score < 25 else "STRONG" if score > 30 else "AVG"
            house_strength_map[house_num] = f"{strength} ({score})"
            sav_summary_list.append(f"H{house_num}: {score}")
            
        sav_summary = ", ".join(sorted(sav_summary_list, key=lambda x: int(x.split(':')[0][1:])))
        
        def get_nakshatra(longitude):
            nak_names = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
                        'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
                        'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
                        'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
                        'Uttara Bhadrapada', 'Revati']
            nak_id = int(longitude / 13.333333)
            if nak_id >= len(nak_names): nak_id = len(nak_names) - 1
            return f"{nak_names[nak_id]}"
        
        monthly_data = []
        
        for month in range(1, 13):
            sample_date = datetime(year, month, 15)
            
            # FIX: Dasha context
            dashas = self.dasha_calc.calculate_current_dashas(birth_data, sample_date)
            md = dashas['mahadasha']['planet']
            ad = dashas['antardasha']['planet'] 
            pd = dashas['pratyantardasha']['planet']
            dasha_str = f"MD:{md}-AD:{ad}-PD:{pd}"
            
            # Transit context
            transits = []
            for planet in ['Sun', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Venus', 'Mercury']:
                pos = self.transit_calc.get_planet_position(sample_date, planet)
                if pos is not None:
                    house = self.transit_calc.calculate_house_from_longitude(pos, d1_chart['ascendant'])
                    sign_idx = int(pos / 30)
                    nak_name = get_nakshatra(pos)
                    
                    # CHECK FOR NATAL CONJUNCTION
                    conjunction_str = ""
                    if sign_idx in natal_positions:
                        natal_planets = [p for p in natal_positions[sign_idx] if p != planet]
                        if natal_planets:
                            conjunction_str = f" [CONJUNCT NATAL {' & '.join(natal_planets).upper()}]"
                    
                    strength_str = house_strength_map.get(house, "AVG")
                    transits.append(f"{planet} in {house}H [{strength_str}] ({nak_name}){conjunction_str}")
            
            monthly_data.append(f"Month {month}: {dasha_str} || Transits: {', '.join(transits)}")
        
        # Get native name (first 6 characters)
        native_name = (birth_data.get('name', 'Unknown'))[:6]
        
        return f"""
NATAL CONTEXT ({native_name}):
Ascendant Sign Index: {asc_sign}
D9 NAVAMSA (Inner Strength): {d9_summary}
D10 DASAMSA (Career Detail): {d10_summary}
HOUSE SCORES (SAV Strength): {sav_summary}

MONTHLY FORENSIC DATA:
{chr(10).join(monthly_data)}
"""

    def _create_prediction_prompt(self, raw_data: str, year: int) -> str:
        return f"""
You are an elite Vedic Astrologer using the **"First Principles Physics" method**.

Your Goal: Predict specific life events for the user for {year} by calculating the "Net Energy Vector" of every transit.

INPUT DATA (Forensic Report):
{raw_data}

### UNIVERSAL PHYSICS ENGINE (The "How It Works" Protocol):

For EVERY month, analyze the transits using this 4-step physics calculation. Do not use generic rules; derive the event from the energy.

**STEP 1: The Energy Source (The Planet)**
- **Rahu/Mars/Saturn/Ketu:** These are "High Entropy" sources. They cause disruption, heat, pressure, or breaks.
- **Jupiter/Venus/Mercury/Sun:** These are "Structured" sources. They cause expansion, pleasure, communication, or authority.

**STEP 2: The Container (The House)**
- Where is this energy happening? (4H=Home/Kitchen, 8H=Bathroom/Hidden, 12H=Foreign/Hospital, etc.)

**STEP 3: The Volume (SAV Score)**
- **Score >30 (LOUD):** The event is massive, visible, and physical.
    - *Benefic + High SAV:* Massive Gain/Success.
    - *Malefic + High SAV:* Massive Disruption/Chaos/Explosion. (e.g., Rahu in 4th with 41 pts = Appliance burst/Fire).
- **Score <25 (WEAK):** The event is draining or vulnerable.
    - *Benefic + Low SAV:* Disappointment/Lack of help.
    - *Malefic + Low SAV:* Physical Injury/Pain/Weakness. (e.g., Mars in 8th with 22 pts = Injury/Fall).

**STEP 4: The Trigger (Conjunction/Aspect)**
- Is the Transit Planet touching a Natal Planet? That Natal planet's portfolio *explodes* (if Rahu) or *freezes* (if Saturn).

### PREDICTION INSTRUCTION:
Scan ALL 12 months. For each month, list **ALL significant events** derived from this physics engine. 
- Look for **"High Energy Malefics"** (Potential accidents/chaos).
- Look for **"High Energy Benefics"** (Major success/travel).
- Look for **"Weak Energy Malefics"** (Health vulnerability/injury).

**DO NOT** filter results. If you see a risk of accident, PREDICT IT. If you see travel, PREDICT IT.

### OUTPUT JSON FORMAT:
Return a JSON object with this EXACT structure.

{{
    "macro_trends": [
        "Trend 1", 
        "Trend 2"
    ],
    "monthly_predictions": [
        {{
            "month_id": 1,
            "focus_areas": ["Home Hazard", "Health", "Travel"], 
            "events": [
                {{
                    "type": "Home Hazard",
                    "prediction": "Rahu (Entropy) in 4th House (Kitchen/Home) with Massive SAV (41) creates a 'pressure cooker' environment. High risk of appliance malfunction, gas leak, or domestic chaos.",
                    "intensity": "High"
                }},
                {{
                    "type": "Health/Injury",
                    "prediction": "Mars aspecting 8th House (Bathroom/Sudden) with Low SAV indicates physical vulnerability to slips or falls.",
                    "intensity": "Medium"
                }}
            ]
        }},
        ... (repeat for all 12 months)
    ]
}}
"""

    async def _get_ai_prediction_async(self, prompt: str) -> Dict[str, Any]:
        """Get AI prediction using Gemini (Non-blocking)"""
        
        def run_sync_gemini():
            if not self.model:
                raise Exception("Gemini model not initialized - check GEMINI_API_KEY")
            
            # CRITICAL FIX: Safety settings to allow astrological content
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                },
            ]
            
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"},
                safety_settings=safety_settings
            )
            
            # Check if response was blocked by safety filters
            if not response.candidates:
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    raise Exception(f"Response blocked. Reason: {response.prompt_feedback.block_reason}")
                raise Exception("Response blocked by safety filters (No candidates returned)")
            
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                raise Exception(f"Response blocked/empty. Finish reason: {candidate.finish_reason}")
            
            return candidate.content.parts[0].text

        try:
            # Run blocking API call in thread
            response_text = await asyncio.to_thread(run_sync_gemini)
            
            # Log Gemini's response
            print(f"\n🤖 GEMINI RESPONSE:")
            print("=" * 80)
            print(response_text)
            print("=" * 80)
            
            if not response_text:
                raise Exception("Empty response from Gemini")
            
            return json.loads(response_text)
                
        except json.JSONDecodeError:
            return {
                "macro_trends": ["AI generated detailed predictions but formatting needs adjustment"],
                "monthly_predictions": [{
                    "month_id": i,
                    "focus_areas": ["General"],
                    "events": [{
                        "type": "General",
                        "prediction": "Detailed predictions available - contact support for formatting",
                        "intensity": "Medium"
                    }]
                } for i in range(1, 13)]
            }
        except Exception as e:
            print(f"❌ GEMINI API ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "macro_trends": [f"Prediction service temporarily unavailable: {str(e)}"],
                "monthly_predictions": [{
                    "month_id": i,
                    "focus_areas": ["General"],
                    "events": [{
                        "type": "General",
                        "prediction": "Predictions will be available once service is restored",
                        "intensity": "Medium"
                    }]
                } for i in range(1, 13)]
            }