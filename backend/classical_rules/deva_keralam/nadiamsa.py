"""Source-versioned Deva Keralam Nadiamsa calculation.

Table 1 of the pinned Book I edition gives 150 Nadiamsas and the order in
movable, fixed and dual signs.  A sign is divided into 150 spans of 12 arc
minutes; each span has a former and latter half of 6 arc minutes.

No spelling or ordering fallback is permitted.  A table must contain exactly
one non-empty source name for every ordinal from 1 through 150 before it can
be used.  That keeps OCR gaps from becoming chart facts.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from classical_rules.facts import ClassicalFact, ClassicalFactSet


DIVISIONS_PER_SIGN = 150
SIGN_DEGREES = Decimal("30")
DIVISION_DEGREES = Decimal("0.2")
HALF_DEGREES = Decimal("0.1")
ARCSECONDS_PER_DEGREE = Decimal("3600")

SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
MOVABLE_SIGNS = frozenset({0, 3, 6, 9})
FIXED_SIGNS = frozenset({1, 4, 7, 10})
DUAL_SIGNS = frozenset({2, 5, 8, 11})

DEFAULT_TABLE_PATH = Path(__file__).with_name("data") / "santhanam_book_1_table_1_v1.json"


class DevaKeralamTableError(ValueError):
    """The edition table is absent, incomplete or structurally unsafe."""


@dataclass(frozen=True)
class NadiamsaTable:
    table_key: str
    schema_version: str
    edition: str
    source_reference: str
    names_by_ordinal: Mapping[int, str]


@dataclass(frozen=True)
class NadiamsaPosition:
    calculator_version: str
    table_key: str
    source_reference: str
    subject: str
    sidereal_longitude: float
    sign_index: int
    sign_name: str
    sign_modality: str
    degree_in_sign: float
    physical_division: int
    ordinal: int
    name: str
    half: str
    start_degree_in_sign: float
    midpoint_degree_in_sign: float
    end_degree_in_sign: float
    distance_to_division_boundary_arcseconds: float
    distance_to_half_boundary_arcseconds: float
    on_division_boundary: bool
    on_half_boundary: bool
    longitude_uncertainty_arcseconds: Optional[float]
    precision_status: str
    birth_time_precision_warning: bool
    precision_reason: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not result.is_finite():
        raise ValueError(f"{label} must be finite")
    return result


@lru_cache(maxsize=8)
def load_nadiamsa_table(path: str | Path = DEFAULT_TABLE_PATH) -> NadiamsaTable:
    """Load and strictly validate one edition's full 150-name table."""
    table_path = Path(path)
    try:
        payload = json.loads(table_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DevaKeralamTableError(f"Cannot load Nadiamsa table: {table_path}") from exc

    rows = payload.get("names")
    if not isinstance(rows, list):
        raise DevaKeralamTableError("Nadiamsa table names must be a list")
    names: Dict[int, str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise DevaKeralamTableError("Every Nadiamsa row must be an object")
        try:
            ordinal = int(row.get("ordinal"))
        except (TypeError, ValueError) as exc:
            raise DevaKeralamTableError("Every Nadiamsa row needs an integer ordinal") from exc
        name = str(row.get("source_name") or "").strip()
        if ordinal in names:
            raise DevaKeralamTableError(f"Duplicate Nadiamsa ordinal: {ordinal}")
        if not name:
            raise DevaKeralamTableError(f"Missing source name for Nadiamsa ordinal: {ordinal}")
        names[ordinal] = name

    expected = set(range(1, DIVISIONS_PER_SIGN + 1))
    if set(names) != expected:
        missing = sorted(expected - set(names))
        unexpected = sorted(set(names) - expected)
        raise DevaKeralamTableError(
            f"Nadiamsa table must contain ordinals 1..150; missing={missing}, unexpected={unexpected}"
        )
    ordering = payload.get("ordering") or {}
    if ordering != {
        "movable": "1_to_150",
        "fixed": "150_to_1",
        "dual": "76_to_150_then_1_to_75",
    }:
        raise DevaKeralamTableError("Nadiamsa ordering metadata does not match Table 1")

    source = payload.get("source") or {}
    source_reference = str(source.get("reference") or "").strip()
    if not source_reference:
        raise DevaKeralamTableError("Nadiamsa table requires a source reference")
    return NadiamsaTable(
        table_key=str(payload.get("table_key") or "").strip(),
        schema_version=str(payload.get("schema_version") or "").strip(),
        edition=str(payload.get("edition") or "").strip(),
        source_reference=source_reference,
        names_by_ordinal=names,
    )


def _modality(sign_index: int) -> str:
    if sign_index in MOVABLE_SIGNS:
        return "movable"
    if sign_index in FIXED_SIGNS:
        return "fixed"
    if sign_index in DUAL_SIGNS:
        return "dual"
    raise ValueError(f"Invalid sign index: {sign_index}")


def _ordinal(physical_division: int, modality: str) -> int:
    if modality == "movable":
        return physical_division
    if modality == "fixed":
        return 151 - physical_division
    # First physical division is ordinal 76; division 76 wraps to ordinal 1.
    return ((physical_division + 74) % 150) + 1


def calculate_nadiamsa(
    sidereal_longitude: Any,
    *,
    subject: str = "ascendant",
    longitude_uncertainty_arcseconds: Any | None = None,
    table_path: str | Path = DEFAULT_TABLE_PATH,
) -> NadiamsaPosition:
    """Calculate a named Deva Keralam Nadiamsa without approximate fallbacks.

    ``longitude_uncertainty_arcseconds`` is an uncertainty radius, not a birth
    time.  Ascendant clock-time uncertainty must first be converted with the
    local ascensional rate.  When it is omitted, ascendant precision is marked
    unverified rather than presumed exact.
    """
    longitude = _decimal(sidereal_longitude, "sidereal_longitude") % Decimal("360")
    sign_index = int((longitude / SIGN_DEGREES).to_integral_value(rounding=ROUND_FLOOR))
    degree = longitude % SIGN_DEGREES
    quotient = (degree / DIVISION_DEGREES).to_integral_value(rounding=ROUND_FLOOR)
    physical_division = int(quotient) + 1
    # Decimal modulo normalization means 30 degrees is already the next sign.
    physical_division = min(max(physical_division, 1), DIVISIONS_PER_SIGN)
    modality = _modality(sign_index)
    ordinal = _ordinal(physical_division, modality)
    table = load_nadiamsa_table(table_path)

    start = Decimal(physical_division - 1) * DIVISION_DEGREES
    midpoint = start + HALF_DEGREES
    end = start + DIVISION_DEGREES
    offset = degree - start
    half = "former" if offset < HALF_DEGREES else "latter"
    distance_division = min(offset, DIVISION_DEGREES - offset)
    distance_half = min(abs(offset - HALF_DEGREES), distance_division)
    on_division_boundary = distance_division == 0
    on_half_boundary = offset == HALF_DEGREES

    uncertainty: Optional[Decimal]
    if longitude_uncertainty_arcseconds is None:
        uncertainty = None
    else:
        uncertainty = _decimal(longitude_uncertainty_arcseconds, "longitude_uncertainty_arcseconds")
        if uncertainty < 0:
            raise ValueError("longitude_uncertainty_arcseconds cannot be negative")

    nearest_required_boundary = min(distance_division, abs(offset - HALF_DEGREES)) * ARCSECONDS_PER_DEGREE
    subject_key = str(subject or "point").strip().lower()
    if on_division_boundary or on_half_boundary:
        precision_status = "boundary"
        warning = True
        precision_reason = "The longitude lies exactly on a Nadiamsa or half-Nadiamsa boundary."
    elif uncertainty is None and subject_key in {"ascendant", "lagna"}:
        precision_status = "unverified"
        warning = True
        precision_reason = (
            "Ascendant accuracy was not supplied; exact birth-time uncertainty must be converted "
            "with the local ascensional rate before this Nadiamsa can be treated as secure."
        )
    elif uncertainty is not None and uncertainty >= nearest_required_boundary:
        precision_status = "crosses_boundary"
        warning = True
        precision_reason = "The supplied longitude uncertainty reaches a Nadiamsa or half-Nadiamsa boundary."
    else:
        precision_status = "verified_within_boundary" if uncertainty is not None else "ephemeris_position"
        warning = False
        precision_reason = (
            "The supplied uncertainty remains inside this Nadiamsa half."
            if uncertainty is not None
            else "Planetary longitude is not birth-time precision-gated by this calculator."
        )

    return NadiamsaPosition(
        calculator_version="deva-keralam-nadiamsa/1.0.0",
        table_key=table.table_key,
        source_reference=table.source_reference,
        subject=str(subject or "point"),
        sidereal_longitude=float(longitude),
        sign_index=sign_index,
        sign_name=SIGN_NAMES[sign_index],
        sign_modality=modality,
        degree_in_sign=float(degree),
        physical_division=physical_division,
        ordinal=ordinal,
        name=table.names_by_ordinal[ordinal],
        half=half,
        start_degree_in_sign=float(start),
        midpoint_degree_in_sign=float(midpoint),
        end_degree_in_sign=float(end),
        distance_to_division_boundary_arcseconds=float(distance_division * ARCSECONDS_PER_DEGREE),
        distance_to_half_boundary_arcseconds=float(abs(offset - HALF_DEGREES) * ARCSECONDS_PER_DEGREE),
        on_division_boundary=on_division_boundary,
        on_half_boundary=on_half_boundary,
        longitude_uncertainty_arcseconds=float(uncertainty) if uncertainty is not None else None,
        precision_status=precision_status,
        birth_time_precision_warning=warning,
        precision_reason=precision_reason,
    )


def _fact(key: str, value: Any, position: NadiamsaPosition) -> ClassicalFact:
    return ClassicalFact(
        key=key,
        value=value,
        source_rules=("DEVA_KERALAM.BOOK_1.TABLE_1.NADIAMSA_ORDER",),
        source_references=(position.source_reference,),
        calculator_bindings=("classical_rules.deva_keralam.nadiamsa.calculate_nadiamsa",),
        evidence={
            "table_key": position.table_key,
            "calculator_version": position.calculator_version,
            "sidereal_longitude": position.sidereal_longitude,
        },
    )


def build_deva_keralam_fact_set(
    chart: Mapping[str, Any],
    *,
    ascendant_longitude_uncertainty_arcseconds: Any | None = None,
    table_path: str | Path = DEFAULT_TABLE_PATH,
) -> ClassicalFactSet:
    """Adapt an existing D1 chart into additive, source-carrying Nadi facts.

    This function does not mutate ``chart`` and callers must opt in to it.  It
    therefore cannot add or change fields in existing chart/chat contracts.
    """
    if not isinstance(chart, Mapping):
        raise ValueError("chart must be a mapping")
    if chart.get("ascendant") is None:
        raise ValueError("A numeric sidereal ascendant is required")

    positions: Dict[str, NadiamsaPosition] = {
        "ascendant": calculate_nadiamsa(
            chart["ascendant"],
            subject="ascendant",
            longitude_uncertainty_arcseconds=ascendant_longitude_uncertainty_arcseconds,
            table_path=table_path,
        )
    }
    for planet, row in (chart.get("planets") or {}).items():
        if not isinstance(row, Mapping) or row.get("longitude") is None:
            continue
        positions[str(planet)] = calculate_nadiamsa(
            row["longitude"], subject=str(planet), table_path=table_path
        )

    facts = ClassicalFactSet()
    for subject, position in positions.items():
        prefix = f"deva_keralam.{subject}.nadiamsa"
        values = {
            "ordinal": position.ordinal,
            "name": position.name,
            "half": position.half,
            "physical_division": position.physical_division,
            "sign_index": position.sign_index,
            "sign_name": position.sign_name,
            "sign_modality": position.sign_modality,
            "distance_to_division_boundary_arcseconds": position.distance_to_division_boundary_arcseconds,
            "distance_to_half_boundary_arcseconds": position.distance_to_half_boundary_arcseconds,
            "precision_status": position.precision_status,
            "birth_time_precision_warning": position.birth_time_precision_warning,
        }
        for suffix, value in values.items():
            facts.add(_fact(f"{prefix}.{suffix}", value, position))
    return facts
