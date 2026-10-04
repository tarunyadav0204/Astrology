from datetime import date, datetime

from health_v2.divisional_confirmation_engine import D30HealthConfirmationEngine
from health_v2.timing_engine import HealthTimingHeatmapEngine


def _chart():
    return {
        "ascendant": 5.0,
        "houses": [{"house": h, "sign": h - 1} for h in range(1, 13)],
        "planets": {
            "Sun": {"house": 5, "sign": 4, "longitude": 130.0},
            "Moon": {"house": 4, "sign": 3, "longitude": 100.0},
            "Mars": {"house": 1, "sign": 0, "longitude": 10.0},
            "Mercury": {"house": 6, "sign": 5, "longitude": 160.0},
            "Jupiter": {"house": 9, "sign": 8, "longitude": 250.0},
            "Venus": {"house": 7, "sign": 6, "longitude": 190.0},
            "Saturn": {"house": 10, "sign": 9, "longitude": 280.0},
            "Rahu": {"house": 11, "sign": 10, "longitude": 310.0},
            "Ketu": {"house": 5, "sign": 4, "longitude": 130.0},
        },
    }


def _blueprint():
    conditions = {}
    for name, row in _chart()["planets"].items():
        conditions[name] = {
            "planet": name,
            "house": row["house"],
            "functional_role": {"ruled_houses": []},
            "finding_modifiers": {
                "support": [{"type": "natural_benefic"}] if name == "Jupiter" else [],
                "pressure": [{"type": "natural_malefic"}] if name in {"Mars", "Saturn", "Rahu", "Ketu"} else [],
            },
        }
    return {
        "planet_health_contexts": conditions,
        "vulnerabilities": [{
            "stable_id": "health.anatomy.digestion",
            "label": "Digestive vulnerability",
            "body_zones": ["digestion"],
            "eligible_for_timing": True,
            "evidence_grade": "strong",
            "source_planets": ["Mercury"],
            "planetary_delivery": [{"planet": "Mercury", "house": 6}],
            "supporting_rules": ["Mercury occupies House 6"],
            "protective_rules": [],
            "contradicting_rules": [],
        }],
    }


def _dashas(_day, _birth):
    planets = ["Jupiter", "Mercury", "Mercury", "Mercury", "Moon"]
    return {
        level: {"planet": planet, "start": "2026-09-01", "end": "2026-09-30"}
        for level, planet in zip(
            ("mahadasha", "antardasha", "pratyantardasha", "sookshma", "prana"), planets
        )
    }


def test_heatmap_requires_both_dasha_permission_and_real_transit_contact():
    far = lambda day, planet: {"planet": planet, "longitude": 17.0}
    result = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {}, dasha_provider=_dashas, transit_provider=far
    ).calculate(date(2026, 9, 1), 1)
    assert result["days"][0]["heat_level"] == 0
    assert result["days"][0]["details"] == []


def test_timing_uses_three_dasha_levels_and_builds_a_health_window():
    def contacts(_day, planet):
        # Jupiter sustains the H6 window; Sun supplies a stronger phase.
        return {"planet": planet, "longitude": 160.0 if planet in {"Sun", "Jupiter"} else 17.0}

    result = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {}, dasha_provider=_dashas, transit_provider=contacts
    ).calculate(date(2026, 9, 1), 1)
    detail = result["days"][0]["details"][0]
    assert result["days"][0]["heat_level"] > 0
    assert [row["level"] for row in detail["dasha_chain"]] == [
        "mahadasha", "antardasha", "pratyantardasha"
    ]
    mercury_pd = detail["dasha_chain"][2]
    assert mercury_pd["direct_finding_planet"] is True
    assert mercury_pd["natal_house"] == 6
    assert mercury_pd["connected_houses"] == []
    assert next(row for row in detail["transit_contacts"] if row["transit_planet"] == "Sun")["orb"] == 0.0
    sun_contact = next(row for row in detail["transit_contacts"] if row["transit_planet"] == "Sun")
    assert sun_contact["transit_house"] == 6
    assert sun_contact["natal_house"] == 6
    assert sun_contact["aspect_number"] == 1
    assert detail["transit_house_activations"]
    summary = detail["activation_summary"]
    assert summary["dasha_houses"] == [6]
    assert summary["transit_houses"] == [6]
    assert summary["confirmed_houses"] == [6]
    house_six = summary["houses"][0]
    assert house_six["confirmed_by_both"] is True
    assert any(row["mode"] == "natal_occupation" for row in house_six["dasha_activators"])
    assert any(row["mode"] == "occupation" for row in house_six["transit_activators"])
    assert result["claim_policy"]["sustained_transit_required_for_window"] is True
    assert result["claim_policy"]["heat_is_probability"] is False
    assert result["claim_policy"]["sookshma_prana_used"] is False
    assert result["windows"][0]["start_date"] == "2026-09-01"
    assert result["windows"][0]["end_date"] == "2026-09-01"
    assert result["windows"][0]["detail"]["activation_summary"]["condition_link"] == {
        "finding_id": "health.anatomy.digestion",
        "label": "Digestive vulnerability",
        "body_zones": ["digestion"],
        "natal_planets": ["Mercury"],
        "natal_houses": [6],
        "natal_rules": ["Mercury occupies House 6"],
        "dasha_repeated_houses": [6],
        "transit_repeated_houses": [6],
        "confirmed_houses": [6],
    }


