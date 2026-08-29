from reports.context.health_body_zones import (
    build_priority_body_zones,
    compact_health_body_zone_map,
)


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
    assert all(item["primary_medical_factors"] for item in result["major_vulnerabilities"])
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
    # Mars is unrelated to this chart's sixth-house anatomical chain, so its
    # repetition must not inflate confidence for every named body region.
    assert not any(row["divisional_repetition"] for row in profile["major_vulnerabilities"])


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


def test_named_vulnerabilities_originate_in_the_sixth_house_chain():
    result = build_priority_body_zones(
        _chart(),
        lords_nakshatra={
            "sixth_lord": {
                "planet": "Mercury",
                "nakshatra": {
                    "nakshatra": "Chitra",
                    "lord": "Mars",
                    "pada": 2,
                },
            }
        },
    )

    chain = result["sixth_house_chain"]
    assert chain["sixth_house_sign"] == "Virgo"
    assert chain["sixth_lord"] == "Mercury"
    assert chain["sixth_lord_house"] == 3
    assert chain["sixth_lord_house_zones"] == ["shoulders", "arms", "hands", "lungs"]
    assert chain["sixth_lord_sign"] == "Gemini"
    assert chain["sixth_lord_nakshatra"] == "Chitra"
    assert chain["sixth_lord_nakshatra_zones"] == ["forehead"]
    assert result["major_vulnerabilities"]
    assert all(row["primary_medical_factors"] for row in result["major_vulnerabilities"])
    assert all(row["primary_medical_reasons"] for row in result["major_vulnerabilities"])
    assert all(
        "lord Mercury is in Gemini" in " ".join(row["primary_medical_reasons"])
        or "lord Mercury occupies Chitra" in " ".join(row["primary_medical_reasons"])
        or "sign in House 6 is Virgo" in " ".join(row["primary_medical_reasons"])
        or "lord Mercury is placed in House 3" in " ".join(row["primary_medical_reasons"])
        for row in result["major_vulnerabilities"]
    )


def test_sixth_lord_destination_house_contributes_anatomy_without_diagnosing():
    chart = _chart()
    # Virgo is H6 for Aries rising; Mercury placed in H8 contributes the
    # anorectal/pelvic field as one anatomical factor.
    chart["planets"]["Mercury"] = {"house": 8, "sign": 7}
    result = build_priority_body_zones(chart)

    chain = result["sixth_house_chain"]
    assert chain["sixth_lord_house"] == 8
    assert "anus" in chain["sixth_lord_house_zones"]
    destination_rows = [
        row for row in result["priority_zones"]
        if "sixth_lord_house" in (row.get("primary_medical_factors") or [])
    ]
    assert destination_rows
    assert any("anorectal and pelvic region" == row["zone"] for row in destination_rows)
    assert result["claim_policy"]["diagnosis_allowed"] is False


def test_sixth_lord_in_eighth_house_is_retained_in_major_health_evidence():
    # Scorpio rising: Aries occupies H6 and its lord Mars is placed in H8.
    # Nakshatra/sign/H6 anatomy must not crowd the H8 anorectal/pelvic field
    # out of the evidence sent to Tara.
    houses = [
        {"house": house, "sign": (7 + house - 1) % 12}
        for house in range(1, 13)
    ]
    chart = {
        "houses": houses,
        "planets": {
            "Sun": {"house": 5, "sign": 11},
            "Moon": {"house": 1, "sign": 7},
            "Mars": {"house": 8, "sign": 2},
            "Mercury": {"house": 5, "sign": 11},
            "Jupiter": {"house": 10, "sign": 4},
            "Venus": {"house": 6, "sign": 0},
            "Saturn": {"house": 3, "sign": 9},
            "Rahu": {"house": 4, "sign": 10},
            "Ketu": {"house": 10, "sign": 4},
        },
        "graha_drishti_by_house": {},
    }
    result = build_priority_body_zones(
        chart,
        lords_nakshatra={
            "sixth_lord": {
                "planet": "Mars",
                "nakshatra": {"nakshatra": "Ardra", "lord": "Rahu", "pada": 2},
            }
        },
    )

    major = result["major_vulnerabilities"]
    anorectal = next(
        row for row in major if row["zone"] == "anorectal and pelvic region"
    )
    assert "sixth_lord_house" in anorectal["primary_medical_factors"]
    assert any(
        "House 6 lord Mars is placed in House 8" in reason
        for reason in anorectal["primary_medical_reasons"]
    )
    assert "anus" in anorectal["anatomical_members"]
    assert "rectum" in anorectal["anatomical_members"]
    assert any(
        row["zone"] == "anorectal and pelvic region"
        for row in result["medical_profile"]["major_vulnerabilities"]
    )


