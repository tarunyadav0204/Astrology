from datetime import date, datetime

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
    assert result["period_groups"] == [{
        "group_id": "2026-09-01:health.anatomy.digestion",
        "start_date": "2026-09-01",
        "end_date": "2026-09-03",
        "activation_level": window["activation_level"],
        "windows": [window],
        "finding_count": 1,
    }]


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
    assert len(groups) == 2
    assert [row["finding_id"] for row in groups[0]["windows"]] == ["a", "b"]
    assert [row["finding_id"] for row in groups[1]["windows"]] == ["c"]


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