def test_node_fifth_and_ninth_aspects_are_not_used():
    def node_fifth_only(_day, planet):
        # Rahu is 120 degrees away from natal Mercury. This would be a disputed
        # fifth aspect; it must not colour the day.
        return {"planet": planet, "longitude": 40.0 if planet == "Rahu" else 17.0}

    result = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {}, dasha_provider=_dashas, transit_provider=node_fifth_only
    ).calculate(date(2026, 9, 1), 1)
    assert result["days"][0]["heat_level"] == 0
    assert result["claim_policy"]["node_fifth_ninth_aspects_used"] is False


def test_classical_aspect_number_is_exposed_instead_of_only_degree_geometry():
    def mars_eighth_aspect(_day, planet):
        # Natal Mercury is at 160 degrees; Mars at 310 degrees reaches it by
        # its 8th-house (210-degree) special aspect.
        return {"planet": planet, "longitude": 310.0 if planet == "Mars" else 17.0}

    result = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {}, dasha_provider=_dashas,
        transit_provider=mars_eighth_aspect,
    ).calculate(date(2026, 9, 1), 1)
    contact = next(
        row for row in result["days"][0]["details"][0]["transit_contacts"]
        if row["transit_planet"] == "Mars"
    )
    assert contact["aspect_angle"] == 210
    assert contact["aspect_number"] == 8


def test_sustained_transit_opens_window_without_sun_or_moon_and_days_are_merged():
    def sustained(_day, planet):
        return {"planet": planet, "longitude": 160.0 if planet == "Jupiter" else 17.0}

    result = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {}, dasha_provider=_dashas, transit_provider=sustained
    ).calculate(date(2026, 9, 1), 3)
    assert len(result["windows"]) == 1
    window = result["windows"][0]
    assert window["start_date"] == "2026-09-01"
    assert window["end_date"] == "2026-09-03"
    assert window["phase"] == "active_window"
    assert window["sun_phases"] == []
    assert window["moon_peak_dates"] == []
    assert len(result["period_groups"]) == 1
    group = result["period_groups"][0]
    assert group["group_id"] == "2026-09-01:health.anatomy.digestion"
    assert group["start_date"] == "2026-09-01"
    assert group["end_date"] == "2026-09-03"
    assert group["activation_level"] == window["activation_level"]
    assert group["finding_count"] == 1
    assert group["windows"][0]["finding_id"] == "health.anatomy.digestion"


def test_moon_contact_alone_refines_a_day_but_cannot_create_peak():
    def moon_only(_day, planet):
        # Jupiter supplies the sustained structural confirmation. Moon exactly
        # contacts natal Mercury, but there is no Sun or active-dasha-lord
        # transit to create a bounded concentration.
        return {
            "planet": planet,
            "longitude": 160.0 if planet in {"Jupiter", "Moon"} else 17.0,
        }

    result = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {}, dasha_provider=_dashas, transit_provider=moon_only
    ).calculate(date(2026, 9, 1), 1)

    detail = result["days"][0]["details"][0]
    window = result["windows"][0]
    assert detail["activation_summary"]["moon_triggers"]
    assert detail["phase"] == "active_window"
    assert detail["heat_level"] < 4
    assert window["key_concentration_phases"] == []
    assert window["moon_peak_dates"] == ["2026-09-01"]


