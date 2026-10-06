"""Canonical chart-to-fact adapter for reviewed Deva Keralam rules.

The adapter is opt in and returns a ``ClassicalFactSet``.  It never adds fields
to the chart payload used by existing chart, mobile, web or chat clients.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from math import isfinite
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from calculators.planetary_dignities_calculator import (
    PlanetaryDignitiesCalculator,
    SIGN_LORDS,
    SIGN_NAMES,
)
from calculators.vedic_graha_drishti import get_aspect_houses_for_planet
from classical_rules.facts import ClassicalFact, ClassicalFactSet

from .nadiamsa import DEFAULT_TABLE_PATH, build_deva_keralam_fact_set
from .ontology import DASHA_LEVELS, PLANETS, is_canonical_fact_key
from .age_timing import AgeTimingInputError, calculate_age_timing_window
from .period_timing import PeriodTimingInputError, normalize_source_period_chain
from .period_phase import calculate_period_phase_facts


ADAPTER_VERSION = "deva-keralam-chart-facts/1.2.0"
_CALCULATOR = "classical_rules.deva_keralam.chart_facts.compile_deva_keralam_chart_facts"
_STRUCTURAL_SOURCE = "Classical whole-sign chart geometry; calculated from the supplied sidereal D1 longitudes"
_ASPECT_SOURCE = (
    "Parashari graha drishti; existing canonical vedic_graha_drishti calculator, "
    "with the product's conservative seventh-only node policy"
)
_DIGNITY_SOURCE = "Existing canonical planetary_dignities_calculator"


class ChartFactInputError(ValueError):
    """Input data is contradictory or insufficient for deterministic facts."""


def _longitude(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ChartFactInputError(f"{label} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ChartFactInputError(f"{label} must be numeric") from exc
    if not isfinite(number):
        raise ChartFactInputError(f"{label} must be finite")
    return number % 360.0


def _fact(key: str, value: Any, *, family: str, source: str, evidence: Optional[Mapping[str, Any]] = None) -> ClassicalFact:
    if not is_canonical_fact_key(key):
        raise AssertionError(f"Adapter attempted to emit an unknown canonical key: {key}")
    return ClassicalFact(
        key=key,
        value=value,
        source_rules=(f"DEVA_KERALAM.FACT_ONTOLOGY.{family.upper()}",),
        source_references=(source,),
        calculator_bindings=(_CALCULATOR,),
        evidence={"adapter_version": ADAPTER_VERSION, **dict(evidence or {})},
    )


def _add(facts: ClassicalFactSet, key: str, value: Any, *, family: str, source: str, evidence: Optional[Mapping[str, Any]] = None) -> None:
    facts.add(_fact(key, value, family=family, source=source, evidence=evidence))


def _navamsa(longitude: float) -> int:
    return int(PlanetaryDignitiesCalculator._navamsa_sign(longitude))


def _house(sign: int, ascendant_sign: int) -> int:
    return ((sign - ascendant_sign) % 12) + 1


def _modality(sign: int) -> str:
    remainder = int(sign) % 3
    return ("movable", "fixed", "dual")[remainder]


def _parity(sign: int) -> str:
    return "odd" if int(sign) % 2 == 0 else "even"


def _relative_house(subject_sign: int, anchor_sign: int) -> int:
    return ((int(subject_sign) - int(anchor_sign)) % 12) + 1


def _conjunction_pair(first: str, second: str) -> tuple[str, str]:
    order = {planet: index for index, planet in enumerate(PLANETS)}
    return (first, second) if order[first] < order[second] else (second, first)


def _aspect_hit(source: str, source_sign: int, target_sign: int) -> int | None:
    for number in _aspect_numbers(source):
        if (int(source_sign) + number - 1) % 12 == int(target_sign):
            return number
    return None


def _lordships(planet: str, ascendant_sign: int) -> list[int]:
    return [house for house in range(1, 13) if SIGN_LORDS[(ascendant_sign + house - 1) % 12] == planet]


def _aspect_numbers(planet: str) -> list[int]:
    numbers = [number for number in get_aspect_houses_for_planet(planet) if number != 1]
    # Rahu/Ketu fifth and ninth aspects are disputed.  The canonical Positions
    # implementation already applies the user's selected conservative policy.
    return [7] if planet in {"Rahu", "Ketu"} else numbers


def _iso_date(value: Any, label: str) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except (TypeError, ValueError) as exc:
        raise ChartFactInputError(f"{label} must be an ISO date") from exc


def _planet_rows(chart: Mapping[str, Any], ascendant_sign: int) -> Dict[str, Dict[str, Any]]:
    supplied = chart.get("planets") or {}
    if not isinstance(supplied, Mapping):
        raise ChartFactInputError("chart.planets must be a mapping")
    rows: Dict[str, Dict[str, Any]] = {}
    for planet in PLANETS:
        raw = supplied.get(planet)
        if raw is None:
            continue
        if not isinstance(raw, Mapping) or raw.get("longitude") is None:
            raise ChartFactInputError(f"chart.planets.{planet}.longitude is required when the planet is supplied")
        longitude = _longitude(raw["longitude"], f"chart.planets.{planet}.longitude")
        sign = int(longitude // 30)
        house = _house(sign, ascendant_sign)
        if raw.get("sign") is not None and int(raw["sign"]) != sign:
            raise ChartFactInputError(f"chart.planets.{planet}.sign contradicts its longitude")
        if raw.get("house") is not None and int(raw["house"]) != house:
            raise ChartFactInputError(f"chart.planets.{planet}.house contradicts its longitude and Ascendant")
        rows[planet] = {
            **dict(raw), "longitude": longitude, "sign": sign,
            "degree": longitude % 30.0, "house": house,
        }
    return rows


def _merge_nadi_facts(
    facts: ClassicalFactSet,
    chart: Mapping[str, Any],
    *,
    uncertainty: Any | None,
    table_path: str | Path,
) -> None:
    nadi = build_deva_keralam_fact_set(
        chart,
        ascendant_longitude_uncertainty_arcseconds=uncertainty,
        table_path=table_path,
    ).as_dict()["facts"]
    for old_key, payload in nadi.items():
        key = old_key
        if old_key.startswith("deva_keralam.") and not old_key.startswith("deva_keralam.ascendant."):
            key = "deva_keralam.planet." + old_key[len("deva_keralam."):]
        if not is_canonical_fact_key(key):
            continue
        facts.add(ClassicalFact(
            key=key,
            value=payload["value"],
            source_rules=tuple(payload["source_rules"]),
            source_references=tuple(payload["source_references"]),
            calculator_bindings=tuple(payload["calculator_bindings"]),
            evidence=dict(payload.get("evidence") or {}),
        ))


def _project_house_lord_facts(
    facts: ClassicalFactSet,
    *,
    ascendant_sign: int,
    planets: Mapping[str, Mapping[str, Any]],
) -> None:
    """Project one stable fact grammar for each of the twelve house lords.

    Identity is always known from the Ascendant. Placement facts remain absent
    when the caller supplied a partial chart without that lord, preserving the
    fact engine's fail-closed behavior.
    """
    nadi_suffixes = (
        "ordinal", "name", "half", "physical_division", "sign_index", "sign_name",
        "sign_modality", "distance_to_division_boundary_arcseconds",
        "distance_to_half_boundary_arcseconds", "precision_status",
        "birth_time_precision_warning",
    )
    for house in range(1, 13):
        sign = (ascendant_sign + house - 1) % 12
        lord = SIGN_LORDS[sign]
        prefix = f"deva_keralam.house.{house}.lord"
        _add(facts, f"{prefix}.name", lord, family="house_lord", source=_STRUCTURAL_SOURCE)
        if lord not in planets:
            continue
        row = planets[lord]
        longitude, rashi = float(row["longitude"]), int(row["sign"])
        navamsa = _navamsa(longitude)
        for suffix, value in {
            "longitude": longitude,
            "degree_in_sign": longitude % 30.0,
            "house": int(row["house"]),
            "vargottama": rashi == navamsa,
            "rashi.index": rashi,
            "rashi.name": SIGN_NAMES[rashi],
            "rashi.lord": SIGN_LORDS[rashi],
            "rashi.modality": _modality(rashi),
            "navamsa.index": navamsa,
            "navamsa.name": SIGN_NAMES[navamsa],
            "navamsa.lord": SIGN_LORDS[navamsa],
            "navamsa.modality": _modality(navamsa),
            "navamsa.parity": _parity(navamsa),
        }.items():
            _add(facts, f"{prefix}.{suffix}", value, family="house_lord", source=_STRUCTURAL_SOURCE)
        planet_nadi_prefix = f"deva_keralam.planet.{lord}.nadiamsa"
        for suffix in nadi_suffixes:
            source_fact = facts.get(f"{planet_nadi_prefix}.{suffix}")
            if source_fact is None:
                continue
            facts.add(ClassicalFact(
                key=f"{prefix}.nadiamsa.{suffix}",
                value=source_fact.value,
                source_rules=source_fact.source_rules,
                source_references=source_fact.source_references,
                calculator_bindings=source_fact.calculator_bindings,
                evidence={**source_fact.evidence, "projected_house": house, "projected_lord": lord},
            ))
        for target in PLANETS:
            if target not in planets or target == lord:
                continue
            lord_sign, target_sign = int(row["sign"]), int(planets[target]["sign"])
            conjunction = lord_sign == target_sign
            aspect_to = _aspect_hit(lord, lord_sign, target_sign)
            aspected_by = _aspect_hit(target, target_sign, lord_sign)
            relation_values = {
                f"relationship.conjunction.{target}.present": conjunction,
                f"relationship.conjunction.{target}.numbers": [1] if conjunction else [],
                f"relationship.aspect_to.{target}.present": aspect_to is not None,
                f"relationship.aspect_to.{target}.numbers": [] if aspect_to is None else [aspect_to],
                f"relationship.aspected_by.{target}.present": aspected_by is not None,
                f"relationship.aspected_by.{target}.numbers": [] if aspected_by is None else [aspected_by],
                f"relative_to.{target}.house": _relative_house(lord_sign, target_sign),
            }
            for suffix, value in relation_values.items():
                source = _ASPECT_SOURCE if "aspect" in suffix else _STRUCTURAL_SOURCE
                _add(facts, f"{prefix}.{suffix}", value, family="house_lord_relation", source=source)


def _project_dispositor_facts(
    facts: ClassicalFactSet,
    *,
    planets: Mapping[str, Mapping[str, Any]],
) -> None:
    nadi_suffixes = (
        "ordinal", "name", "half", "physical_division", "sign_index", "sign_name",
        "sign_modality", "distance_to_division_boundary_arcseconds",
        "distance_to_half_boundary_arcseconds", "precision_status",
        "birth_time_precision_warning",
    )
    for subject, subject_row in planets.items():
        dispositor = SIGN_LORDS[int(subject_row["sign"])]
        prefix = f"deva_keralam.planet.{subject}.dispositor"
        _add(facts, f"{prefix}.name", dispositor, family="dispositor", source=_STRUCTURAL_SOURCE)
        if dispositor not in planets:
            continue
        row = planets[dispositor]
        longitude, rashi = float(row["longitude"]), int(row["sign"])
        navamsa = _navamsa(longitude)
        for suffix, value in {
            "longitude": longitude, "degree_in_sign": longitude % 30.0,
            "house": int(row["house"]), "vargottama": rashi == navamsa,
            "rashi.index": rashi, "rashi.name": SIGN_NAMES[rashi],
            "rashi.lord": SIGN_LORDS[rashi], "rashi.modality": _modality(rashi),
            "navamsa.index": navamsa, "navamsa.name": SIGN_NAMES[navamsa],
            "navamsa.lord": SIGN_LORDS[navamsa], "navamsa.modality": _modality(navamsa),
            "navamsa.parity": _parity(navamsa),
        }.items():
            _add(facts, f"{prefix}.{suffix}", value, family="dispositor", source=_STRUCTURAL_SOURCE)
        for suffix in nadi_suffixes:
            source_fact = facts.get(f"deva_keralam.planet.{dispositor}.nadiamsa.{suffix}")
            if source_fact is None:
                continue
            facts.add(ClassicalFact(
                key=f"{prefix}.nadiamsa.{suffix}", value=source_fact.value,
                source_rules=source_fact.source_rules, source_references=source_fact.source_references,
                calculator_bindings=source_fact.calculator_bindings,
                evidence={**source_fact.evidence, "subject": subject, "dispositor": dispositor},
            ))
        for target, target_row in planets.items():
            if target == dispositor:
                continue
            target_sign = int(target_row["sign"])
            conjunction = rashi == target_sign
            aspect_to = _aspect_hit(dispositor, rashi, target_sign)
            aspected_by = _aspect_hit(target, target_sign, rashi)
            for suffix, value in {
                f"relationship.conjunction.{target}.present": conjunction,
                f"relationship.conjunction.{target}.numbers": [1] if conjunction else [],
                f"relationship.aspect_to.{target}.present": aspect_to is not None,
                f"relationship.aspect_to.{target}.numbers": [] if aspect_to is None else [aspect_to],
                f"relationship.aspected_by.{target}.present": aspected_by is not None,
                f"relationship.aspected_by.{target}.numbers": [] if aspected_by is None else [aspected_by],
            }.items():
                source = _ASPECT_SOURCE if "aspect" in suffix else _STRUCTURAL_SOURCE
                _add(facts, f"{prefix}.{suffix}", value, family="dispositor_relation", source=source)


def _add_timing_facts(
    facts: ClassicalFactSet,
    timing: Mapping[str, Any],
    *,
    ascendant_sign: int,
    natal_planets: Mapping[str, Mapping[str, Any]],
) -> None:
    raw_source_periods = timing.get("source_periods")
    if raw_source_periods is not None:
        try:
            source_periods = normalize_source_period_chain(raw_source_periods, as_of=timing.get("as_of"))
        except PeriodTimingInputError as exc:
            raise ChartFactInputError(str(exc)) from exc
        for period, raw_period in zip(source_periods, raw_source_periods):
            prefix = f"deva_keralam.timing.period.{period.slot}"
            try:
                phase_values = calculate_period_phase_facts(
                    period, as_of=timing.get("as_of"), phase_window=raw_period.get("phase_window"),
                )
            except PeriodTimingInputError as exc:
                raise ChartFactInputError(str(exc)) from exc
            for suffix, value in {**period.fact_values(), **phase_values}.items():
                if value is None:
                    continue
                _add(
                    facts,
                    f"{prefix}.{suffix}",
                    value,
                    family="period",
                    source="Caller-supplied source-neutral period chain validated against timing.as_of",
                    evidence={
                        "period_timing_version": "deva-keralam-source-periods/1.0.0",
                        "interval_semantics": "half_open",
                        "nesting_order": period.slot,
                        "no_default_dasha_system": True,
                    },
                )

    raw_chain = timing.get("dasha") or timing.get("dashas") or {}
    if isinstance(raw_chain, list):
        raw_chain = {str(row.get("level") or ""): row for row in raw_chain if isinstance(row, Mapping)}
    if raw_chain and not isinstance(raw_chain, Mapping):
        raise ChartFactInputError("timing.dasha must be a mapping or list")
    level_aliases = {"MD": "mahadasha", "AD": "antardasha", "PD": "pratyantardasha", "SD": "sookshma", "Pr": "prana"}
    for supplied_level, row in (raw_chain or {}).items():
        level = level_aliases.get(str(supplied_level), str(supplied_level).lower())
        if level not in DASHA_LEVELS or not isinstance(row, Mapping):
            raise ChartFactInputError(f"Unknown dasha level: {supplied_level!r}")
        lord = str(row.get("lord") or "")
        if lord not in PLANETS:
            raise ChartFactInputError(f"Dasha {level} requires a canonical planet lord")
        prefix = f"deva_keralam.timing.dasha.{level}"
        _add(facts, f"{prefix}.lord", lord, family="dasha", source="Caller-supplied canonical Vimshottari period")
        for field in ("ordinal", "start", "end", "active"):
            if row.get(field) is None:
                continue
            value = row[field]
            if field == "ordinal":
                value = int(value)
            elif field in {"start", "end"}:
                value = _iso_date(value, f"dasha.{level}.{field}")
            elif field == "active":
                value = bool(value)
            _add(facts, f"{prefix}.{field}", value, family="dasha", source="Caller-supplied canonical Vimshottari period")

    transits = timing.get("transits") or {}
    if transits and not isinstance(transits, Mapping):
        raise ChartFactInputError("timing.transits must be a mapping")
    default_as_of = timing.get("as_of")
    for planet, raw in transits.items():
        if planet not in PLANETS or not isinstance(raw, Mapping):
            raise ChartFactInputError(f"Unknown transit planet: {planet!r}")
        longitude = _longitude(raw.get("longitude"), f"timing.transits.{planet}.longitude")
        sign = int(longitude // 30)
        house = _house(sign, ascendant_sign)
        aspect_numbers = _aspect_numbers(planet)
        aspected_signs = {(sign + number - 1) % 12 for number in aspect_numbers}
        aspected_houses = sorted({_house(target, ascendant_sign) for target in aspected_signs})
        conjunct = sorted(name for name, row in natal_planets.items() if int(row["sign"]) == sign)
        aspects = sorted(name for name, row in natal_planets.items() if int(row["sign"]) in aspected_signs)
        prefix = f"deva_keralam.timing.transit.{planet}"
        values = {
            "longitude": longitude, "house": house, "rashi_index": sign,
            "rashi_name": SIGN_NAMES[sign], "aspected_houses": aspected_houses,
            "conjunct_natal_planets": conjunct, "aspects_natal_planets": aspects,
        }
        as_of = raw.get("as_of", default_as_of)
        if as_of is not None:
            values["as_of"] = _iso_date(as_of, f"timing.transits.{planet}.as_of")
        for suffix, value in values.items():
            _add(facts, f"{prefix}.{suffix}", value, family="transit", source=_ASPECT_SOURCE)

    birth_date = timing.get("birth_date")
    as_of = timing.get("as_of")
    if birth_date is not None and as_of is not None:
        try:
            window = calculate_age_timing_window(birth_date, as_of)
        except AgeTimingInputError as exc:
            raise ChartFactInputError(str(exc)) from exc
        age_years = (window.as_of - window.birth_date).days / 365.2425
        values = {**window.fact_values(), "age_years": round(age_years, 8)}
        for suffix, value in values.items():
            _add(
                facts,
                f"deva_keralam.timing.native.{suffix}",
                value,
                family="age",
                source="Civil calendar age derived only from supplied birth_date and as_of",
                evidence={
                    "interval_semantics": "half_open",
                    "feb_29_anniversary_policy": "february_28_in_non_leap_years",
                },
            )


def compile_deva_keralam_chart_facts(
    chart: Mapping[str, Any],
    *,
    ascendant_longitude_uncertainty_arcseconds: Any | None = None,
    timing_context: Optional[Mapping[str, Any]] = None,
    table_path: str | Path = DEFAULT_TABLE_PATH,
) -> ClassicalFactSet:
    """Build deterministic natal and optional timing facts from an existing D1 chart."""
    if not isinstance(chart, Mapping) or chart.get("ascendant") is None:
        raise ChartFactInputError("A mapping with numeric chart.ascendant is required")
    ascendant = _longitude(chart["ascendant"], "chart.ascendant")
    ascendant_sign = int(ascendant // 30)
    planets = _planet_rows(chart, ascendant_sign)
    normalized_chart = deepcopy(dict(chart))
    normalized_chart["ascendant"] = ascendant
    normalized_chart["planets"] = deepcopy(planets)
    facts = ClassicalFactSet()

    _add(facts, "deva_keralam.ascendant.longitude", ascendant, family="ascendant", source=_STRUCTURAL_SOURCE)
    _add(facts, "deva_keralam.ascendant.degree_in_sign", ascendant % 30.0, family="ascendant", source=_STRUCTURAL_SOURCE)
    for suffix, value in {
        "index": ascendant_sign, "name": SIGN_NAMES[ascendant_sign], "lord": SIGN_LORDS[ascendant_sign],
        "modality": _modality(ascendant_sign),
    }.items():
        _add(facts, f"deva_keralam.ascendant.rashi.{suffix}", value, family="ascendant", source=_STRUCTURAL_SOURCE)
    _add(facts, "deva_keralam.ascendant.house", 1, family="ascendant", source=_STRUCTURAL_SOURCE)
    asc_navamsa = _navamsa(ascendant)
    for suffix, value in {
        "index": asc_navamsa, "name": SIGN_NAMES[asc_navamsa], "lord": SIGN_LORDS[asc_navamsa],
        "modality": _modality(asc_navamsa), "parity": _parity(asc_navamsa),
    }.items():
        _add(facts, f"deva_keralam.ascendant.navamsa.{suffix}", value, family="ascendant", source=_STRUCTURAL_SOURCE)

    for house in range(1, 13):
        sign = (ascendant_sign + house - 1) % 12
        lord = SIGN_LORDS[sign]
        occupants = [planet for planet in PLANETS if planet in planets and int(planets[planet]["house"]) == house]
        for suffix, value in {
            "rashi.index": sign, "rashi.name": SIGN_NAMES[sign],
            "rashi.modality": _modality(sign), "lord": lord, "occupants": occupants,
        }.items():
            _add(facts, f"deva_keralam.house.{house}.{suffix}", value, family="house", source=_STRUCTURAL_SOURCE)
        if lord in planets:
            _add(facts, f"deva_keralam.house.{house}.lord_house", planets[lord]["house"], family="house", source=_STRUCTURAL_SOURCE)

    for planet, row in planets.items():
        prefix = f"deva_keralam.planet.{planet}"
        sign, longitude = int(row["sign"]), float(row["longitude"])
        for suffix, value in {
            "longitude": longitude, "degree_in_sign": longitude % 30.0, "house": int(row["house"]),
        }.items():
            _add(facts, f"{prefix}.{suffix}", value, family="planet", source=_STRUCTURAL_SOURCE)
        for suffix, value in {
            "index": sign, "name": SIGN_NAMES[sign], "lord": SIGN_LORDS[sign], "modality": _modality(sign),
        }.items():
            _add(facts, f"{prefix}.rashi.{suffix}", value, family="planet", source=_STRUCTURAL_SOURCE)
        _add(facts, f"{prefix}.lordships", _lordships(planet, ascendant_sign), family="planet", source=_STRUCTURAL_SOURCE)
        navamsa = _navamsa(longitude)
        for suffix, value in {
            "index": navamsa, "name": SIGN_NAMES[navamsa], "lord": SIGN_LORDS[navamsa],
            "modality": _modality(navamsa), "parity": _parity(navamsa),
        }.items():
            _add(facts, f"{prefix}.navamsa.{suffix}", value, family="planet", source=_STRUCTURAL_SOURCE)
        _add(facts, f"{prefix}.vargottama", sign == navamsa, family="planet", source=_STRUCTURAL_SOURCE)

    _merge_nadi_facts(
        facts, normalized_chart,
        uncertainty=ascendant_longitude_uncertainty_arcseconds,
        table_path=table_path,
    )
    precision = facts.require("deva_keralam.ascendant.nadiamsa.precision_status").value
    warning = facts.require("deva_keralam.ascendant.nadiamsa.birth_time_precision_warning").value
    for suffix, value in {
        "status": precision,
        "longitude_uncertainty_arcseconds": (
            None if ascendant_longitude_uncertainty_arcseconds is None
            else float(ascendant_longitude_uncertainty_arcseconds)
        ),
        "reliable": not bool(warning),
    }.items():
        _add(facts, f"deva_keralam.precision.ascendant.{suffix}", value, family="precision", source="Deva Keralam 150-Nadi boundary precision policy")

    ordered_planets = [planet for planet in PLANETS if planet in planets]
    conjunctions_by_planet = {planet: [] for planet in ordered_planets}
    for index, first in enumerate(ordered_planets):
        for second in ordered_planets[index + 1:]:
            present = planets[first]["sign"] == planets[second]["sign"]
            canonical_first, canonical_second = _conjunction_pair(first, second)
            _add(facts, f"deva_keralam.relationship.conjunction.{canonical_first}.{canonical_second}.present", present, family="conjunction", source=_STRUCTURAL_SOURCE)
            if present:
                conjunctions_by_planet[first].append(second)
                conjunctions_by_planet[second].append(first)
    aspects_by_planet = {planet: [] for planet in ordered_planets}
    aspected_by_planet = {planet: [] for planet in ordered_planets}
    for source_planet in ordered_planets:
        source_sign = int(planets[source_planet]["sign"])
        numbers = _aspect_numbers(source_planet)
        target_signs = {(source_sign + number - 1) % 12: number for number in numbers}
        aspected_houses = sorted({_house(sign, ascendant_sign) for sign in target_signs})
        _add(facts, f"deva_keralam.planet.{source_planet}.aspected_houses", aspected_houses, family="aspect", source=_ASPECT_SOURCE)
        for house in range(1, 13):
            hit = next((number for sign, number in target_signs.items() if _house(sign, ascendant_sign) == house), None)
            prefix = f"deva_keralam.relationship.aspect.{source_planet}.house.{house}"
            _add(facts, f"{prefix}.present", hit is not None, family="aspect", source=_ASPECT_SOURCE)
            _add(facts, f"{prefix}.numbers", [] if hit is None else [hit], family="aspect", source=_ASPECT_SOURCE)
        for target_planet in ordered_planets:
            if source_planet == target_planet:
                continue
            hit = target_signs.get(int(planets[target_planet]["sign"]))
            prefix = f"deva_keralam.relationship.aspect.{source_planet}.{target_planet}"
            _add(facts, f"{prefix}.present", hit is not None, family="aspect", source=_ASPECT_SOURCE)
            _add(facts, f"{prefix}.numbers", [] if hit is None else [hit], family="aspect", source=_ASPECT_SOURCE)
            _add(facts, f"deva_keralam.relationship.relative_house.{source_planet}.{target_planet}", _relative_house(source_sign, int(planets[target_planet]["sign"])), family="relative_house", source=_STRUCTURAL_SOURCE)
            _add(facts, f"deva_keralam.planet.{source_planet}.relative_to.{target_planet}.house", _relative_house(source_sign, int(planets[target_planet]["sign"])), family="relative_house", source=_STRUCTURAL_SOURCE)
            if hit is not None:
                aspects_by_planet[source_planet].append(target_planet)
                aspected_by_planet[target_planet].append(source_planet)

    for planet in ordered_planets:
        for suffix, value in {
            "conjunct_planets": sorted(conjunctions_by_planet[planet], key=PLANETS.index),
            "aspects_planets": sorted(aspects_by_planet[planet], key=PLANETS.index),
            "aspected_by_planets": sorted(aspected_by_planet[planet], key=PLANETS.index),
        }.items():
            _add(facts, f"deva_keralam.planet.{planet}.{suffix}", value, family="planet_relation", source=_ASPECT_SOURCE if "aspect" in suffix else _STRUCTURAL_SOURCE)
    for house in range(1, 13):
        aspectors = [
            planet for planet in ordered_planets
            if facts.require(f"deva_keralam.relationship.aspect.{planet}.house.{house}.present").value
        ]
        _add(facts, f"deva_keralam.house.{house}.aspected_by_planets", aspectors, family="aspect", source=_ASPECT_SOURCE)

    _project_house_lord_facts(facts, ascendant_sign=ascendant_sign, planets=planets)
    _project_dispositor_facts(facts, planets=planets)

    dignities = PlanetaryDignitiesCalculator(normalized_chart).calculate_planetary_dignities()
    for planet in ordered_planets:
        row = dignities.get(planet)
        if isinstance(row, Mapping) and row.get("dignity") is not None:
            _add(facts, f"deva_keralam.planet.{planet}.dignity", row["dignity"], family="dignity", source=_DIGNITY_SOURCE)

    if timing_context:
        if not isinstance(timing_context, Mapping):
            raise ChartFactInputError("timing_context must be a mapping")
        _add_timing_facts(facts, timing_context, ascendant_sign=ascendant_sign, natal_planets=planets)
    return facts
