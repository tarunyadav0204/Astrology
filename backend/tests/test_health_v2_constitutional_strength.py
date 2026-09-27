from __future__ import annotations

from health_v2.constitutional_strength_engine import ConstitutionalStrengthEngine


def _chart(asc_sign=0):
    placements = {
        "Sun": (5, 4, 132.0), "Moon": (4, 3, 102.0), "Mars": (1, 0, 5.0),
        "Mercury": (6, 5, 170.0), "Jupiter": (9, 8, 250.0), "Venus": (7, 6, 200.0),
        "Saturn": (10, 9, 285.0), "Rahu": (11, 10, 315.0), "Ketu": (5, 4, 135.0),
    }
    return {
        "ascendant": asc_sign * 30 + 5.0,
        "houses": [{"house": h, "sign": (asc_sign + h - 1) % 12} for h in range(1, 13)],
        "planets": {
            planet: {"house": house, "sign": sign, "longitude": longitude, "degree": longitude % 30}
            for planet, (house, sign, longitude) in placements.items()
        },
    }


def test_functional_nature_preserves_mixed_lordship_instead_of_binary_lookup():
    # Gemini Lagna: Saturn owns H8 and H9 and must remain mixed.
    chart = _chart(2)
    result = ConstitutionalStrengthEngine(chart).calculate()
    saturn = result["planet_conditions"]["Saturn"]["functional_role"]
    assert saturn["ruled_houses"] == [8, 9]
    assert saturn["classification"] == "mixed"


def test_mixed_lordship_contributes_both_support_and_pressure_to_a_pillar():
    chart = _chart(2)
    # Saturn (H8/H9 lord for Gemini) occupies the first pillar.
    chart["planets"]["Saturn"].update(house=1)
    pillar = ConstitutionalStrengthEngine(chart).calculate()["kendra_pillars"][0]
    assert any("mixed lordship includes support" in item for item in pillar["support"])
    assert any("mixed lordship includes pressure" in item for item in pillar["pressure"])


def test_second_and_seventh_lordship_is_vitality_sensitive_not_neutral_or_fatalistic():
    chart = _chart(0)
    venus = ConstitutionalStrengthEngine(chart).calculate()["planet_conditions"]["Venus"]["functional_role"]
    assert venus["ruled_houses"] == [2, 7]
    assert venus["classification"] == "vitality_sensitive"


def test_yogakaraka_is_derived_from_kendra_and_trikona_ownership():
    # Taurus Lagna: Saturn owns H9 and H10.
    chart = _chart(1)
    result = ConstitutionalStrengthEngine(chart).calculate()
    saturn = result["planet_conditions"]["Saturn"]["functional_role"]
    assert saturn["is_yogakaraka"] is True
    assert saturn["classification"] == "yogakaraka"


def test_dignity_measures_capacity_without_changing_functional_agenda():
    chart = _chart(2)
    chart["planets"]["Saturn"].update(sign=6, longitude=200.0, degree=20.0)
    result = ConstitutionalStrengthEngine(chart).calculate()
    saturn = result["planet_conditions"]["Saturn"]
    assert saturn["dignity"] == "exalted"
    assert saturn["functional_role"]["classification"] == "mixed"


def test_moon_and_mercury_split_exaltation_from_moolatrikona_by_degree():
    chart = _chart()
    chart["planets"]["Moon"].update(sign=1, longitude=32.0, degree=2.0)
    chart["planets"]["Mercury"].update(sign=5, longitude=167.0, degree=17.0)
    conditions = ConstitutionalStrengthEngine(chart).calculate()["planet_conditions"]
    assert conditions["Moon"]["dignity"] == "exalted"
    assert conditions["Mercury"]["dignity"] == "moolatrikona"


def test_vargottama_is_reported_without_automatic_positive_label():
    chart = _chart(0)
    d9 = _chart(0)
    d9["planets"]["Saturn"]["sign"] = chart["planets"]["Saturn"]["sign"]
    result = ConstitutionalStrengthEngine(chart, {"D9": d9}).calculate()
    saturn = result["planet_conditions"]["Saturn"]
    assert saturn["vargottama_d1_d9"] is True
    assert "positive" not in str(saturn).lower()