def test_active_dasha_lord_direct_transit_is_a_bounded_heightened_phase():
    def active_lord_contact(_day, planet):
        # Mercury is active in AD/PD and directly returns to natal Mercury.
        # Jupiter continues to supply independent structural confirmation.
        return {
            "planet": planet,
            "longitude": 160.0 if planet in {"Mercury", "Jupiter"} else 17.0,
        }

    result = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {}, dasha_provider=_dashas,
        transit_provider=active_lord_contact,
    ).calculate(date(2026, 9, 1), 1)

    detail = result["days"][0]["details"][0]
    window = result["windows"][0]
    trigger = detail["activation_summary"]["active_dasha_transit_triggers"][0]
    assert trigger["transit_planet"] == "Mercury"
    assert trigger["natal_planet"] == "Mercury"
    assert detail["phase"] == "heightened"
    assert detail["heat_level"] == 3
    assert window["key_concentration_basis"] == "active_dasha_chain_exact_contact"
    assert window["key_concentration_phases"] == [
        {
            "start_date": "2026-09-01", "end_date": "2026-09-01",
            "basis": "active_dasha_chain_exact_contact",
            "bases": ["active_dasha_chain_exact_contact"],
        },
    ]


def test_node_dispositor_and_joined_dasha_lord_carry_anatomical_timing():
    """Regression for chart 10323's 29 Dec 2025 anorectal surgery window.

    The fixture contains only astronomical/calculation facts.  The known
    surgery outcome is not used as an input or a scoring override.
    """
    chart = {
        "ascendant": 78.9089,
        "houses": [{"house": house, "sign": (2 + house - 1) % 12} for house in range(1, 13)],
        "planets": {
            "Sun": {"house": 12, "sign": 1, "longitude": 40.520},
            "Moon": {"house": 9, "sign": 10, "longitude": 325.135},
            "Mars": {"house": 11, "sign": 0, "longitude": 17.045},
            "Mercury": {"house": 11, "sign": 0, "longitude": 21.541},
            "Jupiter": {"house": 11, "sign": 0, "longitude": 3.980},
            "Venus": {"house": 11, "sign": 0, "longitude": 18.353},
            "Saturn": {"house": 4, "sign": 5, "longitude": 166.696},
            "Rahu": {"house": 7, "sign": 8, "longitude": 240.603},
            "Ketu": {"house": 1, "sign": 2, "longitude": 60.603},
        },
    }
    conditions = {
        planet: {
            "planet": planet,
            "house": row["house"],
            "functional_role": {"ruled_houses": {
                "Saturn": [8, 9], "Mercury": [1, 4], "Mars": [6, 11],
                "Jupiter": [7, 10],
            }.get(planet, [])},
            "nakshatra_context": (
                {"lord": "Ketu"} if planet == "Rahu" else
                {"lord": "Mars"} if planet == "Ketu" else {}
            ),
            "finding_modifiers": {"support": [], "pressure": []},
        }
        for planet, row in chart["planets"].items()
    }
    finding = {
        "stable_id": "health.anatomy.anorectal_and_pelvic_region",
        "label": "Anorectal and pelvic region anatomical vulnerability",
        "claim_type": "anatomical_vulnerability",
        "body_zones": ["anus", "rectum", "pelvic region"],
        "eligible_for_timing": True,
        "evidence_grade": "moderate",
        "source_planets": ["Mars"],
        "timing_planets": ["Mars"],
        "timing_houses": [6],
        "planetary_delivery": [{"planet": "Mars", "house": 11}],
        "supporting_rules": ["Scorpio in House 6 links the disease axis to the anorectal region."],
        "protective_rules": [],
        "contradicting_rules": [],
    }
    d30 = {
        # Gemini D30: Scorpio falls in H6, so its lord Mars carries the
        # disease house into H7 (rectum and anal canal in the medical-house
        # anatomy table).  The engine must derive this link, not receive it as
        # a case-specific rule.
        "ascendant": 64.0,
        "planets": {
            "Sun": {"house": 3, "sign": 2},
            "Moon": {"house": 4, "sign": 3},
            "Mars": {"house": 7, "sign": 6},
            "Mercury": {"house": 6, "sign": 5},
            "Jupiter": {"house": 9, "sign": 8},
            "Venus": {"house": 2, "sign": 1},
            "Saturn": {"house": 10, "sign": 9},
            "Rahu": {"house": 5, "sign": 4},
            "Ketu": {"house": 11, "sign": 10},
        },
    }
    d30_confirmation = D30HealthConfirmationEngine(chart, d30).calculate([finding])
    finding["d30_confirmation"] = d30_confirmation["finding_confirmations"][finding["stable_id"]]
    blueprint = {
        "planet_health_contexts": conditions,
        "vulnerabilities": [finding],
        "divisional_health_confirmation": {"D30": d30_confirmation},
    }

    def periods(_day, _birth):
        return {
            "mahadasha": {"planet": "Saturn", "start": "2021-03-28", "end": "2040-03-27"},
            "antardasha": {"planet": "Mercury", "start": "2024-03-30", "end": "2026-12-08"},
            "pratyantardasha": {"planet": "Rahu", "start": "2025-09-30", "end": "2026-02-25"},
            "sookshma": {"planet": "Ketu", "start": "2025-12-25", "end": "2026-01-03"},
            "prana": {"planet": "Rahu", "start": "2025-12-29", "end": "2025-12-30"},
        }

    transits = {
        "Sun": 253.566, "Moon": 2.544, "Mars": 256.378,
        "Mercury": 240.289, "Jupiter": 87.489, "Venus": 251.551,
        "Saturn": 331.792, "Rahu": 318.094, "Ketu": 138.094,
    }
    result = HealthTimingHeatmapEngine(
        chart, blueprint, {}, dasha_provider=periods,
        transit_provider=lambda _day, planet: {"planet": planet, "longitude": transits[planet]},
    ).calculate(date(2025, 12, 29), 1)

    detail = result["days"][0]["details"][0]
    assert result["days"][0]["primary_finding_id"] == finding["stable_id"]
    assert "joined_finding_planet" in detail["dasha_chain"][1]["reasons"]
    assert "node_dispositor_carries_finding" in detail["dasha_chain"][2]["reasons"]
    assert "node_nakshatra_lord_carries_finding" in detail["refinement_dasha_chain"][0]["reasons"]
    contacts = detail["transit_contacts"]
    assert any(row["transit_planet"] == "Saturn" and row["natal_planet"] == "Rahu" for row in contacts)
    assert any(row["transit_planet"] == "Mercury" and row["natal_planet"] == "Rahu" for row in contacts)
    assert detail["manifestation_scope"] == "treatment_or_intervention_attention"
    assert detail["intervention_gate"]["mars_carrier_activated_by_dasha"] is True
    assert detail["d30_confirmation"]["anatomical_link_activated"] is True
    assert any(
        row["planet"] == "Mars"
        and row["source_house"] == 6
        and row["destination_house"] == 7
        for row in detail["d30_confirmation"]["anatomical_links"]
    )
    assert {row["planet"] for row in result["windows"][0]["lower_dasha_phases"]} == {"Ketu", "Rahu"}


