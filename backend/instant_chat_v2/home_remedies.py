"""Classical, chart-derived remedies for Home and Property routes.

This module deliberately does not use the running dasha.  A static remedy
question first diagnoses the natal obstruction through D1 and D4, then maps
the highest-ranked responsible graha to a conservative Navagraha-shanti
practice.  It does not manufacture coaching, budgeting or lifestyle advice.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


_PRESSURE_PLANETS = frozenset({"Saturn", "Mars", "Rahu", "Ketu"})
_DIFFICULT_DIGNITIES = frozenset({"debilitated", "enemy_sign"})
_DUSTHANA = frozenset({6, 8, 12})


_CLASSICAL_GRAHA_SHANTI: dict[str, dict[str, str]] = {
    "Sun": {
        "action": "At sunrise, offer clean water to Surya and recite Om Hraam Hreem Hraum Sah Suryaya Namah 108 times.",
        "frequency": "Every Sunday for 11 consecutive Sundays.",
        "dana": "Offer wheat or copper in charity on Sunday according to your means.",
        "devata": "Surya",
    },
    "Moon": {
        "action": "On Monday, worship Shiva and recite Om Shraam Shreem Shraum Sah Chandraya Namah 108 times.",
        "frequency": "Every Monday for 11 consecutive Mondays.",
        "dana": "Offer rice or white cloth in charity on Monday according to your means.",
        "devata": "Shiva and Chandra",
    },
    "Mars": {
        "action": "On Tuesday, recite the Hanuman Chalisa and Om Kraam Kreem Kraum Sah Bhaumaya Namah 108 times.",
        "frequency": "Every Tuesday for 11 consecutive Tuesdays.",
        "dana": "Offer red lentils in charity on Tuesday according to your means.",
        "devata": "Hanuman and Mangala",
    },
    "Mercury": {
        "action": "On Wednesday, worship Vishnu and recite Om Braam Breem Braum Sah Budhaya Namah 108 times.",
        "frequency": "Every Wednesday for 11 consecutive Wednesdays.",
        "dana": "Offer green gram or educational materials in charity on Wednesday according to your means.",
        "devata": "Vishnu and Budha",
    },
    "Jupiter": {
        "action": "On Thursday, worship Brihaspati or Vishnu and recite Om Graam Greem Graum Sah Gurave Namah 108 times.",
        "frequency": "Every Thursday for 11 consecutive Thursdays.",
        "dana": "Offer chana dal or turmeric in charity on Thursday according to your means.",
        "devata": "Brihaspati and Vishnu",
    },
    "Venus": {
        "action": "On Friday, worship Lakshmi and recite Om Draam Dreem Draum Sah Shukraya Namah 108 times.",
        "frequency": "Every Friday for 11 consecutive Fridays.",
        "dana": "Offer white cloth or white sweets in charity on Friday according to your means.",
        "devata": "Lakshmi and Shukra",
    },
    "Saturn": {
        "action": "On Saturday after sunset, light a sesame-oil lamp for Shani and recite Om Praam Preem Praum Sah Shanaye Namah 108 times.",
        "frequency": "Every Saturday for 11 consecutive Saturdays.",
        "dana": "Offer black sesame or mustard oil in charity on Saturday according to your means.",
        "devata": "Shani",
    },
    "Rahu": {
        "action": "On Saturday, worship Durga and recite Om Bhraam Bhreem Bhraum Sah Rahave Namah 108 times.",
        "frequency": "Every Saturday for 11 consecutive Saturdays.",
        "dana": "Offer a dark blanket or black sesame in charity on Saturday according to your means.",
        "devata": "Durga and Rahu",
    },
    "Ketu": {
        "action": "On Tuesday, worship Ganesha and recite Om Sraam Sreem Sraum Sah Ketave Namah 108 times.",
        "frequency": "Every Tuesday for 11 consecutive Tuesdays.",
        "dana": "Offer sesame or a blanket in charity on Tuesday according to your means.",
        "devata": "Ganesha and Ketu",
    },
}


def _integer(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _challenging_aspector(row: Mapping[str, Any]) -> bool:
    planet = str(row.get("planet") or "")
    tone = str(row.get("tone") or "").lower()
    return planet in _PRESSURE_PLANETS or ("malefic" in tone and "benefic" not in tone)


def _add_candidate(
    candidates: dict[str, dict[str, Any]],
    planet: Any,
    *,
    score: float,
    reason: str,
    chart: str,
    house: int,
    role: str,
) -> None:
    name = str(planet or "").strip()
    if name not in _CLASSICAL_GRAHA_SHANTI:
        return
    row = candidates.setdefault(name, {"planet": name, "obstruction_score": 0.0, "evidence": []})
    row["obstruction_score"] = round(float(row["obstruction_score"]) + score, 3)
    row["evidence"].append({
        "chart": chart,
        "house": house,
        "role": role,
        "reason": reason,
        "weight": score,
    })


def _score_condition(
    candidates: dict[str, dict[str, Any]],
    row: Mapping[str, Any],
    *,
    chart_weight: float,
    fourth_house: bool,
) -> None:
    if not row.get("available"):
        return
    chart = str(row.get("chart") or "")
    house = _integer(row.get("house"))
    if house is None:
        return
    lord = str(row.get("lord") or "")
    lord_house = _integer(row.get("lord_house"))
    dignity = str(row.get("lord_dignity") or "").lower()

    if dignity in _DIFFICULT_DIGNITIES or lord_house in _DUSTHANA:
        pressure_cause = (
            dignity.replace("_", " ")
            if dignity in _DIFFICULT_DIGNITIES
            else f"placement in House {lord_house}"
        )
        _add_candidate(
            candidates,
            lord,
            score=chart_weight * (5.5 if fourth_house else 2.25),
            reason=(
                f"{chart} House {house} lord {lord} is under pressure through "
                f"{pressure_cause}."
            ),
            chart=chart,
            house=house,
            role="pressured_house_lord",
        )

    for planet in row.get("occupants") or []:
        if str(planet) in _PRESSURE_PLANETS:
            _add_candidate(
                candidates,
                planet,
                score=chart_weight * (4.5 if fourth_house else 1.5),
                reason=f"{chart} {planet} occupies House {house} and contributes pressure to this property factor.",
                chart=chart,
                house=house,
                role="challenging_occupant",
            )

    for aspect in row.get("house_aspects") or []:
        if not isinstance(aspect, Mapping) or not _challenging_aspector(aspect):
            continue
        planet = str(aspect.get("planet") or "")
        _add_candidate(
            candidates,
            planet,
            score=chart_weight * (6.0 if fourth_house else 1.25),
            reason=f"{chart} {planet} directly aspects House {house} and is the calculated pressure on this property factor.",
            chart=chart,
            house=house,
            role="challenging_aspector",
        )


def _score_natal_factors(
    candidates: dict[str, dict[str, Any]],
    factors_by_house: Mapping[int, Sequence[Mapping[str, Any]]],
) -> None:
    for house, factors in factors_by_house.items():
        for factor in factors:
            if str(factor.get("polarity") or "").lower() != "challenging":
                continue
            source = str(factor.get("source") or "")
            facts = factor.get("facts") if isinstance(factor.get("facts"), Mapping) else {}
            # A reversed or cancelled Avayogi contribution must not be ranked
            # as the obstruction. Independent afflictions remain eligible.
            avayogi_effect = facts.get("avayogi_effect") if isinstance(facts.get("avayogi_effect"), Mapping) else {}
            if source == "avayogi_lord" and str(avayogi_effect.get("polarity") or "") in {"neutral", "supportive"}:
                continue
            planet = factor.get("planet")
            weight = min(3.0, max(0.5, abs(float(factor.get("weight") or 0.5))))
            _add_candidate(
                candidates,
                planet,
                score=weight * (1.5 if house == 4 else 0.65),
                reason=f"The D1 property ledger records {planet} as a challenging {source.replace('_', ' ')} for House {house}.",
                chart="D1",
                house=house,
                role=source or "challenging_natal_factor",
            )


def build_classical_property_remedy_blueprint(
    *,
    d1_conditions: Sequence[Mapping[str, Any]],
    d4_conditions: Sequence[Mapping[str, Any]],
    natal_factors_by_house: Mapping[int, Sequence[Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Select traditional property remedies from the calculated obstruction."""
    candidates: dict[str, dict[str, Any]] = {}
    for row in d1_conditions:
        _score_condition(candidates, row, chart_weight=1.0, fourth_house=_integer(row.get("house")) == 4)
    for row in d4_conditions:
        _score_condition(candidates, row, chart_weight=0.75, fourth_house=_integer(row.get("house")) == 4)
    _score_natal_factors(candidates, natal_factors_by_house or {})

    ranked = sorted(
        candidates.values(),
        key=lambda row: (-float(row.get("obstruction_score") or 0), str(row.get("planet") or "")),
    )
    d1_fourth_available = any(
        row.get("available") and _integer(row.get("house")) == 4
        for row in d1_conditions
    )
    d4_fourth_available = any(
        row.get("available") and _integer(row.get("house")) == 4
        for row in d4_conditions
    )
    calculation_complete = d1_fourth_available and d4_fourth_available
    remedies: list[dict[str, Any]] = []
    for rank, driver in enumerate(ranked[:3], start=1):
        planet = str(driver["planet"])
        practice = _CLASSICAL_GRAHA_SHANTI[planet]
        evidence = sorted(driver.get("evidence") or [], key=lambda row: -float(row.get("weight") or 0))
        strongest = evidence[0] if evidence else {}
        remedies.append({
            "rank": rank,
            "planet": planet,
            "classification": "classical_graha_shanti",
            "tradition": "Traditional Navagraha upaya",
            "action": practice["action"],
            "frequency": practice["frequency"],
            "dana": practice["dana"],
            "devata": practice["devata"],
            "astrological_reason": strongest.get("reason"),
            "calculated_role": strongest.get("role"),
            "obstruction_score": driver["obstruction_score"],
            "evidence": evidence[:5],
            "claim_boundary": "This is a traditional spiritual upaya, not a guarantee of purchase, sale, possession or dispute resolution.",
        })

    top = remedies[0] if remedies and calculation_complete else {}
    return {
        "schema_version": "classical-property-remedy/v1",
        "scope": "static natal Home/Property obstruction remedy from D1 and D4",
        "selection_mode": "single_top",
        "selection_rule": (
            "Rank the graha directly pressuring D1 House 4 first, then the D1 House 4 lord and D4 House 4, "
            "then repeated obstruction houses. Do not select from current dasha or transit."
        ),
        "candidate_planets": [row["planet"] for row in ranked],
        "ranked_remedies": remedies,
        "top_recommendation": top,
        "alternatives": remedies[1:3],
        "priority_order": [
            f"{row['planet']}: {row.get('astrological_reason') or 'calculated property pressure'}"
            for row in remedies
        ],
        "remedy_sections": {"classical_graha_shanti": remedies},
        "caution": (
            "Use one calculated graha-shanti practice consistently. Do not prescribe a gemstone from this packet; "
            "gemstone suitability needs a separate full-chart judgment."
            if top else
            "No responsible graha-specific property remedy can be selected without a calculated D1/D4 obstruction."
        ),
        "evidence_complete": bool(top) and calculation_complete,
        "required_layers": {
            "d1_fourth_house": d1_fourth_available,
            "d4_fourth_house": d4_fourth_available,
        },
        "forbidden_substitutions": [
            "budgeting advice presented as an astrological remedy",
            "communication or journaling exercises",
            "current dasha or transit used to choose a static property remedy",
            "gemstone prescription without a separate suitability analysis",
            "Vastu claim without inspecting the property",
        ],
    }