def test_unrelated_afflicted_anatomy_can_confirm_but_not_create_a_named_zone():
    result = build_priority_body_zones(
        _chart(),
        lords_nakshatra={
            "sixth_lord": {
                "planet": "Mercury",
                "nakshatra": {"nakshatra": "Chitra", "lord": "Mars", "pada": 2},
            }
        },
    )

    assert all(row["primary_medical_factors"] for row in result["major_vulnerabilities"])


def _cancer_magha_chart():
    # Cancer ascendant: Sagittarius occupies H6; its lord Jupiter occupies Leo
    # in H2 and is in Magha. This is the concrete chart shape reported by the
    # user and must produce three distinct anatomical foundations.
    houses = [
        {"house": house, "sign": (3 + house - 1) % 12}
        for house in range(1, 13)
    ]
    return {
        "houses": houses,
        "planets": {
            "Sun": {"house": 9, "sign": 11},
            "Moon": {"house": 4, "sign": 6},
            "Mars": {"house": 2, "sign": 4},
            "Mercury": {"house": 8, "sign": 10},
            "Jupiter": {"house": 2, "sign": 4},
            "Venus": {"house": 11, "sign": 1},
            "Saturn": {"house": 2, "sign": 4},
            "Rahu": {"house": 2, "sign": 4},
            "Ketu": {"house": 8, "sign": 10},
        },
        "graha_drishti_by_house": {},
    }


def test_sixth_house_foundations_use_canonical_magha_mapping():
    result = build_priority_body_zones(
        _cancer_magha_chart(),
        lords_nakshatra={
            "sixth_lord": {
                "planet": "Jupiter",
                "nakshatra": {"nakshatra": "Magha", "lord": "Ketu", "pada": 3},
            }
        },
    )

    major = result["major_vulnerabilities"]
    assert [row["zone"] for row in major] == ["nose", "heart and upper spine/back", "hips and thighs"]
    assert major[0]["primary_medical_factors"] == ["sixth_lord_nakshatra"]
    assert major[0]["confirmation_factors"] == ["nakshatra_lord_condition"]
    assert set(major[0]["anatomical_members"]) == {"nose"}
    assert major[1]["primary_medical_factors"] == ["sixth_lord_sign"]
    assert major[2]["primary_medical_factors"] == ["sixth_house_sign"]


def test_compact_health_body_zone_map_exposes_chain_limbs_for_the_analysis_page():
    result = build_priority_body_zones(
        _cancer_magha_chart(),
        lords_nakshatra={
            "sixth_lord": {
                "planet": "Jupiter",
                "nakshatra": {"nakshatra": "Magha", "lord": "Ketu", "pada": 3},
            }
        },
    )
    compact = compact_health_body_zone_map(result)

    assert compact["top_zone_names"] == ["nose", "heart and upper spine/back", "hips and thighs"]
    assert [limb["factor"] for limb in compact["chain_limbs"]][:3] == [
        "sixth_house_sign",
        "sixth_lord_sign",
        "sixth_lord_nakshatra",
    ]
    assert compact["chain_limbs"][0]["anchor"] == "Sagittarius"
    assert compact["chain_limbs"][2]["anchor"] == "Magha"
    assert compact["major_vulnerabilities"][0]["primary_medical_reasons"]


def test_all_27_nakshatra_anatomy_mappings_are_available():
    expected = {
        "Ashwini": ["knees"], "Bharani": ["head"], "Krittika": ["waist"],
        "Rohini": ["legs"], "Mrigashira": ["eyes"], "Ardra": ["hair"],
        "Punarvasu": ["fingers"], "Pushya": ["mouth", "face"], "Ashlesha": ["nails"],
        "Magha": ["nose"], "Purva Phalguni": ["private parts"],
        "Uttara Phalguni": ["private parts"], "Hasta": ["hands"], "Chitra": ["forehead"],
        "Swati": ["teeth"], "Vishakha": ["upper limbs"], "Anuradha": ["heart"],
        "Jyeshtha": ["tongue"], "Mula": ["feet"], "Purva Ashadha": ["thighs"],
        "Uttara Ashadha": ["thighs"], "Shravana": ["ears"], "Dhanishta": ["back"],
        "Shatabhisha": ["chin"], "Purva Bhadrapada": ["sides of body"],
        "Uttara Bhadrapada": ["sides of body"], "Revati": ["armpits", "groins"],
    }
    for name, zones in expected.items():
        result = build_priority_body_zones(
            _chart(),
            lords_nakshatra={
                "sixth_lord": {
                    "planet": "Mercury",
                    "nakshatra": {"nakshatra": name, "lord": "Mars", "pada": 1},
                }
            },
        )
        assert result["sixth_house_chain"]["sixth_lord_nakshatra_zones"] == zones