def test_vargottama_vitality_anchor_is_visible_as_capacity_support_without_erasing_pressure():
    chart = _chart(3)
    chart["planets"]["Moon"].update(house=4, sign=6, longitude=190.0, degree=10.0)
    chart["planets"]["Saturn"].update(house=2, sign=4, longitude=130.0, degree=10.0)
    d9 = _chart(3)
    d9["planets"]["Moon"].update(sign=6, longitude=190.0, degree=10.0)
    moon = next(
        row for row in ConstitutionalStrengthEngine(chart, {"D9": d9}).calculate()["vitality_anchors"]
        if row["role"] == "lagna_lord"
    )
    assert {"type": "vargottama_d1_d9"} in moon["strengthening_factors"]
    assert moon["affliction_details"]


def test_retrograde_is_not_converted_to_a_weakness_multiplier():
    chart = _chart()
    chart["planets"]["Saturn"]["retrograde"] = True
    saturn = ConstitutionalStrengthEngine(chart).calculate()["planet_conditions"]["Saturn"]
    assert saturn["retrograde"] is True
    assert saturn["retrograde_interpretation"] == "intensified_or_non_linear"
    assert "multiplier" not in saturn


def test_combustion_uses_angular_distance_and_stays_separate_from_dignity():
    chart = _chart()
    chart["planets"]["Sun"].update(longitude=100.0, sign=3, degree=10.0)
    chart["planets"]["Mercury"].update(longitude=108.0, sign=3, degree=18.0)
    mercury = ConstitutionalStrengthEngine(chart).calculate()["planet_conditions"]["Mercury"]
    assert mercury["combustion"]["is_combust"] is True
    assert mercury["combustion"]["distance_from_sun"] == 8.0
    assert mercury["dignity"] == "ordinary"


def test_friendly_and_inimical_sign_relationships_are_preserved_separately_from_dignity():
    chart = _chart(3)
    chart["planets"]["Sun"].update(house=9, sign=11, longitude=350.0, degree=20.0)
    chart["planets"]["Mercury"].update(house=1, sign=3, longitude=100.0, degree=10.0)
    conditions = ConstitutionalStrengthEngine(chart).calculate()["planet_conditions"]
    assert conditions["Sun"]["dignity"] == "ordinary"
    assert conditions["Sun"]["sign_relationship"] == {"status": "friendly", "dispositor": "Jupiter", "sign": 11}
    assert conditions["Mercury"]["sign_relationship"]["status"] == "inimical"
    assert {"type": "inimical_sign", "dispositor": "Moon"} in conditions["Mercury"]["affliction_details"]


def test_nakshatra_lord_relationship_qualifies_vitality_delivery_without_transferring_afflictions():
    chart = _chart(3)
    # 2° Pisces is Purva Bhadrapada, ruled by Jupiter, a natural friend of Sun.
    chart["planets"]["Sun"].update(house=9, sign=11, longitude=332.0, degree=2.0)
    chart["planets"]["Jupiter"].update(house=2, sign=4, longitude=128.0, degree=8.0)
    chart["planets"]["Saturn"].update(house=2, sign=4, longitude=130.0, degree=10.0)
    sun = next(
        row for row in ConstitutionalStrengthEngine(chart).calculate()["vitality_anchors"]
        if row["role"] == "sun"
    )
    context = sun["nakshatra_context"]
    assert context["nakshatra"] == "Purva Bhadrapada"
    assert context["lord"] == "Jupiter"
    assert context["relationship"] == "friendly"
    assert context["lord_affliction_details"]
    factor = next(row for row in sun["strengthening_factors"] if row["type"] == "nakshatra_lord_support")
    assert factor["lord"] == "Jupiter"
    # Saturn pressures Jupiter, but it must not become a direct Sun affliction.
    assert not any(
        detail.get("type") == "joined_by_malefics" and "Saturn" in detail.get("planets", [])
        for detail in sun["affliction_details"]
    )


def test_node_ruled_nakshatra_is_preserved_without_disputed_friendship_grade():
    chart = _chart()
    # 12° Leo is Magha, ruled by Ketu.
    chart["planets"]["Sun"].update(house=5, sign=4, longitude=132.0, degree=12.0)
    sun = ConstitutionalStrengthEngine(chart).calculate()["planet_conditions"]["Sun"]
    assert sun["nakshatra_context"]["nakshatra"] == "Magha"
    assert sun["nakshatra_context"]["lord"] == "Ketu"
    assert sun["nakshatra_context"]["relationship"] == "ungraded"