def test_sun_contact_can_create_peak_but_moon_is_not_required():
    def sun_trigger(_day, planet):
        return {
            "planet": planet,
            "longitude": 160.0 if planet in {"Sun", "Jupiter"} else 17.0,
        }

    result = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {}, dasha_provider=_dashas, transit_provider=sun_trigger
    ).calculate(date(2026, 9, 1), 1)

    detail = result["days"][0]["details"][0]
    assert detail["activation_summary"]["sun_triggers"]
    assert detail["activation_summary"]["moon_triggers"] == []
    assert detail["phase"] == "peak"
    assert detail["heat_level"] == 4


def test_overlapping_findings_are_grouped_into_one_user_facing_period():
    blueprint = _blueprint()
    second = dict(blueprint["vulnerabilities"][0])
    second.update({
        "stable_id": "health.anatomy.second_digestive_pattern",
        "label": "Second digestive pattern",
    })
    blueprint["vulnerabilities"].append(second)

    def sustained(_day, planet):
        return {"planet": planet, "longitude": 160.0 if planet == "Jupiter" else 17.0}

    result = HealthTimingHeatmapEngine(
        _chart(), blueprint, {}, dasha_provider=_dashas, transit_provider=sustained
    ).calculate(date(2026, 9, 1), 3)
    assert len(result["windows"]) == 2
    assert len(result["period_groups"]) == 1
    assert result["period_groups"][0]["finding_count"] == 2


