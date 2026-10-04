from __future__ import annotations

from health_v2.natal_engine import NatalHealthBlueprintEngine


def _aries_chart(*, mercury_house: int = 6):
    return {
        "ascendant": 5.0,
        "houses": [{"house": house, "sign": house - 1} for house in range(1, 13)],
        "planets": {
            "Sun": {"house": 5, "sign": 4},
            "Moon": {"house": 4, "sign": 3},
            "Mars": {"house": 1, "sign": 0},
            "Mercury": {"house": mercury_house, "sign": 5},
            "Jupiter": {"house": 9, "sign": 8},
            "Venus": {"house": 7, "sign": 6},
            "Saturn": {"house": 10, "sign": 9},
            "Rahu": {"house": 11, "sign": 10},
            "Ketu": {"house": 5, "sign": 4},
        },
        "graha_drishti_by_house": {},
    }


def _whole_sign_chart(*, ascendant_sign: int, sixth_lord: str, sixth_lord_sign: int):
    """Build a minimal chart whose houses follow the whole-sign sequence."""
    placements = {
        "Sun": (1, ascendant_sign),
        "Moon": (2, (ascendant_sign + 1) % 12),
        "Mars": (3, (ascendant_sign + 2) % 12),
        "Mercury": (4, (ascendant_sign + 3) % 12),
        "Jupiter": (5, (ascendant_sign + 4) % 12),
        "Venus": (7, (ascendant_sign + 6) % 12),
        "Saturn": (8, (ascendant_sign + 7) % 12),
        "Rahu": (10, (ascendant_sign + 9) % 12),
        "Ketu": (4, (ascendant_sign + 3) % 12),
    }
    sixth_lord_house = ((sixth_lord_sign - ascendant_sign) % 12) + 1
    placements[sixth_lord] = (sixth_lord_house, sixth_lord_sign)
    return {
        "ascendant": ascendant_sign * 30 + 5.0,
        "houses": [
            {"house": house, "sign": (ascendant_sign + house - 1) % 12}
            for house in range(1, 13)
        ],
        "planets": {
            planet: {"house": house, "sign": sign}
            for planet, (house, sign) in placements.items()
        },
        "graha_drishti_by_house": {},
    }


def test_health_v2_is_natal_only_and_does_not_replace_legacy():
    result = NatalHealthBlueprintEngine(_aries_chart()).calculate()
    assert result["status"] == "preview"
    assert result["scope"] == "natal_vulnerability_only"
    assert result["legacy_health_unchanged"] is True
    assert result["claim_policy"]["timing_used"] is False
    assert result["claim_policy"]["clinical_diagnosis"] is False


def test_every_timing_eligible_vulnerability_is_present_in_natal_output():
    result = NatalHealthBlueprintEngine(_aries_chart()).calculate()
    ids = {row["stable_id"] for row in result["vulnerabilities"]}
    assert set(result["eligible_vulnerability_ids"]) <= ids
    assert all(
        row["support_grade"] in {"moderate", "strong"}
        for row in result["vulnerabilities"]
        if row["eligible_for_timing"]
    )
    assert all(row["constitutional_modifier"]["status"] for row in result["vulnerabilities"])


def test_named_condition_claims_retain_authored_evidence():
    result = NatalHealthBlueprintEngine(_aries_chart()).calculate()
    named = [row for row in result["vulnerabilities"] if row["claim_type"] == "named_classical_susceptibility"]
    assert all(row["source_pattern_ids"] for row in named)
    assert all(row["supporting_rules"] for row in named)


def test_output_contains_no_fatal_or_diagnostic_verdict():
    result = NatalHealthBlueprintEngine(_aries_chart()).calculate()
    rendered = str(result).lower()
    assert "serious/fatal" not in rendered
    assert "disease_risk_level" not in rendered
    assert "health_score" not in rendered


