"""Deterministic health activation windows.

The engine never creates a health topic.  It times only findings already
established by :class:`NatalHealthBlueprintEngine`. Mahadasha, Antardasha and
Pratyantardasha establish permission, sustained sidereal transits confirm the
window, the Sun can strengthen a phase, and the Moon can mark a brief peak.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List
import re
from zoneinfo import ZoneInfo

from calculators.real_transit_calculator import RealTransitCalculator
from shared.dasha_calculator import DashaCalculator
from utils.timezone_service import parse_timezone_offset


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
SAMPLE_HOURS = (0, 6, 12, 18)
LEVELS = ("mahadasha", "antardasha", "pratyantardasha")
LEVEL_WEIGHT = {"mahadasha": 2, "antardasha": 3, "pratyantardasha": 4}
# Nodes use conjunction/opposition only.  Their 5th/9th aspects are deliberately
# excluded because those aspects are not consistent across classical lineages.
ASPECT_ANGLES = {
    "Sun": (0, 180), "Moon": (0, 180), "Mars": (0, 90, 180, 210),
    "Mercury": (0, 180), "Jupiter": (0, 120, 180, 240),
    "Venus": (0, 180), "Saturn": (0, 60, 180, 270),
    "Rahu": (0, 180), "Ketu": (0, 180),
}
ORB = {"Moon": 2.0, "Sun": 1.5, "Mercury": 1.5, "Venus": 1.5, "Mars": 2.0,
       "Jupiter": 2.0, "Saturn": 2.0, "Rahu": 2.0, "Ketu": 2.0}
TRANSIT_WEIGHT = {"Moon": 1, "Sun": 2, "Mercury": 2, "Venus": 2, "Mars": 3,
                  "Jupiter": 3, "Saturn": 3, "Rahu": 3, "Ketu": 3}


def _angle_distance(value: float, target: float) -> float:
    difference = abs((value - target) % 360.0)
    return min(difference, 360.0 - difference)


def _planet(chart: Dict[str, Any], name: str) -> Dict[str, Any]:
    row = (chart.get("planets") or {}).get(name)
    return row if isinstance(row, dict) else {}


def _planet_longitude(chart: Dict[str, Any], name: str) -> float | None:
    row = _planet(chart, name)
    try:
        if row.get("longitude") is not None:
            return float(row["longitude"]) % 360.0
        return (float(row["sign"]) * 30.0 + float(row.get("degree") or 0.0)) % 360.0
    except (KeyError, TypeError, ValueError):
        return None


def _period_planet(row: Any) -> str:
    return str(row.get("planet") or "") if isinstance(row, dict) else str(row or "")


def _date_string(value: Any) -> str | None:
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    raw = str(value or "")
    return raw[:10] or None


class HealthTimingHeatmapEngine:
    """Build health activation windows without converting them to probability."""

    def __init__(
        self,
        chart: Dict[str, Any],
        natal_blueprint: Dict[str, Any],
        birth_data: Dict[str, Any],
        *,
        dasha_provider: Callable[[datetime, Dict[str, Any]], Dict[str, Any]] | None = None,
        transit_provider: Callable[[datetime, str], Dict[str, Any]] | None = None,
    ):
        self.chart = chart
        self.blueprint = natal_blueprint
        self.birth_data = birth_data
        self.conditions = natal_blueprint.get("planet_health_contexts") or {}
        dasha = DashaCalculator()
        transits = RealTransitCalculator()
        self.dasha_provider = dasha_provider or (
            lambda day, birth: dasha._resolve_levels_at(birth, day, strict=True)
        )
        self.transit_provider = transit_provider or transits.get_planet_state

    def calculate(self, start_date: date, days: int = 120) -> Dict[str, Any]:
        if days < 1 or days > 366:
            raise ValueError("Health heatmap range must be between 1 and 366 days")
        vulnerabilities = [
            row for row in (self.blueprint.get("vulnerabilities") or [])
            if row.get("eligible_for_timing")
        ]
        output = []
        sensitive = 0
        for offset in range(days):
            current = start_date + timedelta(days=offset)
            candidates_by_finding: Dict[str, Dict[str, Any]] = {}
            for hour in SAMPLE_HOURS:
                local_moment = datetime.combine(current, datetime.min.time()).replace(hour=hour)
                dashas = self.dasha_provider(local_moment, self.birth_data) or {}
                transit_moment = self._transit_moment(local_moment)
                transit_states = {planet: self.transit_provider(transit_moment, planet) for planet in PLANETS}
                for finding in vulnerabilities:
                    result = self._judge_vulnerability(finding, dashas, transit_states)
                    if result is None:
                        continue
                    result["sample_local_time"] = f"{hour:02d}:00"
                    current_best = candidates_by_finding.get(str(result["finding_id"]))
                    if current_best is None or (
                        result["heat_level"], result["evidence_score"]
                    ) > (
                        current_best["heat_level"], current_best["evidence_score"]
                    ):
                        candidates_by_finding[str(result["finding_id"])] = result
            candidates = list(candidates_by_finding.values())
            candidates.sort(key=lambda row: (-row["heat_level"], -row["evidence_score"], row["finding_id"]))
            strongest = candidates[0] if candidates else None
            heat_level = strongest["heat_level"] if strongest else 0
            if heat_level:
                sensitive += 1
            output.append({
                "date": current.isoformat(),
                "heat_level": heat_level,
                "phase": strongest["phase"] if strongest else "no_distinct_activation",
                "primary_finding_id": strongest["finding_id"] if strongest else None,
                "primary_label": strongest["label"] if strongest else None,
                "candidate_count": len(candidates),
                # Windows are built from the complete candidate set. Truncating
                # here created artificial one-day gaps whenever another finding
                # temporarily entered the top four.
                "details": candidates,
            })
        windows = self._build_windows(output)
        return {
            "schema_version": "health.timing_windows.v2",
            "method": "natal_finding_then_three_level_dasha_then_sustained_transit_with_sun_moon_refinement",
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=days - 1)).isoformat(),
            "days": output,
            "windows": windows,
            "period_groups": self._group_overlapping_windows(windows),
            "sensitive_day_count": sensitive,
            "legend": {
                "0": "no_distinct_activation", "1": "mild", "2": "notable",
                "3": "strong", "4": "peak",
            },
            "claim_policy": {
                "heat_is_probability": False,
                "sustained_transit_required_for_window": True,
                "timing_cannot_create_vulnerability": True,
                "node_fifth_ninth_aspects_used": False,
                "sun_moon_are_triggers_not_standalone_diagnosis": True,
                "dasha_levels_used": list(LEVELS),
                "sookshma_prana_used": False,
            },
        }

    @staticmethod
    def _date_ranges(values: List[str]) -> List[Dict[str, str]]:
        """Merge consecutive ISO dates into compact phases."""
        dates = sorted({date.fromisoformat(value) for value in values})
        if not dates:
            return []
        ranges = []
        start = previous = dates[0]
        for current in dates[1:]:
            if current != previous + timedelta(days=1):
                ranges.append({"start_date": start.isoformat(), "end_date": previous.isoformat()})
                start = current
            previous = current
        ranges.append({"start_date": start.isoformat(), "end_date": previous.isoformat()})
        return ranges

    def _build_windows(self, days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge consecutive activations of the same natal finding.

        The daily observations remain in the response for auditability, but
        clients should present these periods. Sun and Moon only refine an
        already established MD/AD/PD plus sustained-transit window.
        """
        occurrences: Dict[str, List[tuple[date, Dict[str, Any]]]] = {}
        for day in days:
            current = date.fromisoformat(day["date"])
            for detail in day.get("details") or []:
                occurrences.setdefault(str(detail["finding_id"]), []).append((current, detail))

        windows = []
        for finding_id, rows in occurrences.items():
            rows.sort(key=lambda item: item[0])
            groups: List[List[tuple[date, Dict[str, Any]]]] = []
            for current, detail in rows:
                if not groups or current != groups[-1][-1][0] + timedelta(days=1):
                    groups.append([])
                groups[-1].append((current, detail))
            for group in groups:
                representative_date, representative = max(
                    group,
                    key=lambda item: (item[1]["heat_level"], item[1]["evidence_score"]),
                )
                sun_dates = [
                    current.isoformat() for current, detail in group
                    if detail.get("activation_summary", {}).get("sun_triggers")
                ]
                moon_observations = []
                for current, detail in group:
                    triggers = detail.get("activation_summary", {}).get("moon_triggers") or []
                    if triggers:
                        moon_observations.append((
                            current,
                            min(float(row.get("orb") or 99.0) for row in triggers),
                        ))
                moon_dates = self._closest_dates_per_pass(moon_observations)
                windows.append({
                    "finding_id": finding_id,
                    "stable_id": finding_id,
                    "label": representative.get("label"),
                    "claim_type": representative.get("claim_type"),
                    "system": representative.get("system"),
                    "body_zones": representative.get("body_zones") or [],
                    "start_date": group[0][0].isoformat(),
                    "end_date": group[-1][0].isoformat(),
                    "active_day_count": len(group),
                    "activation_level": max(detail["heat_level"] for _, detail in group),
                    "judgment": representative.get("judgment"),
                    "phase": "active_window",
                    "sun_phases": self._date_ranges(sun_dates),
                    "moon_peak_dates": moon_dates,
                    "representative_date": representative_date.isoformat(),
                    "detail": representative,
                })
        windows.sort(key=lambda row: (row["start_date"], -row["activation_level"], row["finding_id"]))
        return windows

    @staticmethod
    def _closest_dates_per_pass(observations: List[tuple[date, float]]) -> List[str]:
        """Keep one closest date from each consecutive lunar contact."""
        if not observations:
            return []
        observations.sort(key=lambda item: item[0])
        passes: List[List[tuple[date, float]]] = []
        for current, orb in observations:
            if not passes or current > passes[-1][-1][0] + timedelta(days=1):
                passes.append([])
            passes[-1].append((current, orb))
        closest = [min(rows, key=lambda item: (item[1], item[0])) for rows in passes]
        # A Moon marker is supporting detail, not the product itself. Keep the
        # strongest few passes so it cannot become a second daily calendar.
        return sorted(value.isoformat() for value, _ in sorted(closest, key=lambda item: item[1])[:3])

    @staticmethod
    def _group_overlapping_windows(windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collect findings that truly share dates into one user-facing period.

        Use a common intersection rather than transitive overlap. Otherwise a
        chain of partly overlapping windows can incorrectly turn a whole year
        into one period.
        """
        groups: List[Dict[str, Any]] = []
        for window in sorted(windows, key=lambda row: (row["start_date"], row["end_date"])):
            start = date.fromisoformat(window["start_date"])
            end = date.fromisoformat(window["end_date"])
            if not groups or start > date.fromisoformat(groups[-1]["common_end_date"]):
                groups.append({
                    "group_id": f"{window['start_date']}:{window['finding_id']}",
                    "start_date": window["start_date"],
                    "end_date": window["end_date"],
                    "activation_level": window["activation_level"],
                    "windows": [window],
                    "common_end_date": window["end_date"],
                })
                continue
            group = groups[-1]
            group["windows"].append(window)
            group["activation_level"] = max(group["activation_level"], window["activation_level"])
            if start > date.fromisoformat(group["start_date"]):
                group["start_date"] = window["start_date"]
            if end < date.fromisoformat(group["common_end_date"]):
                group["common_end_date"] = window["end_date"]
                group["end_date"] = window["end_date"]
        for group in groups:
            group.pop("common_end_date", None)
            group["windows"].sort(key=lambda row: (-row["activation_level"], row["finding_id"]))
            group["finding_count"] = len(group["windows"])
        return groups

    def _transit_moment(self, local_moment: datetime) -> datetime:
        """Convert a local calendar observation time to a naive UTC instant."""
        timezone_name = str(self.birth_data.get("timezone") or "UTC")
        try:
            return local_moment.replace(tzinfo=ZoneInfo(timezone_name)).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        except Exception:
            offset = parse_timezone_offset(
                timezone_name,
                self.birth_data.get("latitude"),
                self.birth_data.get("longitude"),
                for_date=local_moment,
            )
            return local_moment.replace(
                tzinfo=timezone(timedelta(hours=float(offset)))
            ).astimezone(timezone.utc).replace(tzinfo=None)

    def _vulnerability_signature(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        explicit_timing_planets = {
            str(value) for value in (
                finding.get("timing_planets") or []
            ) if value
        }
        planets = explicit_timing_planets or {
            str(value) for value in (finding.get("source_planets") or []) if value
        }
        carrier_houses = set()
        mechanism_houses = {
            int(value) for value in (finding.get("timing_houses") or [])
            if str(value).isdigit() and 1 <= int(value) <= 12
        }
        has_explicit_houses = bool(mechanism_houses)
        house_basis: Dict[int, List[str]] = {}
        for delivery in finding.get("planetary_delivery") or []:
            if not explicit_timing_planets and delivery.get("planet"):
                planets.add(str(delivery["planet"]))
            if delivery.get("house"):
                carrier_houses.add(int(delivery["house"]))
        for text in finding.get("supporting_rules") or []:
            for match in re.findall(r"(?:House\s+|H)(\d{1,2})", str(text)):
                house = int(match)
                if 1 <= house <= 12:
                    if has_explicit_houses and house not in mechanism_houses:
                        continue
                    mechanism_houses.add(house)
                    house_basis.setdefault(house, []).append(str(text))
        houses = set(mechanism_houses)
        return {
            "planets": planets,
            "houses": houses,
            "carrier_houses": carrier_houses,
            "mechanism_houses": mechanism_houses,
            "house_basis": house_basis,
        }

    def _dasha_chain(self, dashas: Dict[str, Any], signature: Dict[str, Any]) -> List[Dict[str, Any]]:
        chain = []
        for level in LEVELS:
            period = dashas.get(level) or {}
            planet = _period_planet(period)
            condition = self.conditions.get(planet) or {}
            functional = condition.get("functional_role") or {}
            ruled = {int(value) for value in (functional.get("ruled_houses") or [])}
            natal_house = condition.get("house")
            reasons = []
            if planet in signature["planets"]:
                reasons.append("finding_planet")
            if natal_house in signature["mechanism_houses"]:
                reasons.append("occupies_relevant_house")
            connected = sorted(ruled & signature["mechanism_houses"])
            if connected:
                reasons.append("rules_relevant_house")
            aspected_houses = set()
            if natal_house:
                for angle in ASPECT_ANGLES.get(planet, (0, 180)):
                    if angle == 0:
                        continue
                    aspect_number = int(angle / 30) + 1
                    target = ((int(natal_house) + aspect_number - 2) % 12) + 1
                    if target in signature["mechanism_houses"]:
                        aspected_houses.add(target)
            if aspected_houses:
                reasons.append("aspects_relevant_house")
            modifiers = condition.get("finding_modifiers") or {}
            pressure = len(modifiers.get("pressure") or [])
            support = len(modifiers.get("support") or [])
            chain.append({
                "level": level,
                "planet": planet,
                "start": _date_string(period.get("start")) if isinstance(period, dict) else None,
                "end": _date_string(period.get("end")) if isinstance(period, dict) else None,
                "matched": bool(reasons),
                "reasons": reasons,
                "direct_finding_planet": planet in signature["planets"],
                "natal_house": natal_house,
                "connected_houses": connected,
                "aspected_relevant_houses": sorted(aspected_houses),
                "delivery": "mixed" if pressure and support else "pressure" if pressure else "support" if support else "neutral",
            })
        return chain

    def _transit_contacts(self, states: Dict[str, Dict[str, Any]], signature: Dict[str, Any]) -> List[Dict[str, Any]]:
        contacts = []
        for transit_planet, state in states.items():
            transit_longitude = state.get("longitude")
            if transit_longitude is None:
                continue
            for natal_planet in sorted(signature["planets"]):
                natal_longitude = _planet_longitude(self.chart, natal_planet)
                if natal_longitude is None:
                    continue
                best = None
                for angle in ASPECT_ANGLES[transit_planet]:
                    separation = _angle_distance(float(transit_longitude), (natal_longitude - angle) % 360.0)
                    if separation <= ORB[transit_planet] and (best is None or separation < best[1]):
                        best = (angle, separation)
                if best is None:
                    continue
                condition = self.conditions.get(transit_planet) or {}
                modifiers = condition.get("finding_modifiers") or {}
                pressure = len(modifiers.get("pressure") or [])
                support = len(modifiers.get("support") or [])
                contacts.append({
                    "transit_planet": transit_planet,
                    "natal_planet": natal_planet,
                    "transit_house": self._transit_house(float(transit_longitude)),
                    "transit_sign": int(float(transit_longitude) // 30),
                    "natal_house": _planet(self.chart, natal_planet).get("house"),
                    "aspect_angle": best[0],
                    # Classical graha drishti is communicated by house count:
                    # 210 degrees from Mars is its 8th-house aspect, for example.
                    "aspect_number": int(best[0] / 30) + 1,
                    "orb": round(best[1], 3),
                    "exactness": "close" if best[1] <= ORB[transit_planet] / 2 else "applying_or_separating",
                    "delivery": "mixed" if pressure and support else "pressure" if pressure else "support" if support else (
                        "pressure" if transit_planet in {"Mars", "Saturn", "Rahu", "Ketu"} else
                        "support" if transit_planet in {"Jupiter", "Venus"} else "trigger"
                    ),
                    "returns_to_own_natal_position": transit_planet == natal_planet,
                })
        contacts.sort(key=lambda row: (row["orb"], -TRANSIT_WEIGHT[row["transit_planet"]]))
        return contacts

    def _transit_house(self, longitude: float) -> int:
        try:
            ascendant_sign = int(float(self.chart.get("ascendant")) // 30) % 12
        except (TypeError, ValueError):
            first = next((row for row in (self.chart.get("houses") or []) if row.get("house") == 1), {})
            ascendant_sign = int(first.get("sign") or 0) % 12
        return ((int(longitude // 30) - ascendant_sign) % 12) + 1

    def _transit_house_activations(
        self,
        states: Dict[str, Dict[str, Any]],
        signature: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        activations: Dict[tuple, Dict[str, Any]] = {}
        for planet, state in states.items():
            longitude = state.get("longitude")
            if longitude is None:
                continue
            transit_house = self._transit_house(float(longitude))
            for angle in ASPECT_ANGLES.get(planet, (0, 180)):
                aspect_number = int(angle / 30) + 1
                target = transit_house if angle == 0 else ((transit_house + aspect_number - 2) % 12) + 1
                if target not in signature["houses"]:
                    continue
                key = (planet, target, angle)
                activations[key] = {
                    "transit_planet": planet,
                    "transit_house": transit_house,
                    "transit_sign": int(float(longitude) // 30),
                    "target_house": target,
                    "target_kind": (
                        "health_mechanism" if target in signature["mechanism_houses"]
                        else "carrier_house"
                    ),
                    "mode": "occupation" if angle == 0 else "aspect",
                    "aspect_angle": angle,
                    "aspect_number": aspect_number,
                    "repeats_natal_house": _planet(self.chart, planet).get("house") == transit_house,
                }
        return sorted(
            activations.values(),
            key=lambda row: (
                row["transit_planet"] not in {"Saturn", "Jupiter", "Mars", "Rahu", "Ketu"},
                row["transit_planet"], row["target_house"], row["aspect_angle"],
            ),
        )

    def _activation_summary(
        self,
        chain: List[Dict[str, Any]],
        house_activations: List[Dict[str, Any]],
        contacts: List[Dict[str, Any]],
        signature: Dict[str, Any],
    ) -> Dict[str, Any]:
        dasha_by_house: Dict[int, List[Dict[str, Any]]] = {}
        for row in chain:
            if not row.get("matched"):
                continue
            for house in row.get("connected_houses") or []:
                dasha_by_house.setdefault(house, []).append({
                    "planet": row["planet"], "level": row["level"], "mode": "lordship",
                })
            for house in row.get("aspected_relevant_houses") or []:
                dasha_by_house.setdefault(house, []).append({
                    "planet": row["planet"], "level": row["level"], "mode": "natal_aspect",
                })
            if row.get("natal_house") in signature["mechanism_houses"]:
                dasha_by_house.setdefault(int(row["natal_house"]), []).append({
                    "planet": row["planet"], "level": row["level"], "mode": "natal_occupation",
                })

        transit_by_house: Dict[int, List[Dict[str, Any]]] = {}
        carrier_activations = []
        for row in house_activations:
            if row.get("target_kind") == "carrier_house":
                carrier_activations.append(row)
                continue
            transit_by_house.setdefault(int(row["target_house"]), []).append({
                "planet": row["transit_planet"],
                "mode": row["mode"],
                "from_house": row["transit_house"],
                "aspect_number": row["aspect_number"],
            })

        dasha_houses = sorted(dasha_by_house)
        transit_houses = sorted(transit_by_house)
        overlap = sorted(set(dasha_houses) & set(transit_houses))
        house_rows = []
        for house in sorted(set(dasha_houses) | set(transit_houses)):
            house_rows.append({
                "house": house,
                "dasha_activators": dasha_by_house.get(house, []),
                "transit_activators": transit_by_house.get(house, []),
                "confirmed_by_both": house in overlap,
                "natal_basis": list(signature["house_basis"].get(house, []))[:2],
            })
        return {
            "dasha_houses": dasha_houses,
            "transit_houses": transit_houses,
            "confirmed_houses": overlap,
            "houses": house_rows,
            "carrier_house_activations": carrier_activations[:5],
            "sun_triggers": [row for row in contacts if row["transit_planet"] == "Sun"],
            "moon_triggers": [row for row in contacts if row["transit_planet"] == "Moon"],
            "decisive_contacts": contacts[:4],
        }

    def _judge_vulnerability(
        self,
        finding: Dict[str, Any],
        dashas: Dict[str, Any],
        states: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any] | None:
        signature = self._vulnerability_signature(finding)
        if not signature["planets"]:
            return None
        chain = self._dasha_chain(dashas, signature)
        matched = [row for row in chain if row["matched"]]
        # The practical window must be carried by the Pratyantardasha and at
        # least one enclosing level. Sookshma and Prana are intentionally not
        # calculated or scored.
        has_enclosing_permission = any(row["matched"] for row in chain[:2])
        has_pratyantardasha_permission = bool(chain[2]["matched"])
        if not (has_enclosing_permission and has_pratyantardasha_permission):
            return None
        contacts = self._transit_contacts(states, signature)
        all_house_activations = self._transit_house_activations(states, signature)
        structural_planets = {"Mars", "Jupiter", "Saturn", "Rahu", "Ketu"}
        active_dasha_planets = {row["planet"] for row in chain if row["matched"]}
        structural_contacts = [
            row for row in contacts
            if row["transit_planet"] in structural_planets
            and (
                row["transit_planet"] in active_dasha_planets
                or row["natal_planet"] in active_dasha_planets
            )
        ]
        # A sign/house occupation can last months or years and is background
        # context, not a bounded timing window. Require an exact structural
        # contact to a natal planet carrying this susceptibility.
        if not structural_contacts:
            return None
        luminary_contacts = [row for row in contacts if row["transit_planet"] in {"Sun", "Moon"}]
        dasha_score = sum(LEVEL_WEIGHT[row["level"]] for row in matched)
        retained_contacts = luminary_contacts[:2] + structural_contacts[:3]
        explanatory_planets = {
            row["transit_planet"] for row in retained_contacts
        }
        house_activations = [
            row for row in all_house_activations
            if row["transit_planet"] in explanatory_planets
        ]
        activation_summary = self._activation_summary(
            chain, house_activations, retained_contacts, signature
        )
        activation_summary["condition_link"] = {
            "finding_id": finding.get("stable_id"),
            "label": finding.get("label"),
            "body_zones": list(finding.get("body_zones") or []),
            "natal_planets": sorted(signature["planets"]),
            "natal_houses": sorted(signature["mechanism_houses"]),
            "natal_rules": list(finding.get("supporting_rules") or [])[:5],
            "dasha_repeated_houses": activation_summary["dasha_houses"],
            "transit_repeated_houses": activation_summary["transit_houses"],
            "confirmed_houses": activation_summary["confirmed_houses"],
        }
        structural_planet_count = len({
            row["transit_planet"] for row in structural_contacts
        })
        luminary_planets = {
            row["transit_planet"] for row in luminary_contacts
        }
        transit_score = min(6, structural_planet_count * 2) + sum(
            TRANSIT_WEIGHT[planet] for planet in luminary_planets
        )
        score = dasha_score + transit_score
        has_sun_trigger = "Sun" in luminary_planets
        has_moon_trigger = "Moon" in luminary_planets
        if score >= 12 and has_moon_trigger:
            heat = 4
        elif score >= 10 and has_sun_trigger:
            heat = 3
        elif score >= 8:
            heat = 2
        else:
            heat = 1
        pressure = sum(row["delivery"] in {"pressure", "mixed"} for row in matched + retained_contacts)
        support = sum(row["delivery"] in {"support", "mixed"} for row in matched + retained_contacts)
        if pressure > support:
            judgment = "sensitive_with_limited_support"
        elif pressure and support:
            judgment = "sensitive_with_recovery_support"
        else:
            judgment = "activation_with_support"
        finding_id = str(finding.get("stable_id") or "")
        is_surgery_finding = "surgery" in finding_id
        short_dasha = {chain[2]["planet"]} if chain[2]["matched"] else set()
        has_mars_trigger = any(row["transit_planet"] == "Mars" for row in retained_contacts)
        has_intervention_house = any(
            set(row.get("connected_houses") or []) & {8, 12}
            for row in chain if row["matched"]
        )
        surgery_gate_passed = bool(
            is_surgery_finding and "Mars" in short_dasha and has_mars_trigger and has_intervention_house
        )
        return {
            "finding_id": finding.get("stable_id"),
            "stable_id": finding.get("stable_id"),
            "label": finding.get("label"),
            "claim_type": finding.get("claim_type"),
            "system": finding.get("system"),
            "body_zones": list(finding.get("body_zones") or []),
            "natal_grade": finding.get("evidence_grade") or finding.get("support_grade"),
            "heat_level": heat,
            "phase": "peak" if has_moon_trigger else "heightened" if has_sun_trigger else "active_window",
            "judgment": judgment,
            "manifestation_scope": (
                "surgery_attention" if surgery_gate_passed else
                "body_system_activation" if is_surgery_finding else
                "finding_activation"
            ),
            "surgery_gate": {
                "required": is_surgery_finding,
                "passed": surgery_gate_passed,
                "short_dasha_mars": "Mars" in short_dasha,
                "mars_transit_contact": has_mars_trigger,
                "intervention_house_connection": has_intervention_house,
            },
            "evidence_score": score,
            "score_components": {"dasha": dasha_score, "transit": transit_score},
            "dasha_chain": chain,
            "transit_contacts": retained_contacts,
            "transit_house_activations": house_activations[:10],
            "activation_summary": activation_summary,
            "natal_reasons": list(finding.get("supporting_rules") or [])[:5],
            "protective_factors": list(finding.get("protective_rules") or [])[:5],
            "pressure_factors": list(finding.get("contradicting_rules") or [])[:5],
            "interpretation_rule": "This is a sensitivity marker, not a diagnosis or calibrated probability.",
        }