def test_waning_moon_pressure_is_explained_by_phase_instead_of_opaque_malefic_label():
    chart = _chart(3)
    chart["planets"]["Sun"].update(longitude=332.0, sign=11, degree=2.0)
    chart["planets"]["Moon"].update(house=4, longitude=190.0, sign=6, degree=10.0)
    result = ConstitutionalStrengthEngine(chart).calculate()
    moon = result["planet_conditions"]["Moon"]
    assert moon["natural_nature_context"]["basis"] == "waning_or_dark_moon"
    moon_anchor = next(row for row in result["vitality_anchors"] if row["role"] == "lagna_lord")
    assert {"type": "waning_moon"} in moon_anchor["affliction_details"]
    pillar = next(row for row in result["kendra_pillars"] if row["house"] == 4)
    assert any(row["type"] == "waning_moon" and row["planet"] == "Moon" for row in pillar["pressure_details"])


def test_waxing_moon_is_visible_as_a_vitality_strengthening_factor():
    chart = _chart(3)
    chart["planets"]["Sun"].update(longitude=100.0, sign=3, degree=10.0)
    chart["planets"]["Moon"].update(house=4, longitude=190.0, sign=6, degree=10.0)
    result = ConstitutionalStrengthEngine(chart).calculate()
    moon = next(row for row in result["vitality_anchors"] if row["role"] == "lagna_lord")
    assert {"type": "waxing_moon"} in moon["strengthening_factors"]
    assert {"type": "waning_moon"} not in moon["affliction_details"]


def test_rahu_ketu_special_aspects_are_not_used_as_universal_health_pressure():
    chart = _chart(3)
    chart["planets"]["Moon"].update(house=4, sign=6, longitude=190.0, degree=10.0)
    chart["graha_drishti_by_house"] = {
        4: [{"planet": "Saturn"}, {"planet": "Rahu"}, {"planet": "Ketu"}],
    }
    moon = next(
        row for row in ConstitutionalStrengthEngine(chart).calculate()["vitality_anchors"]
        if row["role"] == "lagna_lord"
    )
    aspect = next(row for row in moon["affliction_details"] if row["type"] == "aspected_by_malefics")
    assert aspect["planets"] == ["Saturn"]


def test_debilitation_keeps_cancellation_factors_visible_without_silently_erasing_it():
    chart = _chart(0)
    chart["planets"]["Saturn"].update(house=1, sign=0, longitude=5.0, degree=5.0)
    # Mars disposits Aries and occupies a Kendra from Lagna.
    chart["planets"]["Mars"].update(house=4, sign=3, longitude=95.0, degree=5.0)
    saturn = ConstitutionalStrengthEngine(chart).calculate()["planet_conditions"]["Saturn"]
    assert saturn["dignity"] == "debilitated"
    assert any("dispositor Mars" in item for item in saturn["neecha_bhanga_factors"])


def test_d3_d9_d12_confirmations_are_all_preserved():
    chart = _chart()
    divisions = {name: _chart() for name in ("D3", "D9", "D12")}
    sun = ConstitutionalStrengthEngine(chart, divisions).calculate()["planet_conditions"]["Sun"]
    assert set(sun["divisional_confirmation"]) == {"D3", "D9", "D12"}


def test_jupiter_keeps_residual_protection_when_afflicted_and_separates_expansion():
    chart = _chart()
    chart["planets"]["Jupiter"].update(house=1, sign=8, longitude=250.0)
    chart["planets"]["Saturn"].update(house=1, sign=8, longitude=255.0)
    result = ConstitutionalStrengthEngine(chart).calculate()
    jupiter = result["jupiter_protection"]
    assert jupiter["quality"] == "qualified_but_present"
    assert jupiter["conclusion_key"] == "qualified_but_present"
    assert {"house": 1, "mode": "occupation", "health_focus_key": "h1", "roles": ["constitutional_pillar"]} in jupiter["reach_details"]
    assert any(row["type"] == "natural_benefic" for row in jupiter["support_factors"])
    assert any(row["type"] == "joined_by_malefics" for row in jupiter["pressure_factors"])
    assert jupiter["first_house_expansion_tendency"] is True
    assert "requires separate metabolic corroboration" in jupiter["first_house_note"]


