import sys
import os
from datetime import datetime, timedelta, timezone
import pytz
from calculators.mundane.astronomy import chart_at
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
from calculators.mundane.sports_scorecard import SportsMundaneScorecard
from calculators.mundane.nation_chart_service import (
    get_nation_foundation,
    get_nation_birth_dict_for_dasha,
    resolve_nation_chart_key,
)
from calculators.chart_calculator import ChartCalculator
from panchang.panchang_calculator import PanchangCalculator

class MundaneContextBuilder:
    """
    Builds context for MACRO analysis (Nations, Markets, Politics).
    Replaces ChatContextBuilder when mode='mundane'.
    """

    # --------------------------------------------------------------------------
    # UNCENSORED MUNDANE SYSTEM PROMPT
    # --------------------------------------------------------------------------
    MUNDANE_SYSTEM_INSTRUCTION = """
You are Tara, interpreting calculated mundane astrology evidence.
Answer the actual question and requested horizon using only the supplied calculations.

EVIDENCE INTEGRITY:
- Read mundane_authoritative_summary first. Cite loaded national periods accurately;
  do not invent missing charts, periods, transitions, aspect doctrines or user facts.
- National foundations are declared conventions with unverified historical sources/times;
  identify the chart basis and account for that uncertainty, especially for disputed charts.
- Distinguish event evidence from yearly background. event_time_assumed means noon
  is a placeholder: do not infer an exact event outcome from its ascendant/houses.
- event_chart_status failures are missing evidence, not negative event indications.
- Ingress/lunation datetime fields are UTC; use explicit timezone metadata.
- nav_nayak is partial. Aries ingress supplies only the Minister when available.
  Raja and other unresolved offices must not be invented or inferred from a planet rotation.
- Graha Yuddha rows are proximity candidates, not calculated victory or defeat.
  Other mundane_yogas and commodity links are explicitly unvalidated heuristics.
  Do not rename them as Sanghatta, Parivartana, or classical Sarvatobhadra Vedha.
- Geographic regions are modern editorial analogies, not measured impact locations;
  never turn these mappings into definite province-specific disaster forecasts.
- Outer planets are a modern supplementary method, not classical Vedic grahas.
- National dasha snapshots cover their declared focus instant, not an entire forecast horizon.
  Do not fabricate future dasha changes or day/hour timing absent calculations.

SPORTS:
- sports_scorecard is a heuristic comparison, not an empirically calibrated probability.
  When available, explain the score reasons and retain its stated relative edge.
- confidence_percent is a legacy heuristic index. Never present it as a win probability.
- balanced means no favored side; draw_or_extra_time is a legacy balanced hint,
  not proof that the sporting rules allow a draw or that extra time will occur.
- If sides have no explicit verified ascendant assignment, identify the input-order
  assumption and keep the conclusion conditional. Missing scorecard is not a winner.
- Do not invent minute-by-minute events, VAR, red cards or turning-point times.

PRESENTATION:
Start with the supported assessment and its scope. Explain concrete supporting and
opposing evidence, compare entities where relevant, and give timing only at calculated
precision. Separate calculations, interpretive rules and practical context. No invented
percentages, certainty mandates, guaranteed outcomes or sensational warnings.
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
        self.sports_scorecard = SportsMundaneScorecard()

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
        entities: list = None,
        venue_name: str = None,
        venue_latitude: float = None,
        venue_longitude: float = None,
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
            "venue": {
                "name": venue_name,
                "lat": venue_latitude if venue_latitude is not None else latitude,
                "lon": venue_longitude if venue_longitude is not None else longitude,
            },
            "entities_involved": entities or [country_name]
        }

        # 2. EVENT CHART (Transit chart for the specific moment)
        event_utc = None
        event_local = None
        tz = 0.0
        if event_date:
            try:
                # Use provided time or noon as default
                e_time = event_time or "12:00:00"
                event_latitude = venue_latitude if venue_latitude is not None else latitude
                event_longitude = venue_longitude if venue_longitude is not None else longitude
                # Determine timezone from actual event coordinates on the backend
                from utils.timezone_service import get_iana_timezone, format_utc_offset
                timezone_name = get_iana_timezone(event_latitude, event_longitude)
                naive_local = datetime.fromisoformat(f"{event_date}T{e_time}")
                # Reject nonexistent/ambiguous wall times rather than guessing a DST fold.
                event_local = pytz.timezone(timezone_name).localize(naive_local, is_dst=None)
                tz = event_local.utcoffset().total_seconds() / 3600
                event_utc = event_local.astimezone(timezone.utc).replace(tzinfo=None)

                # Mock object to satisfy ChartCalculator
                from types import SimpleNamespace
                birth_mock = SimpleNamespace(
                    date=event_utc.date().isoformat(),
                    time=event_utc.time().isoformat(),
                    latitude=event_latitude,
                    longitude=event_longitude,
                    timezone=0.0
                )
                
                event_chart = self.chart_calc.calculate_chart(birth_mock)
                context["event_chart"] = event_chart
                context["event_datetime"] = event_local.isoformat()
                context["event_datetime_utc"] = event_utc.isoformat() + "Z"
                context["event_time_assumed"] = not bool(event_time)
                context["event_location"] = {
                    "name": venue_name or country_name,
                    "latitude": event_latitude,
                    "longitude": event_longitude,
                    "timezone_offset": tz,
                    "timezone": timezone_name,
                }
                
                # Add Panchang for the event moment
                try:
                    event_panchang = self.panchang_calc.calculate_panchang(
                        date_str=event_date,
                        time_str=e_time,
                        latitude=event_latitude,
                        longitude=event_longitude,
                        timezone=format_utc_offset(tz)
                    )
                    context["event_panchang"] = event_panchang
                except Exception as pe:
                    print(f"⚠️ Failed to calculate event panchang: {pe}")
            except Exception as e:
                context['event_chart_status'] = {'available': False, 'reason': 'event_time_or_timezone_unresolved'}
                event_utc = None
                print(f"⚠️ Failed to build event chart: {e}")

        # 3. ERA MARKERS (Outer Planets)
        # Use event_date if available, else Jan 1 of the year
        calc_date = event_utc if event_utc is not None else datetime(year, 1, 1)
        event_latitude = venue_latitude if venue_latitude is not None else latitude
        event_longitude = venue_longitude if venue_longitude is not None else longitude
        outer_data = self.outer_calc.calculate_outer_planets(calc_date, event_latitude, event_longitude)
        context["outer_planets"] = outer_data
        context["outer_planets_datetime_utc"] = calc_date.isoformat() + 'Z'
        context["calculation_contract_version"] = 2

        # 4. STRATEGIC OUTLOOK (Ingress Charts)
        ingress_data = self.ingress_calc.calculate_yearly_ingresses(year, event_latitude, event_longitude)
        # Only the independently supported Aries-ingress Minister is supplied.
        aries_dt_str = ingress_data.get('ingresses', {}).get('Aries', {}).get('datetime')
        if aries_dt_str:
            try:
                aries_dt = datetime.fromisoformat(aries_dt_str.replace('Z', '+00:00'))
                ingress_data['nav_nayak'] = self.nav_nayak_calc.calculate_nav_nayak(aries_dt, latitude=event_latitude, longitude=event_longitude)
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

        sports_entities = list(target_entities)
        primary_resolved = self._resolve_nation_name(country_name)
        if primary_resolved and primary_resolved not in target_entities:
            target_entities.insert(0, primary_resolved)

        # Ensure target_entities is what's used in context
        context["entities_involved"] = target_entities
        
        for ent in target_entities:
            foundation = get_nation_foundation(ent)
            try:
                ent_birth = get_nation_birth_dict_for_dasha(ent)
            except ValueError as exc:
                context['entity_charts'][ent] = {'available': False, 'reason': str(exc)}
                ent_birth = None
            
            # 5a. Natal Chart & Dasha
            if ent_birth:
                try:
                    from shared.dasha_calculator import DashaCalculator
                    dasha_calc = DashaCalculator()
                    # Dasha calculator uses the foundation's civil time scale.
                    focus_utc = event_utc if event_utc is not None else datetime(year, 6, 15)
                    dasha_target = focus_utc + timedelta(hours=ent_birth['timezone'])
                    ent_dasha = dasha_calc.calculate_current_dashas(ent_birth, dasha_target, strict=True)
                    
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
                            "as_of": dasha_target.isoformat(),
                            "time_basis": "foundation_fixed_offset_civil_time",
                            "timezone_offset": ent_birth['timezone'],
                        },
                        "foundation": {
                            "date": foundation.get("date"),
                            "event": foundation.get("event"),
                            "source": foundation.get("source"),
                            "time": ent_birth['time'],
                            "latitude": ent_birth['latitude'],
                            "longitude": ent_birth['longitude'],
                            "timezone_offset": ent_birth['timezone'],
                            "reliability": "unverified_foundation_record",
                            "warning": "Foundation chart is a declared convention; historical time/source require independent verification.",
                        }
                    }
                except Exception as e:
                    context["entity_charts"][ent] = {"available": False, "reason": str(e)}
            else:
                context["entity_charts"].setdefault(ent, {"available": False, "reason": "Nation chart not found in database"})

            # 5b. Locational Analysis (Cast a chart for the nation's capital at the event time)
            if event_utc is not None and foundation:
                try:
                    # Foundation cities can differ from capitals (USA, Israel).
                    from pathlib import Path
                    import json
                    countries = json.loads((Path(__file__).resolve().parents[2] / 'data' / 'mundane_countries.json').read_text())
                    capital_record = next((row for row in countries if self._resolve_nation_name(row['name']) == ent), None)
                    if not capital_record:
                        raise ValueError('Capital coordinates unavailable')
                    cap_lat, cap_lon = float(capital_record['lat']), float(capital_record['lng'])
                    cap_mock = SimpleNamespace(date=event_utc.date().isoformat(), time=event_utc.time().isoformat(),
                                               latitude=cap_lat, longitude=cap_lon, timezone=0.0)
                    cap_event_chart = self.chart_calc.calculate_chart(cap_mock)
                    context["locational_analysis"][ent] = {
                        "available": True,
                        "location": capital_record.get('capital') or foundation.get('capital', ent),
                        "datetime_utc": event_utc.isoformat() + 'Z',
                        "coordinates": {"lat": cap_lat, "lon": cap_lon},
                        "lagna_chart": cap_event_chart
                    }
                except Exception as e:
                    context["locational_analysis"][ent] = {"available": False, "reason": str(e)}
            else:
                reason = None
                if not event_date:
                    reason = "no_event_date"
                elif not foundation:
                    reason = "nation_foundation_missing"
                elif event_utc is None:
                    reason = "event_utc_not_computed"
                context["locational_analysis"][ent] = {"available": False, "reason": reason or "locational_skipped"}

        # Compact summary for the LLM (full chart JSON is large; models often miss nested `available: true`).
        mundane_authoritative_summary = {"entities": {}, "instruction": "Use this block first. If national_dasha_loaded is true, dasha data exists — do not claim national repository is empty for that entity."}
        for ent in target_entities:
            ec = context["entity_charts"].get(ent, {})
            loc = context["locational_analysis"].get(ent, {})
            row = {
                "national_dasha_loaded": bool(ec.get("available")),
                "locational_chart_loaded": bool(loc.get("available")),
            }
            if ec.get("available"):
                md = (ec.get("dasha") or {}).get("mahadasha") or {}
                ad = (ec.get("dasha") or {}).get("antardasha") or {}
                row["vimshottari_mahadasha_planet"] = md.get("planet")
                row["vimshottari_antardasha_planet"] = ad.get("planet")
                row["national_foundation_event"] = (ec.get("foundation") or {}).get("event")
            else:
                row["national_chart_reason"] = ec.get("reason")
            if loc.get("available"):
                row["locational_capital"] = loc.get("location")
            else:
                row["locational_reason"] = loc.get("reason")
            mundane_authoritative_summary["entities"][ent] = row
        context["mundane_authoritative_summary"] = mundane_authoritative_summary

        # Legacy support for single country fields (use resolved primary key)
        if primary_resolved in context["entity_charts"]:
            ent_data = context["entity_charts"][primary_resolved]
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
            l_end = datetime(year + 1, 1, 1)

        if event_local is not None:
            local_zone = pytz.timezone(timezone_name)
            l_start = local_zone.localize(l_start).astimezone(timezone.utc)
            l_end = local_zone.localize(l_end).astimezone(timezone.utc)
        lunations = self.lunation_calc.calculate_lunations(l_start, l_end, event_latitude, event_longitude)
        context["lunation_data"] = lunations

        # 7. RISK RADAR (Mundane Yogas)
        # Analyze Yogas for the Event Chart if it exists, otherwise use Aries Ingress
        base_chart_for_yoga = context.get("event_chart") or ingress_data.get('aries_ingress_chart')
        
        if base_chart_for_yoga:
            # Merge outer planets into chart for yoga analysis
            full_planets = base_chart_for_yoga['planets'].copy()
            # Outer positions must match the base chart instant, not a different date.
            yoga_datetime = event_utc if context.get('event_chart') else datetime.fromisoformat(ingress_data['ingresses']['Aries']['datetime'])
            full_planets.update(self.outer_calc.calculate_outer_planets(yoga_datetime, event_latitude, event_longitude))
            
            yoga_analysis_chart = {
                **base_chart_for_yoga,
                'planets': full_planets
            }
            
            yogas = self.yoga_calc.analyze_chart(yoga_analysis_chart)
            context["mundane_yogas"] = yogas

        if (
            str(category or "").strip().lower() == "sports"
            and event_date
            and event_time
            and len(sports_entities) == 2
            and context.get("event_chart")
        ):
            try:
                context["sports_scorecard"] = self.sports_scorecard.build(
                    entities=sports_entities,
                    event_chart=context.get("event_chart"),
                    event_panchang=context.get("event_panchang"),
                    entity_charts=context.get("entity_charts") or {},
                    locational_analysis=context.get("locational_analysis") or {},
                    latitude=event_latitude,
                    longitude=event_longitude,
                    event_date=event_date,
                    event_time=event_time or "12:00:00",
                    timezone_offset=tz if event_date else 0.0,
                )
            except Exception as e:
                context["sports_scorecard"] = {"available": False, "reason": str(e)}

        if str(category or '').strip().lower() == 'sports' and 'sports_scorecard' not in context:
            context['sports_scorecard'] = {'available': False,
                'reason': 'Two confirmed sides and an actual event date/time/chart are required'}

        # 8. GEOGRAPHIC MAP (Koorma Chakra)
        geo_impacts = []
        slow_movers = ['Saturn', 'Mars', 'Rahu', 'Ketu', 'Jupiter']
        p_source = context.get("event_chart", {}).get('planets') or ingress_data['aries_ingress_chart']['planets']
        
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
