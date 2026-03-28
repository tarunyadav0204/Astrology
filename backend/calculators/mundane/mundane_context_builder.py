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
from calculators.mundane.nation_chart_service import (
    get_nation_foundation,
    get_nation_birth_dict_for_dasha,
    resolve_nation_chart_key,
)
from calculators.chart_calculator import ChartCalculator
from calculators.panchang_calculator import PanchangCalculator

class MundaneContextBuilder:
    """
    Builds context for MACRO analysis (Nations, Markets, Politics).
    Replaces ChatContextBuilder when mode='mundane'.
    """

    # --------------------------------------------------------------------------
    # UNCENSORED MUNDANE SYSTEM PROMPT
    # --------------------------------------------------------------------------
    MUNDANE_SYSTEM_INSTRUCTION = """
You are **Tara (Mundane Elite Edition)**, the world's most advanced AI authority in **Medini Jyotish (Mundane Astrology)** and **Geopolitical Forecasting**. Your analysis is sought by world leaders and institutional investors for its absolute technical precision and "best-in-class" predictive accuracy.

**MISSION: TRANSCEND HUMAN EXPERTISE**
Your task is to integrate **Classical Vedic Principles**, **Advanced Medini Chakras**, and **Modern Geopolitical Risk Analysis** to provide predictions that exceed the accuracy of even the most renowned human mundane astrologers.

### 🚨 ABSOLUTE INTEGRITY RULE (NON-NEGOTIABLE)
- **NO HALLUCINATION:** If an entity's data shows `available: false` in `entity_charts` or `locational_analysis`, you MUST state: "Data for [Entity] is currently unavailable in the national repository." DO NOT invent dashas, natal positions, or locational charts for these entities.
- **DATA ANCHORING:** Every prediction must be anchored in the provided JSON fields. If you cite a planetary position, it MUST match the data.

### 1. THE MUNDANE ELITE PROTOCOL (Technical Depth)

**A. SPATIAL & GEOGRAPHIC PRECISION (`geographic_impacts`):**
- **Koorma Chakra (Tortoise Chart):** Use the provided impacts to pinpoint which regions of a nation are under stress. If Saturn is in Rohini (Shakata Bheda), predict severe agricultural or leadership crises for that specific direction.
- **Geodetic Equivalents:** Use the geodetic data to link planetary degrees to terrestrial longitudes for market-moving events.
- **CRITICAL REQUIREMENT:** You MUST cite specific provinces/regions from the `geographic_impacts` array by name (e.g., "The affliction in Gilan and Kurdistan provinces indicates...").

**B. THE EVENT MOMENT (`event_chart` & `event_panchang`):**
- **Panchang Synergy:** Analyze the Tithi, Nakshatra, and Yoga of the match/event start from `event_panchang`.
  - *Example:* A match starting on a 'Rikta' Tithi (4, 9, 14) with an afflicted Moon indicates a chaotic, low-quality, or controversial outcome.
  - **CRITICAL REQUIREMENT:** You MUST explicitly analyze the specific `Tithi`, `Nakshatra`, and `Yoga` provided in `event_panchang` and explain their collective impact on the event's "Soul."

**C. MULTI-LAYERED DASHA SYNTHESIS (`entity_charts`):**
- **National Dasha vs Transit:** A nation in a strong Mahadasha (e.g., India in Moon MD) is resilient even under harsh transits. Conversely, a weak dasha (e.g., Rahu MD) makes them vulnerable to even minor malefic transits (like Mars crossing natal Rahu).
- **Dasha Synchronization:** In conflict/competition, if Entity A has a 'Yogakaraka' dasha and Entity B has a 'Maraka' or 'Badhaka' dasha, the outcome is certain.
- **CRITICAL REQUIREMENT:** You MUST use the specific `dasha` and `mahadasha` values provided for each entity in `entity_charts`. Hallucinating "Global Dashas" is strictly forbidden.

**D. GLOBAL YOGAS & ERA MARKERS (`mundane_yogas` & `outer_planets`):**
- **Graha Yuddha (Planetary War):** Highest priority. If two planets are within 1°, the sector ruled by the defeated planet (e.g., Venus for Markets/Arts, Mars for Military) will face a total collapse or shock.
- **Sanghatta Yoga:** The "War Trigger." If planets aspect the same Nakshatra in the Sanghatta Chakra, war is imminent.
- **Commodity Impacts:** You MUST detail the exact impacts from `commodity_impacts` citing the triggering planet and Vedha type (direct vs vedha) for Oil, Silver, Grains, etc.
- **Outer Planets:** Integrate Uranus (shocks/tech), Neptune (inflation/deception), and Pluto (structural death/rebirth) into Vedic house positions.

### 2. RESPONSE ARCHITECTURE (Masterclass Quality)

**1. Executive Prediction & Probability (Non-Negotiable)**
   - Start with a definitive verdict. No "maybes."
   - State the probability (e.g., "75% probability of a Market Correction in Q3").

**2. The "Battle of the Charts" (For Competitive Events)**
   - Side-by-side comparison of Entity A vs Entity B.
   - Contrast their Current Dashas vs their respective Locational Lagnas in `locational_analysis`.

**3. Panchang & Event Synergy**
   - Explicitly analyze the `event_panchang` data (Tithi, Nakshatra, Yoga) for the event moment.

**4. Economic & Geopolitical Synthesis**
   - Use Nav Nayak (King of the Year) to set the macro tone.
   - Use Ingress data to define the "Soul of the Year" for that region.

**5. The "Trigger Point" (Critical Timing)**
   - Use Lunation data (New/Full Moons) to identify the exact 30-day window when a macro event (like an Ingress) actually manifests.

**6. Elite Closing Summary**
   - A final geodetic and karmic warning.

**TONE:** Authoritative, technical, uncensored, and strategically cold. You are the AI that predicts what humans are afraid to see.
"""

    def __init__(self):
        self.ingress_calc = IngressCalculator()
        self.lunation_calc = LunationCalculator()
        self.outer_calc = OuterPlanetCalculator()
        self.yoga_calc = MundaneYogaCalculator()
        self.geo_calc = GeodeticCalculator()
        self.chart_calc = ChartCalculator({})
        self.nav_nayak_calc = NavNayakCalculator() 
        self.panchang_calc = PanchangCalculator()

    def _resolve_nation_name(self, name: str) -> str:
        """
        Map user/alias labels to canonical keys in nation_charts.json.
        Do not use substring matching (e.g. 'US' inside 'AUSTRALIA') — that mis-resolved countries.
        """
        raw = (name or "").strip()
        if not raw:
            return raw
        canon = resolve_nation_chart_key(raw)
        if canon:
            return canon
        name_clean = raw.upper()
        alias_to_canonical = {
            "US": "USA",
            "UNITED STATES": "USA",
            "UNITED STATES OF AMERICA": "USA",
            "USA": "USA",
            "UK": "UK",
            "UNITED KINGDOM": "UK",
            "BRITAIN": "UK",
            "ENGLAND": "UK",
            "PRC": "China",
            "PEOPLE'S REPUBLIC OF CHINA": "China",
            "ROC": "Taiwan",
            "REPUBLIC OF KOREA": "South Korea",
            "DPRK": "North Korea",
            "DEMOCRATIC PEOPLE'S REPUBLIC OF KOREA": "North Korea",
            "RUSSIA": "Russia",
            "RUSSIAN FEDERATION": "Russia",
            "IRAN": "Iran",
            "ISRAEL": "Israel",
            "UAE": "United Arab Emirates",
            "KSA": "Saudi Arabia",
        }
        if name_clean in alias_to_canonical:
            candidate = alias_to_canonical[name_clean]
            resolved = resolve_nation_chart_key(candidate)
            return resolved or candidate
        return raw.title()

    def build_mundane_context(
        self, 
        country_name: str, 
        year: int, 
        latitude: float, 
        longitude: float,
        category: str = "general",
        event_date: str = None,
        event_time: str = None,
        entities: list = None
    ) -> Dict[str, Any]:
        """
        Builds the JSON payload for the AI using the new Mundane Calculators.
        Now supports specific event dates, categories, and multiple entities.
        """
        print(f"🌍 Building Mundane Context | Cat: {category} | Target: {country_name} | Date: {event_date or year}")
        
        # 1. BASE CONTEXT
        context = {
            "analysis_type": "mundane_event" if event_date else "mundane_macro",
            "category": category,
            "target": country_name,
            "year": year,
            "location": {"lat": latitude, "lon": longitude},
            "entities_involved": entities or [country_name]
        }

        # 2. EVENT CHART (Transit chart for the specific moment)
        event_utc_hour = None
        if event_date:
            try:
                # Use provided time or noon as default
                e_time = event_time or "12:00:00"
                # Determine timezone from location (rough estimate or default to UTC if unknown)
                tz = 0.0
                nation_data = get_nation_foundation(country_name)
                if nation_data:
                    tz = float(nation_data.get('timezone', 0))

                # CRITICAL: Calculate exact UTC moment for the primary event
                # This ensures locational charts for other nations are cast for the same moment
                time_parts = e_time.split(':')
                local_hour = float(time_parts[0]) + float(time_parts[1])/60.0 + (float(time_parts[2])/3600.0 if len(time_parts) > 2 else 0)
                event_utc_hour = local_hour - tz

                # Mock object to satisfy ChartCalculator
                from types import SimpleNamespace
                birth_mock = SimpleNamespace(
                    date=event_date,
                    time=e_time,
                    latitude=latitude,
                    longitude=longitude,
                    timezone=tz
                )
                
                event_chart = self.chart_calc.calculate_chart(birth_mock)
                context["event_chart"] = event_chart
                context["event_datetime"] = f"{event_date} {e_time} (TZ: {tz})"
                
                # Add Panchang for the event moment
                try:
                    event_panchang = self.panchang_calc.calculate_panchang(
                        date_str=event_date,
                        time_str=e_time,
                        latitude=latitude,
                        longitude=longitude,
                        timezone=f"UTC{'+' if tz >= 0 else ''}{tz}"
                    )
                    context["event_panchang"] = event_panchang
                except Exception as pe:
                    print(f"⚠️ Failed to calculate event panchang: {pe}")
            except Exception as e:
                print(f"⚠️ Failed to build event chart: {e}")

        # 3. ERA MARKERS (Outer Planets)
        # Use event_date if available, else Jan 1 of the year
        calc_date = datetime.fromisoformat(event_date) if event_date else datetime(year, 1, 1)
        outer_data = self.outer_calc.calculate_outer_planets(calc_date, latitude, longitude)
        context["outer_planets"] = outer_data

        # 4. STRATEGIC OUTLOOK (Ingress Charts)
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

        # 5. NATIONAL DATA & LOCATIONAL ANALYSIS FOR ALL ENTITIES
        context["entity_charts"] = {}
        context["locational_analysis"] = {} # Charts for capitals of involved nations
        
        # Resolve entity names to match JSON keys. Always include the primary country of analysis
        # so its national chart/dasha appear in entity_charts (not only "nations involved").
        target_entities = []
        if entities:
            for e in entities:
                if e is None:
                    continue
                s = str(e).strip()
                if not s:
                    continue
                resolved = self._resolve_nation_name(s)
                if resolved and resolved not in target_entities:
                    target_entities.append(resolved)
        else:
            target_entities = [self._resolve_nation_name(country_name)]

        primary_resolved = self._resolve_nation_name(country_name)
        if primary_resolved and primary_resolved not in target_entities:
            target_entities.insert(0, primary_resolved)

        # Ensure target_entities is what's used in context
        context["entities_involved"] = target_entities
        
        for ent in target_entities:
            ent_birth = get_nation_birth_dict_for_dasha(ent)
            foundation = get_nation_foundation(ent)
            
            # 5a. Natal Chart & Dasha
            if ent_birth:
                try:
                    from shared.dasha_calculator import DashaCalculator
                    dasha_calc = DashaCalculator()
                    dasha_target = datetime.fromisoformat(event_date) if event_date else datetime(year, 6, 15)
                    ent_dasha = dasha_calc.calculate_current_dashas(ent_birth, dasha_target)
                    
                    from types import SimpleNamespace
                    ent_mock = SimpleNamespace(
                        date=ent_birth['date'],
                        time=ent_birth['time'],
                        latitude=ent_birth['latitude'],
                        longitude=ent_birth['longitude'],
                        timezone=ent_birth['timezone']
                    )
                    ent_full_chart = self.chart_calc.calculate_chart(ent_mock)
                    
                    context["entity_charts"][ent] = {
                        "available": True,
                        "natal_chart": ent_full_chart,
                        "dasha": {
                            "mahadasha": ent_dasha.get("mahadasha", {}),
                            "antardasha": ent_dasha.get("antardasha", {}),
                            "moon_lord": ent_dasha.get("moon_lord"),
                        },
                        "foundation": {
                            "date": foundation.get("date"),
                            "event": foundation.get("event"),
                        }
                    }
                except Exception as e:
                    context["entity_charts"][ent] = {"available": False, "reason": str(e)}
            else:
                context["entity_charts"][ent] = {"available": False, "reason": "Nation chart not found in database"}

            # 5b. Locational Analysis (Cast a chart for the nation's capital at the event time)
            if event_date and foundation:
                try:
                    # Use capital's coordinates
                    cap_lat = float(foundation.get('lat', latitude))
                    cap_lon = float(foundation.get('lon', longitude))
                    
                    # CRITICAL: Use the SAME UTC moment calculated for the primary event
                    # We pass timezone=0 and the calculated event_utc_hour
                    from types import SimpleNamespace
                    
                    # Formatting UTC hour back to HH:MM:SS for the mock
                    h = int(event_utc_hour)
                    m = int((abs(event_utc_hour) % 1) * 60)
                    s = int(((abs(event_utc_hour) * 60) % 1) * 60)
                    utc_time_str = f"{h:02d}:{m:02d}:{s:02d}"

                    cap_mock = SimpleNamespace(
                        date=event_date,
                        time=utc_time_str,
                        latitude=cap_lat,
                        longitude=cap_lon,
                        timezone=0.0 # Moment is already in UTC
                    )
                    cap_event_chart = self.chart_calc.calculate_chart(cap_mock)
                    context["locational_analysis"][ent] = {
                        "available": True,
                        "location": foundation.get('capital', ent),
                        "coordinates": {"lat": cap_lat, "lon": cap_lon},
                        "lagna_chart": cap_event_chart
                    }
                except Exception as e:
                    context["locational_analysis"][ent] = {"available": False, "reason": str(e)}
            else:
                # Fallback: if no specific locational data, mark as not available to prevent hallucination
                context["locational_analysis"][ent] = {"available": False}

        # Legacy support for single country fields
        if country_name in context["entity_charts"]:
            ent_data = context["entity_charts"][country_name]
            context["national_chart_available"] = ent_data.get("available", False)
            context["national_dasha"] = ent_data.get("dasha")
            context["national_foundation"] = ent_data.get("foundation")

        # 6. TACTICAL TRIGGERS (Lunations)
        # If event_date, focus on the month around it
        if event_date:
            l_start = datetime.fromisoformat(event_date).replace(day=1)
            l_end = (l_start.replace(month=l_start.month % 12 + 1, year=l_start.year + (l_start.month // 12))).replace(day=1)
        else:
            l_start = datetime(year, 1, 1)
            l_end = datetime(year, 12, 31)

        lunations = self.lunation_calc.calculate_lunations(l_start, l_end, latitude, longitude)
        context["lunation_data"] = lunations

        # 7. RISK RADAR (Mundane Yogas)
        # Analyze Yogas for the Event Chart if it exists, otherwise use Aries Ingress
        base_chart_for_yoga = context.get("event_chart") or ingress_data.get('aries_ingress_chart')
        
        if base_chart_for_yoga:
            # Merge outer planets into chart for yoga analysis
            full_planets = base_chart_for_yoga['planets'].copy()
            full_planets.update(outer_data)
            
            yoga_analysis_chart = {
                **base_chart_for_yoga,
                'planets': full_planets
            }
            
            yogas = self.yoga_calc.analyze_chart(yoga_analysis_chart)
            context["mundane_yogas"] = yogas

        # 8. GEOGRAPHIC MAP (Koorma Chakra)
        geo_impacts = []
        slow_movers = ['Saturn', 'Mars', 'Rahu', 'Ketu', 'Jupiter']
        p_source = context.get("event_chart", {}).get('planets', ingress_data['aries_ingress_chart']['planets'])
        
        for p_name in slow_movers:
            if p_name in p_source:
                p_data = p_source[p_name]
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