def test_sookshma_and_prana_cannot_open_a_window_when_pratyantardasha_does_not_match():
    def lower_only(_day, _birth):
        return {
            "mahadasha": {"planet": "Jupiter"},
            "antardasha": {"planet": "Jupiter"},
            "pratyantardasha": {"planet": "Venus"},
            "sookshma": {"planet": "Mercury"},
            "prana": {"planet": "Mercury"},
        }

    def sustained(_day, planet):
        return {"planet": planet, "longitude": 160.0 if planet == "Jupiter" else 17.0}

    result = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {}, dasha_provider=lower_only, transit_provider=sustained
    ).calculate(date(2026, 9, 1), 1)
    assert result["windows"] == []


def test_ketu_prana_refines_h6_sign_anatomy_without_granting_permission():
    chart = _chart()
    chart["ascendant"] = 126.0  # Leo: Cancer is H12 and Capricorn is H6.
    chart["planets"]["Saturn"].update({"house": 2, "sign": 5, "longitude": 160.0})
    chart["planets"]["Venus"].update({"house": 8, "sign": 11, "longitude": 340.0})
    chart["planets"]["Rahu"].update({"house": 12, "sign": 3, "longitude": 100.0})
    chart["planets"]["Ketu"].update({"house": 6, "sign": 9, "longitude": 280.0})
    conditions = {}
    for name, row in chart["planets"].items():
        conditions[name] = {
            "planet": name,
            "house": row["house"],
            "functional_role": {"ruled_houses": [6] if name == "Saturn" else []},
            "finding_modifiers": {"support": [], "pressure": []},
        }
    common = {
        "body_zones": [],
        "eligible_for_timing": True,
        "evidence_grade": "moderate",
        "source_planets": ["Saturn"],
        "timing_planets": ["Saturn"],
        "timing_houses": [6],
        "planetary_delivery": [{"planet": "Saturn", "house": 2}],
        "supporting_rules": ["The sign in House 6 supplies the anatomical field"],
        "protective_rules": [],
        "contradicting_rules": [],
    }
    knee = {
        **common,
        "stable_id": "health.anatomy.knees",
        "label": "Knees anatomical vulnerability",
        "body_zones": ["knees"],
        "primary_medical_factors": ["sixth_house_sign"],
    }
    hands = {
        **common,
        "stable_id": "health.anatomy.hands",
        "label": "Hands anatomical vulnerability",
        "body_zones": ["hands"],
        "primary_medical_factors": ["sixth_lord_nakshatra"],
    }
    blueprint = {"planet_health_contexts": conditions, "vulnerabilities": [hands, knee]}

    def periods(_day, _birth):
        return {
            "mahadasha": {"planet": "Saturn", "start": "2019-09-15", "end": "2038-09-15"},
            "antardasha": {"planet": "Venus", "start": "2026-07-06", "end": "2029-09-05"},
            "pratyantardasha": {"planet": "Venus", "start": "2026-07-06", "end": "2027-01-15"},
            "sookshma": {"planet": "Rahu", "start": "2026-09-13", "end": "2026-10-12"},
            "prana": {"planet": "Ketu", "start": "2026-09-30", "end": "2026-10-02"},
        }

    transit_longitudes = {
        "Sun": 160.0,       # crosses natal Saturn in H2
        "Mars": 100.0,      # H12, seventh aspect to H6
        "Jupiter": 100.0,   # H12, seventh aspect to H6
        "Saturn": 340.0,    # H8, seventh aspect to transit Sun
    }
    result = HealthTimingHeatmapEngine(
        chart,
        blueprint,
        {},
        dasha_provider=periods,
        transit_provider=lambda _day, planet: {
            "planet": planet,
            "longitude": transit_longitudes.get(planet, 17.0),
        },
    ).calculate(date(2026, 10, 1), 1)

    day = result["days"][0]
    assert day["primary_finding_id"] == "health.anatomy.knees"
    knee_detail = next(row for row in day["details"] if row["finding_id"] == "health.anatomy.knees")
    hands_detail = next(row for row in day["details"] if row["finding_id"] == "health.anatomy.hands")
    assert knee_detail["evidence_score"] > hands_detail["evidence_score"]
    assert knee_detail["score_components"]["anatomical_specificity"] == 2
    assert knee_detail["manifestation_scope"] == "treatment_or_intervention_attention"
    assert result["claim_policy"]["sookshma_prana_permission_used"] is False
    assert result["claim_policy"]["sookshma_prana_refinement_used"] is True
    assert result["windows"][0]["key_concentration_phases"] == [
        {
            "start_date": "2026-10-01", "end_date": "2026-10-01",
                "basis": "anatomical_specificity_and_sun",
                "bases": ["anatomical_specificity_and_sun"],
        },
    ]
    assert result["windows"][0]["lower_dasha_phases"] == [
        {"level": "sookshma", "planet": "Rahu", "start_date": "2026-10-01", "end_date": "2026-10-01"},
        {"level": "prana", "planet": "Ketu", "start_date": "2026-10-01", "end_date": "2026-10-01"},
    ]