def test_nakshatra_spelling_and_transliteration_variants_use_same_mapping():
    variants = {
        "Mrigasira": ["eyes"],
        "Āśleṣā": ["nails"],
        "Poorva-Ashadha": ["thighs"],
        "Śravaṇa": ["ears"],
        "Satabhishak": ["chin"],
        "Uttara Bhadra": ["sides of body"],
    }
    for name, expected in variants.items():
        result = build_priority_body_zones(
            _chart(),
            lords_nakshatra={
                "sixth_lord": {
                    "planet": "Mercury",
                    "nakshatra": {"nakshatra": name, "lord": "Mars", "pada": 1},
                }
            },
        )
        assert result["sixth_house_chain"]["sixth_lord_nakshatra_zones"] == expected


def test_moon_ketu_is_exposed_as_responsible_susceptibility_not_diagnosis():
    chart = _chart()
    chart["planets"]["Moon"] = {"house": 8, "sign": 7}
    chart["planets"]["Ketu"] = {"house": 8, "sign": 7}
    result = build_priority_body_zones(chart, requested_category="mental_wellbeing")
    signals = result["medical_profile"]["condition_susceptibilities"]
    mental = next(row for row in signals if row["key"] == "mental_emotional_regulation_susceptibility")
    assert mental["diagnosis"] is False
    assert any("Moon shares House 8 with Ketu" in line for line in mental["evidence"])
    assert "sharing a house" in mental["interpretation"]
    assert "professional assessment" in mental["responsible_guidance"]


def test_ketu_aspect_to_moon_is_not_mislabeled_as_nodal_axis_or_conjunction():
    chart = _cancer_magha_chart()
    chart["graha_drishti_by_house"] = {
        4: [{"planet": "Saturn"}, {"planet": "Ketu"}],
        5: [{"planet": "Mars"}],
    }

    result = build_priority_body_zones(chart, requested_category="mental_wellbeing")
    signals = result["medical_profile"]["condition_susceptibilities"]
    mental = next(row for row in signals if row["key"] == "mental_emotional_regulation_susceptibility")

    assert "Moon receives pressure from Saturn, Ketu" in mental["evidence"]
    assert "Ketu's calculated aspect to the Moon" in mental["interpretation"]
    assert "Moon is not conjunct Ketu or on the nodal axis" in mental["interpretation"]
    assert "Moon-Ketu/mental-axis" not in mental["interpretation"]


def test_bp_signal_requires_convergence_and_recommends_checking_not_diagnosis():
    chart = _chart()
    chart["planets"]["Sun"] = {"house": 5, "sign": 4}
    chart["planets"]["Mars"] = {"house": 5, "sign": 4}
    chart["planets"]["Saturn"] = {"house": 5, "sign": 4}
    result = build_priority_body_zones(chart)
    signals = result["medical_profile"]["condition_susceptibilities"]
    vascular = next(row for row in signals if row["key"] == "vascular_pressure_tone")
    assert vascular["risk_level"] == "elevated"
    assert vascular["diagnosis"] is False
    assert "does not establish hypertension" in vascular["responsible_guidance"]
    assert "routine BP checks" in vascular["responsible_guidance"]


def test_metabolic_signal_requires_independent_factors_and_names_screening():
    chart = _chart()
    chart["planets"]["Jupiter"] = {"house": 2, "sign": 1}
    chart["planets"]["Rahu"] = {"house": 2, "sign": 1}
    chart["planets"]["Venus"] = {"house": 6, "sign": 5}
    result = build_priority_body_zones(chart)
    signals = result["medical_profile"]["condition_susceptibilities"]
    metabolic = next(
        row for row in signals if row["key"] == "metabolic_blood_sugar_susceptibility"
    )
    assert metabolic["risk_level"] == "elevated"
    assert metabolic["diagnosis"] is False
    assert "does not establish diabetes" in metabolic["interpretation"]
    assert "glucose/HbA1c screening" in metabolic["responsible_guidance"]
