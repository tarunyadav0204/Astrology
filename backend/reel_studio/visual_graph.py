"""Verified, renderer-addressable astrology graph for Reel Studio.

The director may select node/edge ids from this graph, but never create a
placement or relationship itself. Renderers resolve ids to coordinates.
"""
from __future__ import annotations

from typing import Any

from calculators.vedic_graha_drishti import GRAHA_HOUSE_ASPECTS


def _house_from_sign(sign: int, ascendant_sign: int) -> int:
    return ((int(sign) - int(ascendant_sign)) % 12) + 1


def build_visual_graph(snapshot: dict, transit_planets: dict[str, dict] | None = None, as_of: str | None = None) -> dict[str, Any]:
    asc = int(snapshot.get("ascendant_sign") or 0)
    placements = snapshot.get("placements") or []
    nodes: list[dict] = []
    edges: list[dict] = []
    by_house: dict[int, list[dict]] = {house: [] for house in range(1, 13)}
    for house in range(1, 13):
        nodes.append({"id": f"natal.d1.house.{house}", "kind": "house", "house": house})
    for row in placements:
        planet, house = str(row.get("planet")), int(row.get("house") or 0)
        if not planet or not house:
            continue
        node_id = f"natal.d1.planet.{planet.lower()}"
        nodes.append({"id": node_id, "kind": "planet", "planet": planet, "house": house})
        by_house.setdefault(house, []).append(row)
        edges.append({"id": f"edge.natal.{planet.lower()}.occupies.house_{house}", "from": node_id,
                      "to": f"natal.d1.house.{house}", "type": "occupancy"})
        for aspect_number in GRAHA_HOUSE_ASPECTS.get(planet, []):
            if aspect_number == 1:
                continue
            target = ((house + aspect_number - 2) % 12) + 1
            edges.append({"id": f"edge.natal.{planet.lower()}.aspects.house_{target}", "from": node_id,
                          "to": f"natal.d1.house.{target}", "type": "graha_drishti", "aspect_number": aspect_number})
    for planet, state in (transit_planets or {}).items():
        if planet not in GRAHA_HOUSE_ASPECTS:
            continue
        house = _house_from_sign(int(state.get("sign") or 0), asc)
        node_id = f"transit.{planet.lower()}"
        nodes.append({"id": node_id, "kind": "transit_planet", "planet": planet, "house": house,
                      "sign": int(state.get("sign") or 0), "as_of": as_of})
        edges.append({"id": f"edge.transit.{planet.lower()}.occupies.house_{house}", "from": node_id,
                      "to": f"natal.d1.house.{house}", "type": "transit_occupancy"})
        for aspect_number in GRAHA_HOUSE_ASPECTS.get(planet, []):
            if aspect_number == 1:
                continue
            target = ((house + aspect_number - 2) % 12) + 1
            edge = {"id": f"edge.transit.{planet.lower()}.aspects.house_{target}", "from": node_id,
                    "to": f"natal.d1.house.{target}", "type": "transit_aspect", "aspect_number": aspect_number}
            edges.append(edge)
            for natal in by_house.get(target, []):
                target_planet = str(natal.get("planet") or "").lower()
                edges.append({"id": f"edge.transit.{planet.lower()}.aspects.natal_{target_planet}", "from": node_id,
                              "to": f"natal.d1.planet.{target_planet}", "type": "transit_aspect_to_natal", "aspect_number": aspect_number})
    return {"schema_version": "reel.visual_graph.v1", "as_of": as_of, "nodes": nodes, "edges": edges}