def test_named_condition_cannot_be_selected_by_broad_house_links_without_its_planet():
    chart = _chart()
    conditions = _blueprint()["planet_health_contexts"]
    conditions["Saturn"]["functional_role"] = {"ruled_houses": [6]}
    finding = {
        "stable_id": "health.condition.mental_emotional_regulation_susceptibility",
        "label": "Mental and emotional regulation susceptibility",
        "claim_type": "named_classical_susceptibility",
        "body_zones": ["mind", "sleep"],
        "eligible_for_timing": True,
        "evidence_grade": "moderate",
        "source_planets": ["Moon", "Mercury"],
        "timing_planets": ["Moon", "Mercury"],
        "timing_houses": [4, 5, 12],
        "planetary_delivery": [],
        "supporting_rules": ["Moon receives natal pressure"],
        "protective_rules": [],
        "contradicting_rules": [],
    }

    def broad_house_chain(_day, _birth):
        return {
            "mahadasha": {"planet": "Saturn"},  # aspects H4 from natal H10
            "antardasha": {"planet": "Venus"},
            "pratyantardasha": {"planet": "Venus"},
            "sookshma": {"planet": "Rahu"},
            "prana": {"planet": "Ketu"},
        }

    result = HealthTimingHeatmapEngine(
        chart,
        {"planet_health_contexts": conditions, "vulnerabilities": [finding]},
        {},
        dasha_provider=broad_house_chain,
        transit_provider=lambda _day, planet: {"planet": planet, "longitude": 100.0},
    ).calculate(date(2026, 10, 1), 1)

    assert result["days"][0]["details"] == []


def test_named_condition_is_timed_when_its_own_planet_is_in_md_ad_pd():
    blueprint = _blueprint()
    finding = blueprint["vulnerabilities"][0]
    finding["claim_type"] = "named_classical_susceptibility"

    result = HealthTimingHeatmapEngine(
        _chart(),
        blueprint,
        {},
        dasha_provider=_dashas,
        transit_provider=lambda _day, planet: {
            "planet": planet,
            "longitude": 160.0 if planet == "Jupiter" else 17.0,
        },
    ).calculate(date(2026, 9, 1), 1)

    detail = result["days"][0]["details"][0]
    assert detail["condition_timing_gate"] == {
        "requires_direct_md_ad_pd_carrier": True,
        "direct_md_ad_pd_carrier_present": True,
    }


def test_d30_confirms_severity_without_granting_timing_permission():
    blueprint = _blueprint()
    finding = blueprint["vulnerabilities"][0]
    finding["d30_confirmation"] = {
        "status": "pressure_with_protection",
        "pressure_factors": [{"type": "test_pressure", "meaning": "D30 repeats pressure."}],
        "protective_factors": [{"type": "test_support", "meaning": "D30 retains protection."}],
    }
    blueprint["divisional_health_confirmation"] = {
        "D30": {
            "available": True,
            "intervention_markers": [{"type": "test_intervention", "meaning": "D30 confirms intervention."}],
            "pressure_factors": [],
            "protective_factors": [],
        }
    }

    result = HealthTimingHeatmapEngine(
        _chart(), blueprint, {}, dasha_provider=_dashas,
        transit_provider=lambda _day, planet: {
            "planet": planet,
            "longitude": 160.0 if planet in {"Mars", "Jupiter"} else 17.0,
        },
    ).calculate(date(2026, 9, 1), 1)
    detail = result["days"][0]["details"][0]
    assert detail["score_components"]["d30_confirmation"] >= 1
    assert detail["d30_confirmation"]["role"] == "severity_and_manifestation_confirmation_only"

    def no_permission(_day, _birth):
        return {
            "mahadasha": {"planet": "Jupiter"},
            "antardasha": {"planet": "Jupiter"},
            "pratyantardasha": {"planet": "Venus"},
            "sookshma": {"planet": "Mercury"},
            "prana": {"planet": "Mercury"},
        }

    blocked = HealthTimingHeatmapEngine(
        _chart(), blueprint, {}, dasha_provider=no_permission,
        transit_provider=lambda _day, planet: {"planet": planet, "longitude": 160.0},
    ).calculate(date(2026, 9, 1), 1)
    assert blocked["days"][0]["details"] == []