def test_jupiter_judgment_includes_occupied_house_and_mixed_lordship_on_every_card():
    # Leo Lagna: Jupiter owns the supportive H5 and difficult H8.  Its
    # occupation of H2 must be visible even though H2 is neither a Kendra nor
    # necessarily occupied by the Sun or Moon.
    chart = _chart(4)
    chart["planets"]["Jupiter"].update(house=2, sign=5, longitude=160.0, degree=10.0)
    jupiter = ConstitutionalStrengthEngine(chart).calculate()["jupiter_protection"]
    occupied = next(row for row in jupiter["reach_details"] if row["house"] == 2)
    assert occupied["mode"] == "occupation"
    assert occupied["health_focus_key"] == "h2"
    assert jupiter["quality"] == "qualified_but_present"
    assert any(row["type"] == "mixed_lordship_support" and row["houses"] == [5] for row in jupiter["support_factors"])
    assert any(row["type"] == "mixed_lordship_pressure" and row["houses"] == [8] for row in jupiter["pressure_factors"])
    assert jupiter["judgment_scope"] == "modifies_severity_and_recovery_without_cancelling_vulnerability"


def test_jupiter_quality_uses_secondary_pressure_modifiers_instead_of_ignoring_them():
    chart = _chart()
    # Shukla Dwitiya burns Sagittarius in the selected named table. Jupiter is
    # otherwise in its own Sagittarius, so this proves the tithi modifier is
    # included in the final protection judgment rather than merely displayed.
    chart["planets"]["Sun"].update(longitude=0.0, sign=0, degree=0.0)
    chart["planets"]["Moon"].update(longitude=13.0, sign=0, degree=13.0)
    jupiter = ConstitutionalStrengthEngine(chart).calculate()["jupiter_protection"]
    assert any(row["type"] == "tithi_dagdha" for row in jupiter["pressure_factors"])
    assert jupiter["quality"] == "qualified_but_present"


def test_corrected_yogi_uses_93_20_arc_and_nakshatra_lord():
    chart = _chart()
    chart["planets"]["Sun"]["longitude"] = 10.0
    chart["planets"]["Moon"]["longitude"] = 20.0
    result = ConstitutionalStrengthEngine(chart).calculate()
    special = result["special_lunar_factors"]
    assert round(special["yogi_point"], 6) == round(123 + 20 / 60, 6)
    assert special["yogi_nakshatra_lord"] == "Ketu"
    assert round(special["avayogi_point"], 6) == 190.0
    assert "yogi_lord" in result["planet_conditions"]["Ketu"]["special_roles"]
    assert "avayogi_lord" in result["planet_conditions"][special["avayogi_nakshatra_lord"]]["special_roles"]
    assert any(
        factor["type"] == "yogi_support"
        for factor in result["planet_conditions"]["Ketu"]["finding_modifiers"]["support"]
    )
    avayogi = result["planet_conditions"][special["avayogi_nakshatra_lord"]]
    avayogi_factor_types = {
        factor["type"]
        for group in ("support", "pressure")
        for factor in avayogi["finding_modifiers"][group]
    }
    assert avayogi_factor_types & {"reversed_avayogi_support", "avayogi_pressure"}


def test_tithi_shunya_and_dagdha_are_one_secondary_modifier_not_two_penalties():
    chart = _chart()
    chart["planets"]["Sun"]["longitude"] = 0.0
    chart["planets"]["Moon"]["longitude"] = 1.0
    special = ConstitutionalStrengthEngine(chart).calculate()["special_lunar_factors"]
    assert special["paksha_tithi_number"] == 1
    assert special["tithi_dagdha_signs"] == [6, 9]
    assert special["interpretation_scope"] == "secondary_modifier_only"
    assert "dagdha_rashi" not in special
    result = ConstitutionalStrengthEngine(chart).calculate()
    for planet in special["affected_planets"]:
        assert any(
            factor["type"] == "tithi_dagdha"
            for factor in result["planet_conditions"][planet]["finding_modifiers"]["pressure"]
        )


def test_four_kendra_pillars_preserve_support_and_pressure_separately():
    result = ConstitutionalStrengthEngine(_chart()).calculate()
    assert [row["house"] for row in result["kendra_pillars"]] == [1, 4, 7, 10]
    assert all(set(row) == {"house", "status", "support", "pressure", "support_details", "pressure_details"} for row in result["kendra_pillars"])
    assert "overall_health_score" not in result
    assert result["overall_resilience"]["status"] in {
        "strongly_protected", "supported", "mixed", "constitution_under_pressure"
    }


def test_lagna_lord_sun_and_moon_are_explicit_vitality_anchors():
    result = ConstitutionalStrengthEngine(_chart()).calculate()
    anchors = result["vitality_anchors"]
    assert [row["role"] for row in anchors] == ["lagna_lord", "sun", "moon"]
    assert anchors[0]["planet"] == "Mars"
    assert all(row["status"] in {"strong", "supported", "mixed", "qualified", "pressured"} for row in anchors)
    assert "vitality_anchor_support" in result["overall_resilience"]