def test_capricorn_in_sixth_preserves_knee_region_in_final_vulnerabilities():
    # Keep Saturn out of Capricorn so the knee result must survive from the
    # sign occupying H6 itself, rather than from a duplicate sixth-lord sign.
    chart = _whole_sign_chart(ascendant_sign=4, sixth_lord="Saturn", sixth_lord_sign=10)
    result = NatalHealthBlueprintEngine(chart).calculate()

    assert result["sixth_house_chain"]["sixth_house_sign"] == "Capricorn"
    assert "knees" in result["sixth_house_chain"]["sixth_house_sign_zones"]
    anatomy = {
        zone
        for row in result["vulnerabilities"]
        if row["claim_type"] == "anatomical_vulnerability"
        for zone in row["body_zones"]
    }
    assert "knees" in anatomy
    knee = next(
        row for row in result["vulnerabilities"]
        if row["stable_id"] == "health.anatomy.knees"
    )
    assert "sixth_house_sign" in knee["primary_medical_factors"]
    assert knee["standing_weight"] > 0
    assert knee["confluence_count"] > 0


def test_scorpio_in_sixth_preserves_anorectal_pelvic_region_in_final_vulnerabilities():
    # Keep Mars out of Scorpio to isolate the H6-rashi anatomical contribution.
    chart = _whole_sign_chart(ascendant_sign=2, sixth_lord="Mars", sixth_lord_sign=8)
    result = NatalHealthBlueprintEngine(chart).calculate()

    assert result["sixth_house_chain"]["sixth_house_sign"] == "Scorpio"
    assert {"pelvis", "anus", "rectum", "excretory"} <= set(
        result["sixth_house_chain"]["sixth_house_sign_zones"]
    )
    anatomy = {
        zone
        for row in result["vulnerabilities"]
        if row["claim_type"] == "anatomical_vulnerability"
        for zone in row["body_zones"]
    }
    assert "anorectal and pelvic region" in anatomy


def test_authored_cardiac_surgery_pattern_reaches_health_v2_with_source_evidence():
    chart = _aries_chart()
    chart["planets"]["Sun"] = {"house": 5, "sign": 4}
    chart["planets"]["Mars"] = {"house": 5, "sign": 4}
    chart["planets"]["Saturn"] = {"house": 4, "sign": 3}
    chart["planets"]["Ketu"] = {"house": 4, "sign": 3}
    chart["graha_drishti_by_house"] = {
        5: [{"planet": "Saturn"}],
    }

    result = NatalHealthBlueprintEngine(chart).calculate()
    cardiac = next(
        row for row in result["vulnerabilities"]
        if row["stable_id"] == "health.condition.cardiac_surgery_susceptibility"
    )

    assert cardiac["claim_type"] == "named_classical_susceptibility"
    assert cardiac["system"] == "cardiovascular"
    assert cardiac["eligible_for_timing"] is True
    assert any(line.startswith("Source: Dr. K. S. Charak") for line in cardiac["supporting_rules"])


def test_health_v2_combines_shared_patterns_with_full_medical_karaka_layer():
    chart = _whole_sign_chart(ascendant_sign=2, sixth_lord="Mars", sixth_lord_sign=8)
    # Venus in H6 supplies a pressured reproductive/endocrine karaka; the
    # Scorpio sixth-chain anatomy supplies an independent matching body field.
    chart["planets"]["Venus"] = {"house": 6, "sign": 7}
    chart["planets"]["Mars"] = {"house": 8, "sign": 9}
    result = NatalHealthBlueprintEngine(chart).calculate()

    ids = {row["stable_id"] for row in result["vulnerabilities"]}
    assert "health.condition.reproductive_hormonal_cycle_susceptibility" in ids
    raw_ids = {row["key"] for row in result["technical"]["raw_condition_patterns"]}
    assert "reproductive_hormonal_cycle_susceptibility" in raw_ids


