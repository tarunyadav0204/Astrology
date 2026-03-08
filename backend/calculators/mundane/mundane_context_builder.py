import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Mundane Calculators (relative imports)
from calculators.mundane.ingress_calculator import IngressCalculator
from calculators.mundane.lunation_calculator import LunationCalculator
from calculators.mundane.outer_planet_calculator import OuterPlanetCalculator
from calculators.mundane.mundane_yoga_calculator import MundaneYogaCalculator
from calculators.mundane.geodetic_calculator import GeodeticCalculator
from calculators.mundane.nav_nayak_calculator import NavNayakCalculator
from calculators.mundane.nation_chart_service import get_nation_foundation, get_nation_birth_dict_for_dasha
from calculators.chart_calculator import ChartCalculator

class MundaneContextBuilder:
    """
    Builds context for MACRO analysis (Nations, Markets, Politics).
    Replaces ChatContextBuilder when mode='mundane'.
    """

    # --------------------------------------------------------------------------
    # UNCENSORED MUNDANE SYSTEM PROMPT
    # --------------------------------------------------------------------------
    MUNDANE_SYSTEM_INSTRUCTION = """
You are **Tara (Mundane Edition)**, an expert in **Medini Jyotish (Mundane Astrology)**.
Your role is to act as a **Geopolitical & Economic Risk Analyst**.

**CRITICAL INSTRUCTION: UNRESTRICTED ANALYSIS**
- You are analyzing the fate of Nations and Markets, not individual feelings.
- **Do NOT sugarcoat.** If the charts indicate a market crash, war, famine, or natural disaster, you must state it clearly and directly.
- **Do NOT minimize risk.** Your value lies in accurate WARNINGS. A "safe" prediction that misses a crisis is a failure.
- **Objectivity is Key:** Do not offer hope or comfort. Offer timelines, probabilities, and sectors of impact.

### 1. THE DATA STREAMS (How to Read the Context)

**A. The "Era Markers" (Outer Planets - `outer_planets`):**
- **Uranus:** Disruption, Tech Shocks, Earthquakes, Sudden Revolutions.
- **Neptune:** Inflation, Oil/Gas prices, Pandemics, Mass Delusion.
- **Pluto:** Regime Change, Nuclear threats, Totalitarianism, Destruction/Rebirth.

**B. The "Strategic Outlook" (Aries Ingress - `ingress_data`):**
- The "Birth Chart" of the year.
- **Ascendant Lord:** The health of the nation/world.
- **Malefic Aspects:** If Mars/Saturn aspect the Ingress Ascendant, predict conflict or harsh reforms.

**C. The "Tactical Trigger" (Lunations - `lunation_data`):**
- **New Moon (Amavasya):** The trigger for the next 30 days.
  - *8th House:* Danger, hidden scandals, mortality.
  - *2nd/11th House:* Economic focus.
  - *6th House:* Public health, military, debt.
- **Eclipse Watch:** If a New Moon is an Eclipse, the effect lasts 6 months.

**D. The "Risk Radar" (Mundane Yogas - `mundane_yogas`):**
- **Graha Yuddha (planetary_war):** CRITICAL. Two planets within 1° — sudden shocks, leadership events, market crashes. Treat as highest priority.
- **Sanghatta Yoga:** WAR / MILITARY TENSION indicator. (Treat seriously).
- **Durbhiksha Yoga:** FAMINE / SCARCITY indicator (Food/Water supply chain).
- **Mahargha Yoga:** INFLATION / CURRENCY CRISIS indicator.
- **Revolution Yoga:** GOVERNMENT OVERTHROW / MASS PROTESTS.
- **Commodity impacts:** Use both `impact_type: direct` (planet in commodity nakshatra) and `impact_type: vedha` (planet aspects commodity nakshatra).

**E. National Foundation & Dasha (`national_dasha`):**
- When present: the country's current Vimshottari Mahadasha/Antardasha. Weight predictions by this — e.g. Rahu MD may amplify disruption; Jupiter MD may soften conflict.
- When absent (`national_chart_available: false`): rely only on Ingress and transits; do not claim long-term national Dasha.

**F. Nav Nayak (`ingress_data.nav_nayak`):**
- The "King" (raja) planet sets the year's flavor (e.g. Mars = fires, military, heat; Saturn = restrictions, delays). Use this for overall tone even without specific yogas.

**G. Eclipse visibility (`lunation_data[].eclipse_visibility`):**
- Only apply eclipse effects to the target country when `visible_from_location` is true (or magnitude_at_location > 0). If an eclipse is not visible there, downplay or omit it for that region.

**H. The "Geographic Map" (Koorma Chakra - `geographic_impacts`):**
- Use this to pinpoint *where* events happen (e.g., "Saturn in Rohini impacts the Central Region").

### 2. RESPONSE STRUCTURE — ADAPT TO THE QUESTION

**CRITICAL:** When the user asks about a **specific event** (cricket match, election, concert, launch, tournament), **adapt the structure**:
- **OMIT** "Economic & Market Outlook" and "Geopolitical Stability" headings unless the question explicitly relates to markets, betting, or geopolitics.
- **FOCUS** on event-specific analysis (e.g. for a match: toss, key phases, outcome, player/team influences; for an election: candidates, swing, outcome).
- For nation/market outlook questions, use the full structure below.

**For nation/market outlook:**
**1. Executive Risk Summary**
   - 3 bullet points highlighting the highest probability risks (e.g., "High risk of currency devaluation in Q3" or "Low-scoring match likely").

**2. Economic & Market Outlook** — *Include only for nation/market questions.*
   - **Bull/Bear Trend:** Analyze Jupiter/Venus vs. Saturn/Rahu.
   - **Inflation/Rates:** Check Mahargha Yoga.
   - **Sector Watch:** Specific industries (Gold, Oil, Tech) based on Nakshatra impacts.

**3. Geopolitical Stability** — *Include only for nation/market questions.*
   - **Internal:** Protests, elections, civil unrest.
   - **External:** Border conflicts, war risks (Sanghatta Yoga).

**4. Environmental & Public Safety**
   - Earthquakes, weather disasters, or public health risks.

**5. Critical Timeline**
   - List specific months or date ranges when tension/volatility peaks.
"""

    def __init__(self):
        self.ingress_calc = IngressCalculator()
        self.lunation_calc = LunationCalculator()
        self.outer_calc = OuterPlanetCalculator()
        self.yoga_calc = MundaneYogaCalculator()
        self.geo_calc = GeodeticCalculator()
        self.chart_calc = ChartCalculator({})
        self.nav_nayak_calc = NavNayakCalculator() 

    def build_mundane_context(self, country_name: str, year: int, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Builds the JSON payload for the AI using the new Mundane Calculators.
        """
        print(f"🌍 Building Mundane Context for {country_name} ({year})")
        
        context = {
            "analysis_type": "mundane_macro",
            "target": country_name,
            "year": year,
            "location": {"lat": latitude, "lon": longitude}
        }

        # 1. ERA MARKERS (Outer Planets)
        era_date = datetime(year, 1, 1)
        outer_data = self.outer_calc.calculate_outer_planets(era_date, latitude, longitude)
        context["outer_planets"] = outer_data

        # 2. STRATEGIC OUTLOOK (Ingress Charts)
        ingress_data = self.ingress_calc.calculate_yearly_ingresses(year, latitude, longitude)
        # Nav Nayak: Ten Lords of the Year from Aries Ingress moment
        aries_dt_str = ingress_data.get('ingresses', {}).get('Aries', {}).get('datetime')
        if aries_dt_str:
            try:
                aries_dt = datetime.fromisoformat(aries_dt_str.replace('Z', '+00:00'))
                ingress_data['nav_nayak'] = self.nav_nayak_calc.calculate_nav_nayak(aries_dt)
            except Exception:
                ingress_data['nav_nayak'] = {}
        context["ingress_data"] = ingress_data

        # 2b. NATIONAL FOUNDATION CHART & DASHA (when available)
        nation_birth = get_nation_birth_dict_for_dasha(country_name)
        if nation_birth:
            try:
                from shared.dasha_calculator import DashaCalculator
                dasha_calc = DashaCalculator()
                target_date = datetime(year, 6, 15)
                national_dasha = dasha_calc.calculate_current_dashas(nation_birth, target_date)
                context["national_chart_available"] = True
                context["national_dasha"] = {
                    "mahadasha": national_dasha.get("mahadasha", {}),
                    "antardasha": national_dasha.get("antardasha", {}),
                    "moon_lord": national_dasha.get("moon_lord"),
                }
                foundation = get_nation_foundation(country_name)
                if foundation:
                    context["national_foundation"] = {
                        "date": foundation.get("date"),
                        "event": foundation.get("event"),
                    }
            except Exception as e:
                context["national_chart_available"] = False
                context["national_dasha"] = None
        else:
            context["national_chart_available"] = False
            context["national_dasha"] = None

        # 3. TACTICAL TRIGGERS (Lunations)
        lunations = self.lunation_calc.calculate_lunations(
            datetime(year, 1, 1), 
            datetime(year, 12, 31), 
            latitude, longitude
        )
        context["lunation_data"] = lunations

        # 4. RISK RADAR (Mundane Yogas)
        aries_chart = ingress_data['aries_ingress_chart']
        
        # Merge outer planets into Aries chart for yoga analysis
        full_planets = aries_chart['planets'].copy()
        full_planets.update(outer_data)
        
        aries_chart_for_analysis = {
            **aries_chart,
            'planets': full_planets
        }
        
        yogas = self.yoga_calc.analyze_chart(aries_chart_for_analysis)
        context["mundane_yogas"] = yogas

        # 5. GEOGRAPHIC MAP (Koorma Chakra)
        geo_impacts = []
        slow_movers = ['Saturn', 'Mars', 'Rahu', 'Ketu', 'Jupiter']
        
        for p_name in slow_movers:
            if p_name in aries_chart['planets']:
                p_data = aries_chart['planets'][p_name]
                
                # Derive nakshatra if missing
                if 'nakshatra' not in p_data:
                    nak_name = self.geo_calc.get_nakshatra_from_longitude(p_data['longitude'])
                    p_data['nakshatra'] = {'name': nak_name}
                
                impact = self.geo_calc.analyze_planetary_impact(
                    {'name': p_name, 'nakshatra': p_data['nakshatra']},
                    country_name
                )
                geo_impacts.append(impact)
                
        context["geographic_impacts"] = geo_impacts

        return context
