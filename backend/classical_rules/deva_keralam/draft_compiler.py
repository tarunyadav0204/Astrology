"""Fail-closed compiler for machine-extracted Deva Keralam fact keys."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping

from .ontology import PLANETS, is_canonical_fact_key
from .reviewed_aliases import resolve_nadiamsa_name


class UnknownDraftFactKey(ValueError):
    """An extracted key has no reviewed mapping to the canonical ontology."""


# Every entry is reviewed and intentionally one-way.  Similar-looking OCR or
# model output is not normalized heuristically.
REVIEWED_EXACT_ALIASES: Mapping[str, str] = {
    "ascendant.sign": "deva_keralam.ascendant.rashi.name",
    "ascendant.sign_name": "deva_keralam.ascendant.rashi.name",
    "ascendant.house": "deva_keralam.ascendant.house",
    "ascendant.navamsa.sign": "deva_keralam.ascendant.navamsa.name",
    "ascendant.nadiamsa.ordinal": "deva_keralam.ascendant.nadiamsa.ordinal",
    "ascendant.nadiamsa.name": "deva_keralam.ascendant.nadiamsa.name",
    "ascendant.nadiamsa.half": "deva_keralam.ascendant.nadiamsa.half",
    "ascendant.nadiamsa_half.reliable": "deva_keralam.precision.ascendant.reliable",
    "native.age": "deva_keralam.timing.native.completed_age_years",
}

_DASHA_LEVEL_ALIASES = {
    "MD": "mahadasha", "AD": "antardasha", "PD": "pratyantardasha",
    "SD": "sookshma", "Pr": "prana",
}


def _reviewed_planet_alias(key: str) -> str | None:
    parts = key.split(".")
    if len(parts) < 3 or parts[0] != "planet" or parts[1] not in PLANETS:
        return None
    planet = parts[1]
    suffix = ".".join(parts[2:])
    reviewed_suffixes = {
        "sign": "rashi.name",
        "sign_name": "rashi.name",
        "house": "house",
        "lordships": "lordships",
        "navamsa.sign": "navamsa.name",
        "nadiamsa.ordinal": "nadiamsa.ordinal",
        "nadiamsa.name": "nadiamsa.name",
        "nadiamsa.half": "nadiamsa.half",
        "dignity": "dignity",
    }
    canonical_suffix = reviewed_suffixes.get(suffix)
    return f"deva_keralam.planet.{planet}.{canonical_suffix}" if canonical_suffix else None


def resolve_draft_fact_key(key: str) -> str:
    value = str(key or "").strip()
    if is_canonical_fact_key(value):
        return value
    resolved = REVIEWED_EXACT_ALIASES.get(value) or _reviewed_planet_alias(value)
    if resolved is None:
        parts = value.split(".")
        if len(parts) == 3 and parts[0] == "house" and parts[1].isdigit():
            if 1 <= int(parts[1]) <= 12 and parts[2] in {"lord", "lord_house"}:
                resolved = f"deva_keralam.house.{int(parts[1])}.{parts[2]}"
        elif len(parts) == 3 and parts[0] == "dasha":
            level = _DASHA_LEVEL_ALIASES.get(parts[1], parts[1])
            if level in {"mahadasha", "antardasha", "pratyantardasha", "sookshma", "prana"} and parts[2] in {"lord", "ordinal", "start", "end", "active"}:
                resolved = f"deva_keralam.timing.dasha.{level}.{parts[2]}"
    if resolved and is_canonical_fact_key(resolved):
        return resolved
    raise UnknownDraftFactKey(f"No reviewed Deva Keralam fact mapping for: {value!r}")


def compile_draft_expression(expression: Mapping[str, Any]) -> Dict[str, Any]:
    """Compile a Boolean fact AST without altering operators or expected values."""
    if not isinstance(expression, Mapping):
        raise TypeError("Draft expression must be an object")
    compiled = deepcopy(dict(expression))
    operator = str(compiled.get("op") or "").lower()
    if operator == "fact":
        compiled["key"] = resolve_draft_fact_key(str(compiled.get("key") or ""))
        if compiled["key"].endswith(".nadiamsa.name") and "value" in compiled:
            canonical, alias = resolve_nadiamsa_name(compiled["value"])
            compiled["value"] = canonical
            if alias is not None:
                compiled["reviewed_value_alias"] = alias.as_dict()
        return compiled
    children = compiled.get("children")
    if operator not in {"all", "any", "at_least", "not"} or not isinstance(children, list):
        raise ValueError(f"Unsupported or malformed draft expression operator: {operator!r}")
    compiled["children"] = [compile_draft_expression(child) for child in children]
    return compiled