def test_transits_are_sampled_at_native_local_noon_converted_to_utc():
    sampled = []

    def capture(day, planet):
        sampled.append(day)
        return {"planet": planet, "longitude": 17.0}

    HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {"timezone": "Asia/Kolkata"},
        dasha_provider=_dashas, transit_provider=capture,
    ).calculate(date(2026, 9, 1), 1)
    # Four local observation times are converted to UTC. Local noon in India
    # must therefore appear as 06:30 UTC rather than being treated as 12:00 UT.
    assert any(day.hour == 6 and day.minute == 30 for day in sampled)


def test_numeric_utc_offset_is_converted_instead_of_falling_back_to_utc():
    engine = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {"timezone": "UTC+5:30"},
        dasha_provider=_dashas, transit_provider=lambda day, planet: {},
    )
    assert engine._transit_moment(datetime(2026, 9, 1, 12, 0)) == datetime(2026, 9, 1, 6, 30)


def test_explicit_timing_anchors_exclude_corroborating_prose_and_delivery_planets():
    finding = dict(_blueprint()["vulnerabilities"][0])
    finding.update({
        "timing_planets": ["Mercury"],
        "timing_houses": [6],
        "planetary_delivery": [
            {"planet": "Mercury", "house": 6},
            {"planet": "Jupiter", "house": 2},
        ],
        "supporting_rules": [
            "Mercury rules the relevant House 6",
            "Jupiter in House 2 provides independent corroboration",
        ],
    })
    engine = HealthTimingHeatmapEngine(
        _chart(), _blueprint(), {}, dasha_provider=_dashas,
        transit_provider=lambda day, planet: {},
    )
    signature = engine._vulnerability_signature(finding)
    assert signature["planets"] == {"Mercury"}
    assert signature["mechanism_houses"] == {6}


def test_lunar_trigger_dates_keep_one_closest_day_per_pass_and_cap_the_list():
    observations = [
        (date(2026, 9, 1), 1.2),
        (date(2026, 9, 2), 0.2),
        (date(2026, 9, 3), 0.8),
        (date(2026, 9, 10), 0.4),
        (date(2026, 9, 20), 0.1),
        (date(2026, 9, 30), 0.3),
    ]
    assert HealthTimingHeatmapEngine._closest_dates_per_pass(observations) == [
        "2026-09-02", "2026-09-20", "2026-09-30",
    ]


def test_period_grouping_does_not_chain_partial_overlaps_into_one_long_period():
    windows = [
        {"finding_id": "a", "start_date": "2026-09-01", "end_date": "2026-09-10", "activation_level": 2},
        {"finding_id": "b", "start_date": "2026-09-08", "end_date": "2026-09-20", "activation_level": 2},
        {"finding_id": "c", "start_date": "2026-09-18", "end_date": "2026-09-30", "activation_level": 2},
    ]
    groups = HealthTimingHeatmapEngine._group_overlapping_windows(windows)
    assert [(row["start_date"], row["end_date"]) for row in groups] == [
        ("2026-09-01", "2026-09-07"),
        ("2026-09-08", "2026-09-10"),
        ("2026-09-11", "2026-09-17"),
        ("2026-09-18", "2026-09-20"),
        ("2026-09-21", "2026-09-30"),
    ]
    assert [[row["finding_id"] for row in group["windows"]] for group in groups] == [
        ["a"], ["a", "b"], ["b"], ["b", "c"], ["c"],
    ]
    # A long finding must remain visible after its first overlap rather than
    # being consumed by the first card.
    assert sum("b" in [row["finding_id"] for row in group["windows"]] for group in groups) == 3