def test_planet_health_context_is_shared_beyond_sun_and_vitality_anchors():
    chart = _aries_chart(mercury_house=6)
    longitudes = {
        "Sun": 132.0, "Moon": 102.0, "Mars": 5.0, "Mercury": 170.0,
        "Jupiter": 250.0, "Venus": 200.0, "Saturn": 285.0,
        "Rahu": 315.0, "Ketu": 135.0,
    }
    for planet, longitude in longitudes.items():
        chart["planets"][planet]["longitude"] = longitude
        chart["planets"][planet]["degree"] = longitude % 30

    result = NatalHealthBlueprintEngine(chart).calculate()
    contexts = result["planet_health_contexts"]
    assert set(contexts) == set(chart["planets"])
    assert all(contexts[planet]["nakshatra_context"] for planet in chart["planets"])

    anatomy = [
        row for row in result["vulnerabilities"]
        if row["claim_type"] == "anatomical_vulnerability"
    ]
    assert anatomy
    # Mercury is the sixth lord for Aries and must carry its sign/star
    # delivery context into anatomical findings, not only the Sun card.
    assert all("Mercury" in row["source_planets"] for row in anatomy)
    assert all(
        any(context["planet"] == "Mercury" and context["nakshatra_context"] for context in row["planetary_delivery"])
        for row in anatomy
    )


def test_digestive_finding_preserves_jupiter_protection_and_mixed_lordship():
    # Leo Lagna: Jupiter rules supportive H5 and difficult H8. In H2 with
    # Saturn it must contribute protection and pressure to the same finding.
    chart = _whole_sign_chart(ascendant_sign=4, sixth_lord="Saturn", sixth_lord_sign=5)
    placements = {
        "Moon": (2, 5, 170.0), "Saturn": (2, 5, 165.0),
        "Jupiter": (2, 5, 160.0), "Mars": (8, 11, 350.0),
        "Venus": (8, 11, 340.0),
    }
    for planet, (house, sign, longitude) in placements.items():
        chart["planets"][planet].update(
            house=house, sign=sign, longitude=longitude, degree=longitude % 30,
        )
    for planet, data in chart["planets"].items():
        if data.get("longitude") is None:
            data["longitude"] = data["sign"] * 30 + 5.0
            data["degree"] = 5.0
    d9 = {
        **chart,
        "houses": [dict(row) for row in chart["houses"]],
        "planets": {planet: dict(data) for planet, data in chart["planets"].items()},
    }

    result = NatalHealthBlueprintEngine(chart, {"D9": d9}).calculate()
    digestive = next(
        row for row in result["vulnerabilities"]
        if row["stable_id"] == "health.condition.digestive_intestinal_susceptibility"
    )

    assert digestive["evidence_grade"] == "strong"
    assert digestive["delivery_balance"] == "support_and_pressure"
    assert any(
        factor["type"] == "natural_benefic" and factor["planet"] == "Jupiter" and factor["house"] == 2
        for factor in digestive["protective_rules"]
    )
    assert any(
        factor["type"] == "mixed_lordship_support" and factor["planet"] == "Jupiter" and factor["houses"] == [5]
        for factor in digestive["protective_rules"]
    )
    assert any(
        factor["type"] == "mixed_lordship_pressure" and factor["planet"] == "Jupiter" and factor["houses"] == [8]
        for factor in digestive["contradicting_rules"]
    )
    assert any(
        factor["type"] == "joined_by_malefics" and factor["planet"] == "Jupiter" and "Saturn" in factor["planets"]
        for factor in digestive["contradicting_rules"]
    )
    assert any(
        factor["type"] == "vargottama_capacity" and factor["planet"] == "Jupiter"
        for factor in digestive["capacity_modifiers"]
    )


def test_health_v2_strips_school_specific_node_aspects_but_keeps_node_occupation():
    chart = _aries_chart()
    chart["graha_drishti_by_house"] = {
        4: [{"planet": "Saturn"}, {"planet": "Ketu"}],
    }
    result = NatalHealthBlueprintEngine(chart).calculate()
    assert result["claim_policy"]["rahu_ketu_special_aspects_used"] is False
    moon = result["planet_health_contexts"]["Moon"]
    aspect = next(row for row in moon["affliction_details"] if row["type"] == "aspected_by_malefics")
    assert aspect["planets"] == ["Saturn"]
    assert result["planet_health_contexts"]["Rahu"]["house"] == 11
