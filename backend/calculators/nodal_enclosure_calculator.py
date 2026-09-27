"""Exact Rahu–Ketu enclosure geometry for the modern Kaal Sarp convention.

No named verse for Kaal Sarp was verified in the selected classical corpus.
This module therefore reports an astronomical configuration, not a classical
dosha, a prediction, or a severity grade.  The seven visible grahas must all
be available; missing planets are never silently ignored.
"""

from __future__ import annotations

from typing import Any, Mapping


VISIBLE_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
BOUNDARY_ORB_DEGREES = 1e-6

SOURCE = {
    "tradition_status": "modern_convention",
    "classical_source_verified": False,
    "reference_label": "Modern Rahu–Ketu nodal-enclosure convention",
    "textual_note": (
        "No named verse for this formation was verified in Brihat Parashara Hora "
        "Shastra, Brihat Jataka, Saravali, Phaladeepika, or Jataka Parijata. "
        "AstroRoshni therefore reports only the exact geometry and does not attach "
        "classical effects, severity, remedies, cancellations, or named variants."
    ),
}


def _longitude(planets: Mapping[str, Any], name: str) -> float | None:
    row = planets.get(name)
    if not isinstance(row, Mapping):
        return None
    value = row.get("longitude")
    try:
        return float(value) % 360.0 if value is not None else None
    except (TypeError, ValueError):
        return None


def _forward_distance(start: float, point: float) -> float:
    return (point - start) % 360.0


def _angular_distance(first: float, second: float) -> float:
    separation = abs((first - second) % 360.0)
    return min(separation, 360.0 - separation)


def _arc_result(
    planets: Mapping[str, Any],
    start_name: str,
    start: float,
    end_name: str,
    end: float,
) -> dict[str, Any]:
    span = _forward_distance(start, end)
    inside: list[str] = []
    boundary: list[dict[str, Any]] = []
    outside: list[str] = []

    for name in VISIBLE_PLANETS:
        longitude = _longitude(planets, name)
        if longitude is None:
            continue
        distance = _forward_distance(start, longitude)
        start_orb = _angular_distance(longitude, start)
        end_orb = _angular_distance(longitude, end)
        if start_orb <= BOUNDARY_ORB_DEGREES:
            boundary.append({"planet": name, "node": start_name, "orb_degrees": round(start_orb, 8)})
        elif end_orb <= BOUNDARY_ORB_DEGREES:
            boundary.append({"planet": name, "node": end_name, "orb_degrees": round(end_orb, 8)})
        elif BOUNDARY_ORB_DEGREES < distance < span - BOUNDARY_ORB_DEGREES:
            inside.append(name)
        else:
            outside.append(name)

    return {
        "direction": f"{start_name}_to_{end_name}",
        "label": f"{start_name} → {end_name}",
        "start_longitude": round(start, 8),
        "end_longitude": round(end, 8),
        "arc_degrees": round(span, 8),
        "contained_planets": inside,
        "boundary_planets": boundary,
        "outside_planets": outside,
        "contained_count": len(inside) + len(boundary),
    }


def calculate_nodal_enclosure(chart_data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return exact nodal enclosure evidence while preserving legacy keys."""
    planets = ((chart_data or {}).get("planets") or {})
    required = (*VISIBLE_PLANETS, "Rahu", "Ketu")
    missing = [name for name in required if _longitude(planets, name) is None]
    base: dict[str, Any] = {
        "present": False,
        "complete": False,
        "strict_complete": False,
        "type": None,
        "cancellation": False,
        "cancellation_reason": "",
        "convention_name": "Rahu–Ketu nodal enclosure",
        "display_name": "Kaal Sarp convention",
        "classification": "modern_astronomical_convention",
        "source": dict(SOURCE),
        "boundary_orb_degrees": BOUNDARY_ORB_DEGREES,
        "partial_configuration": {
            "claimed": False,
            "note": "No partial Kaal Sarp threshold is claimed because definitions vary and no selected classical rule defines one.",
        },
        "named_variant": {
            "claimed": False,
            "note": "The twelve serpent-name variants are not assigned without a verified source and stable rule set.",
        },
    }
    if missing:
        return {
            **base,
            "status": "unavailable",
            "missing_planets": missing,
            "summary": "The nodal-enclosure check could not be completed because exact longitudes are missing.",
            "evidence": [],
        }

    rahu = _longitude(planets, "Rahu")
    ketu = _longitude(planets, "Ketu")
    assert rahu is not None and ketu is not None
    rahu_to_ketu = _arc_result(planets, "Rahu", rahu, "Ketu", ketu)
    ketu_to_rahu = _arc_result(planets, "Ketu", ketu, "Rahu", rahu)
    arcs = [rahu_to_ketu, ketu_to_rahu]
    complete_arcs = [arc for arc in arcs if not arc["outside_planets"]]
    selected = complete_arcs[0] if complete_arcs else max(arcs, key=lambda arc: arc["contained_count"])
    complete = bool(complete_arcs)
    has_boundary = bool(selected["boundary_planets"])
    strict_complete = complete and not has_boundary
    status = "complete" if strict_complete else "boundary" if complete else "not_formed"

    if strict_complete:
        summary = f"All seven visible planets lie strictly within the {selected['label']} half of the zodiac."
    elif complete:
        names = ", ".join(item["planet"] for item in selected["boundary_planets"])
        summary = (
            f"All seven visible planets lie within the {selected['label']} half, "
            f"but {names} is on a node boundary; this is shown separately from strict enclosure."
        )
    else:
        outside = ", ".join(selected["outside_planets"])
        summary = f"No complete nodal enclosure is present; {outside} lies outside the more populated nodal half."

    node_separation = _angular_distance(rahu, ketu)
    return {
        **base,
        "present": complete,
        "complete": complete,
        "strict_complete": strict_complete,
        "status": status,
        "type": "Nodal enclosure" if complete else None,
        "direction": selected["direction"],
        "direction_label": selected["label"],
        "contained_planets": selected["contained_planets"],
        "boundary_planets": selected["boundary_planets"],
        "outside_planets": selected["outside_planets"],
        "node_separation_degrees": round(node_separation, 8),
        "selected_arc": selected,
        "arcs_checked": arcs,
        "summary": summary,
        "evidence": [
            {
                "rule_id": "NODE-ENCLOSURE-EXACT",
                "matched": complete,
                "fact": summary,
            },
            {
                "rule_id": "NODE-BOUNDARY-EXACT",
                "matched": has_boundary,
                "fact": (
                    "Boundary planets: "
                    + (", ".join(f"{row['planet']} on {row['node']}" for row in selected["boundary_planets"]) or "none")
                ),
            },
        ],
    }

