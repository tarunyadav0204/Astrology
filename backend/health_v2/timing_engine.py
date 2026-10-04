"""Deterministic health activation windows.

The engine never creates a health topic.  It times only findings already
established by :class:`NatalHealthBlueprintEngine`. Mahadasha, Antardasha and
Pratyantardasha establish permission, sustained sidereal transits confirm the
window, and a Sun contact or an exact contact within the active dasha chain can
concentrate it.  The Moon may refine a day inside that concentration; it does
not create a peak by itself.
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
REFINEMENT_LEVELS = ("sookshma", "prana")
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
HEALTH_MANIFESTATION_HOUSES = {1, 8, 12}
STRUCTURAL_PLANETS = {"Mars", "Jupiter", "Saturn", "Rahu", "Ketu"}
TRANSIT_BRIDGE_ORB = {"Mars": 4.0, "Jupiter": 5.0, "Saturn": 5.0, "Rahu": 3.0, "Ketu": 3.0}
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}


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
                        result["heat_level"], -self._fast_trigger_exactness(result),
                        result["evidence_score"],
                    ) > (
                        current_best["heat_level"], -self._fast_trigger_exactness(current_best),
                        current_best["evidence_score"],
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
        period_groups = self._group_overlapping_windows(windows)
        public_windows = [
            {key: value for key, value in window.items() if key != "_daily_details"}
            for window in windows
        ]
        return {
            "schema_version": "health.timing_windows.v2",
            "method": "natal_finding_then_three_level_dasha_then_sustained_transit_with_bounded_fast_trigger_refinement",
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=days - 1)).isoformat(),
            "days": output,
            "windows": public_windows,
            "period_groups": period_groups,
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
                "moon_alone_cannot_create_peak": True,
                "active_dasha_lord_direct_transit_can_concentrate_window": True,
                "active_dasha_chain_exact_contact_can_concentrate_window": True,
                "dasha_levels_used": list(LEVELS),
                "sookshma_prana_used": False,
                "sookshma_prana_permission_used": False,
                "sookshma_prana_refinement_used": True,
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

    @staticmethod
    def _concentration_ranges(
        sun_dates: List[str],
        sun_basis: str | None,
        active_dasha_transit_dates: List[str],
    ) -> List[Dict[str, Any]]:
        """Merge concentration dates without losing simultaneous trigger types."""
        bases_by_date: Dict[date, set[str]] = {}
        if sun_basis:
            for value in sun_dates:
                bases_by_date.setdefault(date.fromisoformat(value), set()).add(sun_basis)
        for value in active_dasha_transit_dates:
            bases_by_date.setdefault(date.fromisoformat(value), set()).add(
                "active_dasha_chain_exact_contact"
            )
        if not bases_by_date:
            return []
        priority = {
            "anatomical_specificity_and_sun": 0,
            "sun": 1,
            "active_dasha_chain_exact_contact": 2,
        }
        ordered = sorted(bases_by_date)
        output = []
        start = previous = ordered[0]
        current_bases = tuple(sorted(bases_by_date[start], key=lambda value: priority.get(value, 9)))
        for current in ordered[1:]:
            next_bases = tuple(sorted(bases_by_date[current], key=lambda value: priority.get(value, 9)))
            if current != previous + timedelta(days=1) or next_bases != current_bases:
                output.append({
                    "start_date": start.isoformat(),
                    "end_date": previous.isoformat(),
                    "basis": current_bases[0],
                    "bases": list(current_bases),
                })
                start = current
                current_bases = next_bases
            previous = current
        output.append({
            "start_date": start.isoformat(),
            "end_date": previous.isoformat(),
            "basis": current_bases[0],
            "bases": list(current_bases),
        })
        return output

    @staticmethod
    def _fast_trigger_exactness(detail: Dict[str, Any]) -> float:
        summary = detail.get("activation_summary") or {}
        triggers = (
            list(summary.get("sun_triggers") or [])
            + list(summary.get("active_dasha_transit_triggers") or [])
        )
        return min((float(row.get("orb") or 99.0) for row in triggers), default=99.0)

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
                    key=lambda item: (
                        item[1]["heat_level"],
                        -self._fast_trigger_exactness(item[1]),
                        item[1]["evidence_score"],
                    ),
                )
                sun_dates = [
                    current.isoformat() for current, detail in group
                    if detail.get("activation_summary", {}).get("sun_triggers")
                ]
                active_dasha_transit_dates = [
                    current.isoformat() for current, detail in group
                    if detail.get("activation_summary", {}).get("active_dasha_transit_triggers")
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
                anatomical_sun_dates = [
                    current.isoformat() for current, detail in group
                    if detail.get("score_components", {}).get("anatomical_specificity", 0) > 0
                    and detail.get("activation_summary", {}).get("sun_triggers")
                ]
                sun_concentration_dates = anatomical_sun_dates or sun_dates
                sun_basis = (
                    "anatomical_specificity_and_sun" if anatomical_sun_dates else
                    "sun" if sun_dates else None
                )
                key_concentration_phases = self._concentration_ranges(
                    sun_concentration_dates, sun_basis, active_dasha_transit_dates
                )
                concentration_bases = {
                    basis
                    for phase in key_concentration_phases
                    for basis in phase.get("bases") or [phase["basis"]]
                }
                key_concentration_basis = (
                    next(iter(concentration_bases)) if len(concentration_bases) == 1 else
                    "multiple" if concentration_bases else None
                )
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
                    "evidence_score": max(detail["evidence_score"] for _, detail in group),
                    "judgment": representative.get("judgment"),
                    "phase": "active_window",
                    "sun_phases": self._date_ranges(sun_dates),
                    "active_dasha_transit_phases": self._date_ranges(active_dasha_transit_dates),
                    "moon_peak_dates": moon_dates,
                    "key_concentration_phases": key_concentration_phases,
                    "key_concentration_basis": key_concentration_basis,
                    "lower_dasha_phases": self._lower_dasha_phases(group),
                    "representative_date": representative_date.isoformat(),
                    "detail": representative,
                    "_daily_details": [
                        {"date": current.isoformat(), "detail": detail}
                        for current, detail in group
                    ],
                })
        windows.sort(key=lambda row: (
            row["start_date"], -row["activation_level"], -row["evidence_score"], row["finding_id"]
        ))
        return windows

    def _lower_dasha_phases(
        self,
        group: List[tuple[date, Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        observations: Dict[tuple[str, str], List[str]] = {}
        for current, detail in group:
            mechanism_houses = set(
                (detail.get("activation_summary") or {})
                .get("condition_link", {})
                .get("natal_houses", [])
            )
            for row in detail.get("refinement_dasha_chain") or []:
                # Sookshma may describe the shorter background within the
                # permitted MD/AD/PD window.  Prana is retained only when it
                # directly repeats the finding or occupies its mechanism
                # house; otherwise the UI becomes a list of every Prana.
                is_decisive_prana = bool(
                    row.get("direct_finding_planet")
                    or row.get("natal_house") in mechanism_houses
                    or row.get("associated_finding_planets")
                    or row.get("dispositor_finding_planets")
                    or row.get("nakshatra_lord_finding_planets")
                )
                if row.get("matched") and (row.get("level") == "sookshma" or is_decisive_prana):
                    observations.setdefault((row["level"], row["planet"]), []).append(current.isoformat())
        output = []
        for (level, planet), values in observations.items():
            for period in self._date_ranges(values):
                output.append({"level": level, "planet": planet, **period})
        refinement_order = {"sookshma": 0, "prana": 1}
        return sorted(output, key=lambda row: (
            row["start_date"], refinement_order.get(row["level"], 9), row["planet"]
        ))

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
    def _window_for_segment(
        window: Dict[str, Any],
        start: date,
        end: date,
    ) -> Dict[str, Any]:
        """Create a period-local view of a longer finding window."""
        observations = [
            row for row in window.get("_daily_details") or []
            if start <= date.fromisoformat(row["date"]) <= end
        ]
        segment = {
            key: value for key, value in window.items()
            if key != "_daily_details"
        }
        segment["start_date"] = start.isoformat()
        segment["end_date"] = end.isoformat()
        segment["active_day_count"] = len(observations)
        if observations:
            representative = max(
                observations,
                key=lambda row: (
                    row["detail"].get("score_components", {}).get("anatomical_specificity", 0),
                    row["detail"]["heat_level"],
                    -HealthTimingHeatmapEngine._fast_trigger_exactness(row["detail"]),
                    row["detail"]["evidence_score"],
                    row["date"],
                ),
            )
            segment["representative_date"] = representative["date"]
            segment["detail"] = representative["detail"]
            segment["activation_level"] = max(row["detail"]["heat_level"] for row in observations)
            segment["evidence_score"] = max(row["detail"]["evidence_score"] for row in observations)

        def clipped_phases(key: str) -> List[Dict[str, Any]]:
            phases = []
            for phase in window.get(key) or []:
                phase_start = max(start, date.fromisoformat(phase["start_date"]))
                phase_end = min(end, date.fromisoformat(phase["end_date"]))
                if phase_start <= phase_end:
                    phases.append({**phase, "start_date": phase_start.isoformat(), "end_date": phase_end.isoformat()})
            return phases

        for key in (
            "sun_phases", "active_dasha_transit_phases",
            "lower_dasha_phases", "key_concentration_phases",
        ):
            segment[key] = clipped_phases(key)
        segment["moon_peak_dates"] = [
            value for value in window.get("moon_peak_dates") or []
            if start <= date.fromisoformat(value) <= end
        ]
        return segment

    @staticmethod
    def _group_overlapping_windows(windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split the range whenever the set of active findings changes.

        A finding may therefore appear in several adjacent user-facing
        periods. This is intentional: assigning a long window only to its
        first overlap group made it disappear from later dates even though the
        underlying finding remained active.
        """
        if not windows:
            return []
        boundaries = {
            date.fromisoformat(window["start_date"])
            for window in windows
        } | {
            date.fromisoformat(window["end_date"]) + timedelta(days=1)
            for window in windows
        }
        for window in windows:
            for phase in window.get("key_concentration_phases") or []:
                boundaries.add(date.fromisoformat(phase["start_date"]))
                boundaries.add(date.fromisoformat(phase["end_date"]) + timedelta(days=1))
        ordered = sorted(boundaries)
        groups: List[Dict[str, Any]] = []
        for index in range(len(ordered) - 1):
            start = ordered[index]
            end = ordered[index + 1] - timedelta(days=1)
            active = [
                window for window in windows
                if date.fromisoformat(window["start_date"]) <= start
                and date.fromisoformat(window["end_date"]) >= end
            ]
            if not active:
                continue
            def concentration_priority(window: Dict[str, Any]) -> int:
                overlaps_segment = any(
                    date.fromisoformat(phase["start_date"]) <= end
                    and date.fromisoformat(phase["end_date"]) >= start
                    for phase in window.get("key_concentration_phases") or []
                )
                if not overlaps_segment:
                    return 0
                overlapping_bases = {
                    basis
                    for phase in window.get("key_concentration_phases") or []
                    if date.fromisoformat(phase["start_date"]) <= end
                    and date.fromisoformat(phase["end_date"]) >= start
                    for basis in phase.get("bases") or [phase.get("basis")]
                }
                return 2 if overlapping_bases & {
                    "anatomical_specificity_and_sun", "sun",
                } else 1

            active.sort(key=lambda row: (
                -concentration_priority(row),
                -row["activation_level"],
                -row.get("evidence_score", 0),
                row["finding_id"],
            ))
            segment_windows = [
                HealthTimingHeatmapEngine._window_for_segment(window, start, end)
                for window in active
            ]
            signature = tuple(row["finding_id"] for row in segment_windows)
            concentration_signature = tuple(
                (
                    row["finding_id"],
                    tuple(sorted({
                        basis
                        for phase in row.get("key_concentration_phases") or []
                        for basis in phase.get("bases") or [phase.get("basis")]
                        if basis
                    })),
                )
                for row in segment_windows
            )
            merge_signature = (signature, concentration_signature)
            if (
                groups
                and groups[-1]["merge_signature"] == merge_signature
                and date.fromisoformat(groups[-1]["end_date"]) + timedelta(days=1) == start
            ):
                merged_start = date.fromisoformat(groups[-1]["start_date"])
                groups[-1]["end_date"] = end.isoformat()
                groups[-1]["windows"] = [
                    HealthTimingHeatmapEngine._window_for_segment(window, merged_start, end)
                    for window in active
                ]
                groups[-1]["activation_level"] = max(
                    row["activation_level"] for row in groups[-1]["windows"]
                )
                continue
            groups.append({
                "group_id": f"{start.isoformat()}:{':'.join(signature)}",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "activation_level": max(row["activation_level"] for row in segment_windows),
                "windows": segment_windows,
                "finding_count": len(segment_windows),
                "merge_signature": merge_signature,
            })
        for group in groups:
            group.pop("merge_signature", None)
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
        houses = set(mechanism_houses) | set(carrier_houses) | HEALTH_MANIFESTATION_HOUSES
        return {
            "planets": planets,
            "houses": houses,
            "carrier_houses": carrier_houses,
            "mechanism_houses": mechanism_houses,
            "manifestation_houses": set(HEALTH_MANIFESTATION_HOUSES),
            "house_basis": house_basis,
        }

    def _same_natal_sign(self, first: str, second: str) -> bool:
        """Classical sign association used for dasha-result delivery."""
        first_row, second_row = _planet(self.chart, first), _planet(self.chart, second)
        try:
            return int(first_row.get("sign")) % 12 == int(second_row.get("sign")) % 12
        except (TypeError, ValueError):
            return bool(
                first_row.get("house")
                and first_row.get("house") == second_row.get("house")
            )

    def _finding_carrier_links(
        self,
        planet: str,
        signature: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return auditable natal links from a dasha lord to the finding.

        Direct house/lordship links remain in ``_dasha_chain``.  This helper
        covers two classical delivery paths that the earlier timing gate
        omitted: a dasha lord joined to a finding planet, and a node acting
        through its sign lord.  The node's nakshatra lord is exposed as a
        lower-period refinement link, but is not allowed to replace MD/AD/PD
        permission on its own.
        """
        finding_planets = set(signature["planets"])
        associated = sorted(
            target for target in finding_planets
            if target != planet and self._same_natal_sign(planet, target)
        )
        output: Dict[str, Any] = {
            "associated_finding_planets": associated,
            "dispositor": None,
            "dispositor_finding_planets": [],
            "nakshatra_lord": None,
            "nakshatra_lord_finding_planets": [],
        }
        if planet not in {"Rahu", "Ketu"}:
            return output

        try:
            sign = int(_planet(self.chart, planet).get("sign")) % 12
        except (TypeError, ValueError):
            sign = None
        dispositor = SIGN_LORDS.get(sign) if sign is not None else None
        output["dispositor"] = dispositor
        if dispositor:
            output["dispositor_finding_planets"] = sorted(
                target for target in finding_planets
                if dispositor == target or self._same_natal_sign(dispositor, target)
            )

        condition = self.conditions.get(planet) or {}
        nakshatra_lord = (condition.get("nakshatra_context") or {}).get("lord")
        output["nakshatra_lord"] = nakshatra_lord
        if nakshatra_lord:
            output["nakshatra_lord_finding_planets"] = sorted(
                target for target in finding_planets
                if nakshatra_lord == target or self._same_natal_sign(nakshatra_lord, target)
            )
        return output

    def _dasha_chain(
        self,
        dashas: Dict[str, Any],
        signature: Dict[str, Any],
        levels: tuple[str, ...] = LEVELS,
    ) -> List[Dict[str, Any]]:
        chain = []
        for level in levels:
            period = dashas.get(level) or {}
            planet = _period_planet(period)
            condition = self.conditions.get(planet) or {}
            functional = condition.get("functional_role") or {}
            ruled = {int(value) for value in (functional.get("ruled_houses") or [])}
            natal_house = condition.get("house")
            reasons = []
            carrier_links = self._finding_carrier_links(planet, signature)
            if planet in signature["planets"]:
                reasons.append("finding_planet")
            if carrier_links["associated_finding_planets"]:
                reasons.append("joined_finding_planet")
            if carrier_links["dispositor_finding_planets"]:
                reasons.append("node_dispositor_carries_finding")
            # Nakshatra delivery is a refinement only.  It explains why a
            # Sookshma/Prana lord concentrates an already-permitted period,
            # but cannot open the three-level window by itself.
            if level in REFINEMENT_LEVELS and carrier_links["nakshatra_lord_finding_planets"]:
                reasons.append("node_nakshatra_lord_carries_finding")
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
            manifestation_houses = set()
            if natal_house in signature["manifestation_houses"]:
                manifestation_houses.add(int(natal_house))
            manifestation_houses.update(ruled & signature["manifestation_houses"])
            primary_match = bool(reasons)
            manifestation_match = bool(manifestation_houses)
            modifiers = condition.get("finding_modifiers") or {}
            pressure = len(modifiers.get("pressure") or [])
            support = len(modifiers.get("support") or [])
            chain.append({
                "level": level,
                "planet": planet,
                "start": _date_string(period.get("start")) if isinstance(period, dict) else None,
                "end": _date_string(period.get("end")) if isinstance(period, dict) else None,
                "matched": primary_match or manifestation_match,
                "match_scope": (
                    "finding" if primary_match else "health_manifestation" if manifestation_match else "none"
                ),
                "reasons": reasons,
                "manifestation_houses": sorted(manifestation_houses),
                "direct_finding_planet": planet in signature["planets"],
                "natal_house": natal_house,
                "connected_houses": connected,
                "aspected_relevant_houses": sorted(aspected_houses),
                **carrier_links,
                "delivery": "mixed" if pressure and support else "pressure" if pressure else "support" if support else "neutral",
            })
        return chain

    def _transit_contacts(
        self,
        states: Dict[str, Dict[str, Any]],
        signature: Dict[str, Any],
        carrier_planets: set[str] | None = None,
    ) -> List[Dict[str, Any]]:
        contacts = []
        natal_targets = set(signature["planets"]) | set(carrier_planets or set())
        for transit_planet, state in states.items():
            transit_longitude = state.get("longitude")
            if transit_longitude is None:
                continue
            for natal_planet in sorted(natal_targets):
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
                    "contact_scope": (
                        "direct_finding_planet"
                        if natal_planet in signature["planets"] else "active_dasha_carrier"
                    ),
                })
        contacts.sort(key=lambda row: (row["orb"], -TRANSIT_WEIGHT[row["transit_planet"]]))
        return contacts

    def _transit_bridges(
        self,
        states: Dict[str, Dict[str, Any]],
        contacts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find a structural transit acting through a Sun/Moon natal trigger.

        Example: the Sun crosses natal Saturn while transiting Saturn aspects
        that Sun. The luminary supplies the exact trigger; the slow planet
        supplies the sustained structural pressure. This is kept distinct from
        a direct transit-to-natal contact so the evidence remains auditable.
        """
        bridges = []
        luminary_contacts = [row for row in contacts if row["transit_planet"] in {"Sun", "Moon"}]
        for trigger in luminary_contacts:
            luminary = trigger["transit_planet"]
            luminary_longitude = (states.get(luminary) or {}).get("longitude")
            if luminary_longitude is None:
                continue
            for planet in STRUCTURAL_PLANETS:
                longitude = (states.get(planet) or {}).get("longitude")
                if longitude is None:
                    continue
                best = None
                for angle in ASPECT_ANGLES[planet]:
                    separation = _angle_distance(
                        float(luminary_longitude),
                        (float(longitude) + angle) % 360.0,
                    )
                    if separation <= TRANSIT_BRIDGE_ORB[planet] and (best is None or separation < best[1]):
                        best = (angle, separation)
                if best is None:
                    continue
                bridges.append({
                    "structural_planet": planet,
                    "trigger_planet": luminary,
                    "natal_planet": trigger["natal_planet"],
                    "aspect_angle": best[0],
                    "aspect_number": int(best[0] / 30) + 1,
                    "orb": round(best[1], 3),
                    "trigger_orb": trigger["orb"],
                })
        bridges.sort(key=lambda row: (row["orb"], row["trigger_orb"], row["structural_planet"]))
        return bridges

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
        transit_bridges: List[Dict[str, Any]] | None = None,
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
            "structural_bridges": list(transit_bridges or [])[:4],
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
        refinement_chain = self._dasha_chain(dashas, signature, REFINEMENT_LEVELS)
        matched = [row for row in chain if row["matched"]]
        # A finding-specific MD/AD establishes the natal topic. PD may repeat
        # that finding directly or open a classical health-manifestation house
        # (H1/H8/H12). Sookshma and Prana remain excluded from permission.
        has_enclosing_permission = any(
            row["matched"] and row.get("match_scope") == "finding" for row in chain[:2]
        )
        has_pratyantardasha_permission = bool(chain[2]["matched"])
        # An authored organ/system susceptibility must be identified by one
        # of its own condition planets in MD/AD/PD. A broad house connection
        # (for example Saturn aspecting H4) can confirm timing, but must not by
        # itself turn every Moon/Mercury condition that mentions H4 into an
        # active illness. Anatomical findings use their explicit anatomical
        # carrier (normally the sixth lord) and are handled by the ordinary
        # finding-permission rule above.
        is_named_condition = finding.get("claim_type") == "named_classical_susceptibility"
        has_direct_condition_carrier = any(
            row.get("direct_finding_planet") for row in chain
        )
        if not (has_enclosing_permission and has_pratyantardasha_permission):
            return None
        if is_named_condition and not has_direct_condition_carrier:
            return None
        # Transits must be able to reach the active delivery chain, not only
        # the single planet that authored the natal anatomy finding.  Example:
        # an active Mercury joined to the sixth lord, or Rahu acting through a
        # dispositor joined to that lord, is a real carrier of the same natal
        # promise.  Broad health-house matches alone are deliberately excluded.
        carrier_planets = {
            row["planet"] for row in chain + refinement_chain
            if row.get("match_scope") == "finding"
        }
        contacts = self._transit_contacts(states, signature, carrier_planets)
        all_house_activations = self._transit_house_activations(states, signature)
        active_dasha_planets = {row["planet"] for row in chain if row["matched"]}
        active_refinement_planets = {
            row["planet"] for row in refinement_chain if row["matched"]
        }
        structural_contacts = [
            row for row in contacts
            if row["transit_planet"] in STRUCTURAL_PLANETS
            and (
                row["transit_planet"] in active_dasha_planets
                or row["natal_planet"] in active_dasha_planets
            )
        ]
        # Phaladeepika XX.34-38 treats the transit of the operating dasha or
        # bhukti lord as a distinct fructification factor.  Keep only a direct
        # contact with that same planet's natal position here.  A generic
        # transit through one of the finding's houses is confirmation, not a
        # bounded concentration.
        active_dasha_transit_contacts = [
            row for row in contacts
            if row.get("transit_planet") in active_dasha_planets
            and row.get("transit_planet") in {"Sun", "Mars", "Mercury", "Venus"}
            and (
                row.get("returns_to_own_natal_position")
                or row.get("natal_planet") in active_dasha_planets | active_refinement_planets
            )
        ]
        structural_mechanism_activations = [
            row for row in all_house_activations
            if row["transit_planet"] in STRUCTURAL_PLANETS
            and row["target_house"] in signature["mechanism_houses"]
        ]
        transit_bridges = self._transit_bridges(states, contacts)
        structural_confirmation_planets = {
            row["transit_planet"] for row in structural_contacts
        } | {
            row["transit_planet"] for row in structural_mechanism_activations
        } | {
            row["structural_planet"] for row in transit_bridges
        }
        # One exact structural contact is sufficient. Without it, require two
        # independent structural planets repeating the finding's mechanism;
        # a slow occupation of a generic health house alone is only context.
        if not structural_contacts and len(structural_confirmation_planets) < 2:
            return None
        luminary_contacts = [row for row in contacts if row["transit_planet"] in {"Sun", "Moon"}]
        dasha_score = sum(LEVEL_WEIGHT[row["level"]] for row in matched)
        retained_contacts = []
        retained_contact_keys = set()
        for row in luminary_contacts[:2] + active_dasha_transit_contacts[:2] + structural_contacts[:3]:
            key = (
                row.get("transit_planet"), row.get("natal_planet"),
                row.get("aspect_angle"), row.get("orb"),
            )
            if key not in retained_contact_keys:
                retained_contact_keys.add(key)
                retained_contacts.append(row)
        refinement_planets = {
            row["planet"] for row in refinement_chain if row.get("matched")
        }
        explanatory_planets = {
            row["transit_planet"] for row in retained_contacts
        } | structural_confirmation_planets | refinement_planets
        house_activations = [
            row for row in all_house_activations
            if row["transit_planet"] in explanatory_planets
        ]
        activation_summary = self._activation_summary(
            chain, house_activations, retained_contacts, signature, transit_bridges
        )
        activation_summary["active_dasha_transit_triggers"] = active_dasha_transit_contacts[:4]
        activation_summary["carrier_planets"] = sorted(carrier_planets)
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
        activation_summary["lower_dasha_refinement"] = [
            row for row in refinement_chain if row.get("matched")
        ]
        activation_summary["refinement_transit_activations"] = [
            row for row in house_activations
            if row["transit_planet"] in refinement_planets
            and row["target_house"] in signature["manifestation_houses"]
            and row["mode"] == "occupation"
        ]
        primary_medical_factors = set(finding.get("primary_medical_factors") or [])
        specificity_reasons = []
        for row in refinement_chain:
            if not row.get("matched"):
                continue
            repeats_sixth_sign = (
                row.get("natal_house") == 6
                and "sixth_house_sign" in primary_medical_factors
            )
            if repeats_sixth_sign:
                specificity_reasons.append(
                    f"{row['level']} {row['planet']} occupies natal House 6 and repeats the same sign-based body area"
                )
            elif row.get("direct_finding_planet"):
                specificity_reasons.append(
                    f"{row['level']} {row['planet']} directly carries this natal finding"
                )
        specificity_reasons = list(dict.fromkeys(specificity_reasons))
        activation_summary["specificity_reasons"] = specificity_reasons
        structural_planet_count = len(structural_confirmation_planets)
        luminary_planets = {
            row["transit_planet"] for row in luminary_contacts
        }
        transit_score = min(6, structural_planet_count * 2) + sum(
            TRANSIT_WEIGHT[planet] for planet in luminary_planets
        )
        active_dasha_transit_score = min(2, len(active_dasha_transit_contacts) * 2)
        transit_score += active_dasha_transit_score
        refinement_score = sum(1 for row in refinement_chain if row.get("matched"))
        specificity_score = min(3, len(specificity_reasons) * 2)
        score = dasha_score + transit_score + refinement_score + specificity_score
        has_sun_trigger = "Sun" in luminary_planets
        has_active_dasha_transit_trigger = bool(active_dasha_transit_contacts)
        if score >= 12 and has_sun_trigger:
            heat = 4
        elif score >= 10 and (has_sun_trigger or has_active_dasha_transit_trigger):
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
        has_mars_trigger = "Mars" in structural_confirmation_planets
        mars_carrier_activated_by_dasha = bool(
            "Mars" in signature["planets"]
            and any(
                row.get("direct_finding_planet")
                or "Mars" in (row.get("associated_finding_planets") or [])
                or "Mars" in (row.get("dispositor_finding_planets") or [])
                for row in chain if row.get("matched")
            )
        )
        has_intervention_house = any(
            (set(row.get("connected_houses") or []) | set(row.get("manifestation_houses") or [])) & {8, 12}
            for row in chain if row["matched"]
        )
        surgery_gate_passed = bool(
            is_surgery_finding and "Mars" in short_dasha and has_mars_trigger and has_intervention_house
        )
        intervention_gate_passed = bool(
            not is_surgery_finding
            and has_intervention_house
            and (
                (has_mars_trigger and len(structural_confirmation_planets) >= 2)
                or (
                    mars_carrier_activated_by_dasha
                    and bool(structural_confirmation_planets)
                    and has_active_dasha_transit_trigger
                )
            )
        )
        d30_chart = (
            (self.blueprint.get("divisional_health_confirmation") or {}).get("D30") or {}
        )
        finding_d30 = finding.get("d30_confirmation") or {}
        dasha_delivered_planets = {
            row.get("planet") for row in chain + refinement_chain if row.get("matched")
        }
        for row in chain + refinement_chain:
            if not row.get("matched"):
                continue
            dasha_delivered_planets.update(row.get("associated_finding_planets") or [])
            dasha_delivered_planets.update(row.get("dispositor_finding_planets") or [])
            dasha_delivered_planets.update(row.get("nakshatra_lord_finding_planets") or [])
        dasha_delivered_planets.discard(None)
        active_d30_anatomical_links = [
            row for row in (finding_d30.get("anatomical_links") or [])
            if row.get("planet") in dasha_delivered_planets
        ]
        active_d30_intervention_markers = [
            row for row in (d30_chart.get("intervention_markers") or [])
            if (
                (not row.get("planet") and not row.get("planets"))
                or row.get("planet") in dasha_delivered_planets
                or set(row.get("planets") or []) & dasha_delivered_planets
            )
        ]
        d30_intervention_confirmed = bool(
            active_d30_intervention_markers
            and (intervention_gate_passed or surgery_gate_passed)
        )
        d30_pressure_repeated = finding_d30.get("status") in {
            "pressure_repeated", "pressure_with_protection",
        }
        d30_anatomy_repeated = bool(active_d30_anatomical_links)
        d30_confirmation_score = min(
            2,
            int(d30_anatomy_repeated)
            + int(d30_pressure_repeated or d30_intervention_confirmed),
        )
        score += d30_confirmation_score
        if score >= 12 and has_sun_trigger:
            heat = 4
        elif score >= 10 and (has_sun_trigger or has_active_dasha_transit_trigger):
            heat = 3
        elif score >= 8:
            heat = 2
        else:
            heat = 1
        if finding_d30.get("protective_factors") and judgment == "sensitive_with_limited_support":
            judgment = "sensitive_with_recovery_support"
        def distinct_d30_factors(*collections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            output: List[Dict[str, Any]] = []
            seen: set[str] = set()
            for collection in collections:
                for factor in collection:
                    key = str(factor.get("meaning") or factor)
                    if key not in seen:
                        seen.add(key)
                        output.append(factor)
            return output

        active_d30 = {
            "available": bool(d30_chart.get("available")),
            "finding_status": finding_d30.get("status"),
            "anatomical_links": active_d30_anatomical_links,
            "anatomical_link_activated": d30_anatomy_repeated,
            "pressure_factors": distinct_d30_factors(
                list(finding_d30.get("pressure_factors") or []),
                list(d30_chart.get("pressure_factors") or []),
            ),
            "protective_factors": distinct_d30_factors(
                list(finding_d30.get("protective_factors") or []),
                list(d30_chart.get("protective_factors") or []),
            ),
            "intervention_confirmed": d30_intervention_confirmed,
            "intervention_markers": (
                active_d30_intervention_markers
                if d30_intervention_confirmed else []
            ),
            "role": "severity_and_manifestation_confirmation_only",
        }
        return {
            "finding_id": finding.get("stable_id"),
            "stable_id": finding.get("stable_id"),
            "label": finding.get("label"),
            "claim_type": finding.get("claim_type"),
            "system": finding.get("system"),
            "body_zones": list(finding.get("body_zones") or []),
            "natal_grade": finding.get("evidence_grade") or finding.get("support_grade"),
            "heat_level": heat,
            "phase": (
                "peak" if heat == 4 and has_sun_trigger else
                "heightened" if has_sun_trigger or has_active_dasha_transit_trigger else
                "active_window"
            ),
            "judgment": judgment,
            "manifestation_scope": (
                "surgery_attention" if surgery_gate_passed else
                "body_system_activation" if is_surgery_finding else
                "treatment_or_intervention_attention" if intervention_gate_passed else
                "finding_activation"
            ),
            "surgery_gate": {
                "required": is_surgery_finding,
                "passed": surgery_gate_passed,
                "short_dasha_mars": "Mars" in short_dasha,
                "mars_transit_contact": has_mars_trigger,
                "intervention_house_connection": has_intervention_house,
            },
            "intervention_gate": {
                "passed": intervention_gate_passed,
                "mars_transit_activation": has_mars_trigger,
                "mars_carrier_activated_by_dasha": mars_carrier_activated_by_dasha,
                "intervention_house_connection": has_intervention_house,
                "independent_structural_confirmations": len(structural_confirmation_planets),
            },
            "evidence_score": score,
            "score_components": {
                "dasha": dasha_score,
                "transit": transit_score,
                "active_dasha_lord_transit": active_dasha_transit_score,
                "lower_dasha_refinement": refinement_score,
                "anatomical_specificity": specificity_score,
                "d30_confirmation": d30_confirmation_score,
            },
            "condition_timing_gate": {
                "requires_direct_md_ad_pd_carrier": is_named_condition,
                "direct_md_ad_pd_carrier_present": has_direct_condition_carrier,
            },
            "dasha_chain": chain,
            "refinement_dasha_chain": refinement_chain,
            "transit_contacts": retained_contacts,
            "transit_house_activations": house_activations[:10],
            "activation_summary": activation_summary,
            "d30_confirmation": active_d30,
            "natal_reasons": list(finding.get("supporting_rules") or [])[:5],
            "protective_factors": list(finding.get("protective_rules") or [])[:5],
            "pressure_factors": list(finding.get("contradicting_rules") or [])[:5],
            "interpretation_rule": "This is a sensitivity marker, not a diagnosis or calibrated probability.",
        }
