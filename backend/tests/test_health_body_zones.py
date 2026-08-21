from reports.context.health_body_zones import build_priority_body_zones


def _chart(*, mars_house=6):
    # Aries rising, using the same zero-based sign representation as the
    # production chart payload.  Mars in the disease house supplies an acute
    # event-pattern layer in addition to house/sign anatomy.
    return {
        "houses": [{"house": house, "sign": house - 1} for house in range(1, 13)],
        "planets": {
            "Sun": {"house": 1, "sign": 0},
            "Moon": {"house": 4, "sign": 3},
            "Mars": {"house": mars_house, "sign": mars_house - 1},
            "Mercury": {"house": 3, "sign": 2},
            "Jupiter": {"house": 9, "sign": 8},
            "Venus": {"house": 7, "sign": 6},
            "Saturn": {"house": 10, "sign": 9},
            "Rahu": {"house": 11, "sign": 10},
            "Ketu": {"house": 5, "sign": 4},
        },
        "graha_drishti_by_house": {},
    }


def test_major_health_vulnerability_requires_natal_confluence():
    result = build_priority_body_zones(_chart())

    assert result["claim_policy"]["diagnosis_allowed"] is False
    assert result["major_vulnerabilities"]
    assert all(item["confluence_count"] >= 2 for item in result["major_vulnerabilities"])
    assert all(item["standing_weight"] >= 8 for item in result["major_vulnerabilities"])


def test_dasha_activation_does_not_create_a_constitutional_vulnerability():
    chart = _chart(mars_house=3)
    without_dasha = build_priority_body_zones(chart)
    with_dasha = build_priority_body_zones(
        chart,
        current_dashas={"mahadasha": {"planet": "Mars"}},
    )

    before = {
        item["zone"] for item in without_dasha["priority_zones"]
        if item.get("callout_allowed")
    }
    after = {item["zone"] for item in with_dasha["major_vulnerabilities"]}
    # Dasha may re-rank an already established natal susceptibility, but it
    # must not make a new one eligible for a named body-part claim.
    assert after <= before


def _division_with_mars_in(house):
    planets = {
        name: {"house": (house if name == "Mars" else row["house"]), "sign": row["sign"]}
        for name, row in _chart()["planets"].items()
    }
    return {"divisional_chart": {"planets": planets}}


def test_medical_profile_uses_d1_constitution_and_all_health_divisions():
    result = build_priority_body_zones(
        _chart(),
        divisional_charts={
            code: _division_with_mars_in(6)
            for code in ("D3", "D6", "D8", "D30")
        },
        planet_conditions={
            "Mars": {
                "dignity": "own_sign",
                "functional_nature": "yogakaraka",
                "combustion_status": "not_combust",
            }
        },
    )

    profile = result["medical_profile"]
    assert profile["constitution"]["ascendant_sign"] == "Aries"
    assert profile["constitution"]["ascendant_lord"] == "Mars"
    assert {row["house"] for row in profile["constitution"]["core_houses"]} == {1, 6, 8, 12}
    assert set(profile["divisional_health_charts"]) == {"D3", "D6", "D8", "D30"}
    assert any(row["planet"] == "Mars" and row["dignity"] == "own_sign" for row in profile["planet_conditions"])
    assert any(row["divisional_repetition"] for row in profile["major_vulnerabilities"])


def test_divisional_charts_confirm_but_do_not_create_health_vulnerability():
    base = build_priority_body_zones(_chart(mars_house=3))
    with_divisions = build_priority_body_zones(
        _chart(mars_house=3),
        divisional_charts={
            code: _division_with_mars_in(6)
            for code in ("D3", "D6", "D8", "D30")
        },
    )

    assert {row["zone"] for row in with_divisions["major_vulnerabilities"]} == {
        row["zone"] for row in base["major_vulnerabilities"]
    }


def test_current_health_judgment_names_only_activated_natal_vulnerabilities():
    result = build_priority_body_zones(
        _chart(),
        current_dashas={"mahadasha": {"planet": "Mars"}},
        requested_category="current",
    )

    current = result["medical_profile"]["judgments"]["current"]
    assert current["active"] is True
    assert current["activated_vulnerabilities"]
    assert all(row["activation_sources"] for row in current["activated_vulnerabilities"])


def test_surgery_accident_and_recovery_are_separate_judgments():
    result = build_priority_body_zones(
        _chart(),
        planet_conditions={"Mars": {"dignity": "own_sign"}},
        requested_category="surgery",
    )

    judgments = result["medical_profile"]["judgments"]
    assert judgments["surgery"]["supported"] is True
    assert judgments["accident"]["supported"] is False
    assert judgments["recovery"]["supported"] is True