def test_period_group_prioritizes_chart_specific_concentration_that_overlaps_it():
    generic = {
        "finding_id": "generic",
        "start_date": "2026-09-01",
        "end_date": "2026-10-20",
        "activation_level": 4,
        "evidence_score": 30,
        "key_concentration_phases": [{"start_date": "2026-08-20", "end_date": "2026-08-22"}],
        "key_concentration_basis": "sun",
    }
    knee = {
        "finding_id": "knees",
        "start_date": "2026-09-01",
        "end_date": "2026-10-20",
        "activation_level": 3,
        "evidence_score": 21,
        "key_concentration_phases": [{"start_date": "2026-09-30", "end_date": "2026-10-02"}],
        "key_concentration_basis": "anatomical_specificity_and_sun",
    }
    groups = HealthTimingHeatmapEngine._group_overlapping_windows([generic, knee])
    concentrated = next(row for row in groups if row["start_date"] == "2026-09-30")
    assert concentrated["end_date"] == "2026-10-02"
    assert [row["finding_id"] for row in concentrated["windows"]] == ["knees", "generic"]


def test_single_long_window_is_split_around_its_concentration_phase():
    window = {
        "finding_id": "anorectal",
        "start_date": "2025-12-20",
        "end_date": "2026-01-05",
        "activation_level": 3,
        "evidence_score": 17,
        "key_concentration_phases": [{
            "start_date": "2025-12-28",
            "end_date": "2025-12-30",
            "basis": "active_dasha_chain_exact_contact",
            "bases": ["active_dasha_chain_exact_contact"],
        }],
        "_daily_details": [],
    }

    groups = HealthTimingHeatmapEngine._group_overlapping_windows([window])

    assert [(row["start_date"], row["end_date"]) for row in groups] == [
        ("2025-12-20", "2025-12-27"),
        ("2025-12-28", "2025-12-30"),
        ("2025-12-31", "2026-01-05"),
    ]


def test_period_segment_uses_its_own_refinement_chain_instead_of_global_peak_day():
    early_detail = {
        "heat_level": 3,
        "evidence_score": 24,
        "score_components": {"anatomical_specificity": 2},
        "refinement_dasha_chain": [
            {"level": "sookshma", "planet": "Rahu", "matched": True, "natal_house": 12},
            {"level": "prana", "planet": "Ketu", "matched": True, "natal_house": 6},
        ],
    }
    later_detail = {
        "heat_level": 4,
        "evidence_score": 30,
        "score_components": {"anatomical_specificity": 2},
        "refinement_dasha_chain": [
            {"level": "sookshma", "planet": "Jupiter", "matched": True, "natal_house": 2},
            {"level": "prana", "planet": "Ketu", "matched": True, "natal_house": 6},
        ],
    }
    window = {
        "finding_id": "knees",
        "start_date": "2026-09-01",
        "end_date": "2026-10-31",
        "activation_level": 4,
        "evidence_score": 30,
        "detail": later_detail,
        "_daily_details": [
            {"date": "2026-10-01", "detail": early_detail},
            {"date": "2026-10-24", "detail": later_detail},
        ],
    }

    segment = HealthTimingHeatmapEngine._window_for_segment(
        window, date(2026, 9, 30), date(2026, 10, 2)
    )

    assert segment["representative_date"] == "2026-10-01"
    assert [row["planet"] for row in segment["detail"]["refinement_dasha_chain"]] == [
        "Rahu", "Ketu",
    ]


def test_surgery_finding_is_presented_as_body_system_activation_until_specific_gate_passes():
    blueprint = _blueprint()
    finding = blueprint["vulnerabilities"][0]
    finding["stable_id"] = "health.condition.cardiac_surgery_susceptibility"
    finding["label"] = "Classical heart-surgery indication"
    finding["body_zones"] = ["heart", "chest", "circulation"]

    def contacts(_day, planet):
        return {"planet": planet, "longitude": 160.0 if planet in {"Sun", "Jupiter"} else 17.0}

    result = HealthTimingHeatmapEngine(
        _chart(), blueprint, {}, dasha_provider=_dashas, transit_provider=contacts
    ).calculate(date(2026, 9, 1), 1)
    detail = result["days"][0]["details"][0]
    assert detail["manifestation_scope"] == "body_system_activation"
    assert detail["surgery_gate"] == {
        "required": True,
        "passed": False,
        "short_dasha_mars": False,
        "mars_transit_contact": False,
        "intervention_house_connection": False,
    }