def test_luminary_lagna_lord_is_not_counted_twice_as_independent_support():
    chart = _chart()
    # Cancer ascendant makes Moon both Lagna lord and the lunar vitality anchor.
    chart["ascendant"] = 90.0
    for index, house in enumerate(chart["houses"]):
        house["sign"] = (3 + index) % 12
    result = ConstitutionalStrengthEngine(chart).calculate()
    resilience = result["overall_resilience"]
    assert len(result["vitality_anchors"]) == 3
    assert resilience["unique_vitality_anchors"] == 2
    assert resilience["vitality_anchor_support"] <= 2
    assert resilience["vitality_anchor_qualified"] <= 2


def test_vitality_anchors_explain_exact_strengthening_and_weakening_factors():
    chart = _chart(3)
    chart["planets"]["Moon"].update(house=4, sign=6, longitude=190.0, degree=10.0)
    chart["planets"]["Sun"].update(house=9, sign=11, longitude=350.0, degree=20.0)
    chart["planets"]["Mars"].update(house=2, sign=4, longitude=125.0, degree=5.0)
    chart["planets"]["Jupiter"].update(house=2, sign=4, longitude=128.0, degree=8.0, retrograde=True)
    chart["planets"]["Saturn"].update(house=2, sign=4, longitude=130.0, degree=10.0)
    chart["planets"]["Rahu"].update(house=2, sign=4, longitude=132.0, degree=12.0)

    anchors = ConstitutionalStrengthEngine(chart).calculate()["vitality_anchors"]
    moon = next(row for row in anchors if row["role"] == "lagna_lord")
    sun = next(row for row in anchors if row["role"] == "sun")

    assert moon["status"] == "mixed"
    assert moon["sign_name"] == "Libra"
    assert moon["sign_relationship"] == {"status": "neutral", "dispositor": "Venus", "sign": 6}
    assert moon["neutral_factors"][0] == {
        "type": "neutral_sign_relationship", "sign_name": "Libra", "dispositor": "Venus"
    }
    assert moon["strengthening_factors"] == [{"type": "supportive_house_placement", "house": 4, "group": "kendra"}]
    assert moon["affliction_details"] == [
        {"type": "aspected_by_malefics", "planets": ["Saturn"]},
        {"type": "waning_moon"},
    ]
    assert sun["status"] == "mixed"
    assert sun["strengthening_factors"][0] == {"type": "supportive_house_placement", "house": 9, "group": "trikona"}
    assert sun["strengthening_factors"][1] == {"type": "friendly_sign", "dispositor": "Jupiter"}
    exchange = sun["strengthening_factors"][2]
    assert exchange["type"] == "mutual_sign_exchange"
    assert exchange["planet"] == "Jupiter"
    assert exchange["houses"] == [2, 9]
    assert exchange["partner_other_ruled_houses"] == [6]
    assert exchange["partner_retrograde"] is True
    assert exchange["partner_affliction_details"] == [{
        "type": "joined_by_malefics",
        "planets": ["Mars", "Saturn", "Rahu"],
    }]
    assert sun["affliction_details"] == [{"type": "aspected_by_malefics", "planets": ["Mars"]}]


def test_exchange_partner_pressure_qualifies_support_without_becoming_direct_affliction():
    chart = _chart(3)
    chart["planets"]["Sun"].update(house=9, sign=11, longitude=350.0, degree=20.0)
    chart["planets"]["Jupiter"].update(house=2, sign=4, longitude=128.0, degree=8.0, retrograde=True)
    chart["planets"]["Mars"].update(house=2, sign=4, longitude=125.0, degree=5.0)
    chart["planets"]["Saturn"].update(house=2, sign=4, longitude=130.0, degree=10.0)
    chart["planets"]["Rahu"].update(house=2, sign=4, longitude=132.0, degree=12.0)

    sun = next(
        row for row in ConstitutionalStrengthEngine(chart).calculate()["vitality_anchors"]
        if row["role"] == "sun"
    )

    assert sun["affliction_details"] == [{"type": "aspected_by_malefics", "planets": ["Mars"]}]
    exchange = next(row for row in sun["strengthening_factors"] if row["type"] == "mutual_sign_exchange")
    assert exchange["partner_affliction_details"][0]["planets"] == ["Mars", "Saturn", "Rahu"]
