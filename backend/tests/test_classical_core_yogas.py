from backend.calculators.yoga_calculator import YogaCalculator
from backend.calculators.classical_core_yogas import _nature, viparita_yogas


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def chart(placements, asc_sign=0):
    houses = [{"house": house, "sign": (asc_sign + house - 1) % 12} for house in range(1, 13)]
    planets = {}
    for index, planet in enumerate(PLANETS):
        house = placements.get(planet, (index % 12) + 1)
        sign = houses[house - 1]["sign"]
        degree = 5.0 + index
        planets[planet] = {
            "house": house,
            "sign": sign,
            "degree": degree,
            "longitude": sign * 30.0 + degree,
            "retrograde": False,
        }
    return {"ascendant": asc_sign * 30.0, "houses": houses, "planets": planets}


def names(rows):
    return {row["name"] for row in rows}


def test_contextual_planet_nature_has_no_missing_phase_fallback():
    value = chart({
        "Sun": 1, "Moon": 2, "Mercury": 3, "Mars": 4,
        "Jupiter": 5, "Venus": 6, "Saturn": 7,
    })
    value["planets"]["Sun"]["longitude"] = 10.0
    value["planets"]["Moon"]["longitude"] = 100.0
    benefics, malefics, context = _nature(value)
    assert "Moon" in benefics and "Moon" not in malefics
    assert context["waxing_moon"] is True

    value["planets"]["Moon"]["longitude"] = 300.0
    benefics, malefics, context = _nature(value)
    assert "Moon" in malefics and "Moon" not in benefics
    assert context["waxing_moon"] is False

    del value["planets"]["Moon"]["longitude"]
    benefics, malefics, context = _nature(value)
    assert "Moon" not in benefics | malefics
    assert context["waxing_moon"] is None


def test_gaja_kesari_rejects_old_house_sum_false_positive():
    value = chart({
        "Moon": 1, "Jupiter": 12, "Venus": 12,
        "Sun": 2, "Mars": 3, "Mercury": 5, "Saturn": 8,
    })
    assert YogaCalculator(None, value).calculate_gaja_kesari_yoga() == []


def test_gaja_kesari_requires_and_reports_all_bphs_qualifiers():
    value = chart({
        "Moon": 1, "Jupiter": 4, "Venus": 4,
        "Sun": 2, "Mars": 3, "Mercury": 5, "Saturn": 8,
    })
    result = YogaCalculator(None, value).calculate_gaja_kesari_yoga()
    assert names(result) == {"Gaja Kesari Yoga"}
    assert result[0]["strength"] is None
    assert result[0]["source"]["reference_label"] == "BPHS 36.3–4"
    assert len(result[0]["classical_conditions"]) == 3
    assert result[0]["selected_reading"] == "Strict BPHS 36.3"
    assert "alone is insufficient" in result[0]["textual_note"]

    debilitated = chart({
        "Moon": 7, "Jupiter": 10, "Venus": 10,
        "Sun": 2, "Mars": 3, "Mercury": 5, "Saturn": 8,
    })
    assert YogaCalculator(None, debilitated).calculate_gaja_kesari_yoga() == []


def test_pancha_mahapurusha_uses_only_kendra_and_own_or_exaltation():
    value = chart({
        "Mars": 10,  # Capricorn: exaltation
        "Sun": 2, "Moon": 3, "Mercury": 5, "Jupiter": 6, "Venus": 8, "Saturn": 9,
    })
    result = YogaCalculator(None, value).calculate_panch_mahapurusha_yogas()
    assert "Ruchaka Yoga" in names(result)
    assert all(row["strength"] is None for row in result)

    value["planets"]["Mars"].update({"house": 9, "sign": 8, "longitude": 245.0})
    assert "Ruchaka Yoga" not in names(YogaCalculator(None, value).calculate_panch_mahapurusha_yogas())


def test_kemadruma_uses_lagna_kendra_cancellation_in_selected_bphs_reading():
    placements = {
        "Moon": 2, "Sun": 6, "Mars": 5, "Mercury": 6,
        "Jupiter": 8, "Venus": 9, "Saturn": 11,
    }
    value = chart(placements)
    assert "Kemadruma Yoga" in names(YogaCalculator(None, value).calculate_chandra_yogas())

    value = chart({**placements, "Mars": 4})
    assert "Kemadruma Yoga" not in names(YogaCalculator(None, value).calculate_chandra_yogas())

    value = chart({**placements, "Sun": 4})
    assert "Kemadruma Yoga" not in names(YogaCalculator(None, value).calculate_chandra_yogas())

    value = chart(placements)
    value["planets"]["Rahu"] = {"house": 7, "sign": 6, "longitude": 195.0}
    assert "Kemadruma Yoga" not in names(YogaCalculator(None, value).calculate_chandra_yogas())


def test_single_planet_kendra_trikona_yogakaraka_is_not_omitted():
    # Cancer Lagna: Mars owns Houses 5 and 10.  Place it in House 5.
    value = chart({
        "Mars": 5, "Sun": 2, "Moon": 3, "Mercury": 6,
        "Jupiter": 8, "Venus": 9, "Saturn": 11,
    }, asc_sign=3)
    result = YogaCalculator(None, value).calculate_raj_yogas()
    assert any(row["planets"] == ["Mars"] and row["kendra_house"] == 10 and row["trikona_house"] == 5 for row in result)


def test_raja_yoga_applies_bphs_dual_dusthana_lord_exclusion():
    # Aries Lagna: Mars owns 1 and 8; Jupiter owns 9 and 12. Their conjunction
    # would otherwise connect a Kendra/Trikona pair, but both also own a
    # difficult house, which BPHS 34.15 excludes.
    value = chart({
        "Mars": 2, "Jupiter": 2, "Sun": 3, "Moon": 4,
        "Mercury": 5, "Venus": 7, "Saturn": 10,
    })
    result = YogaCalculator(None, value).calculate_raj_yogas()
    assert not any(set(row["planets"]) == {"Mars", "Jupiter"} for row in result)


def test_amala_enforces_exclusive_benefic_occupancy():
    clean = chart({
        "Jupiter": 10, "Sun": 2, "Moon": 3, "Mars": 6,
        "Mercury": 5, "Venus": 8, "Saturn": 9,
    })
    assert "Amala Yoga" in names(YogaCalculator(None, clean).calculate_amala_yoga())

    mixed = chart({
        "Jupiter": 10, "Mars": 10, "Sun": 2, "Moon": 3,
        "Mercury": 5, "Venus": 8, "Saturn": 9,
    })
    assert "Amala Yoga" not in names(YogaCalculator(None, mixed).calculate_amala_yoga())

    node_mixed = chart({
        "Jupiter": 10, "Sun": 2, "Moon": 3, "Mars": 6,
        "Mercury": 5, "Venus": 8, "Saturn": 9,
    })
    node_mixed["planets"]["Rahu"] = {"house": 10, "sign": 9, "longitude": 275.0}
    assert "Amala Yoga" not in names(YogaCalculator(None, node_mixed).calculate_amala_yoga())


def test_saraswati_is_not_a_conjunction_shortcut():
    valid = chart({
        "Mercury": 2, "Jupiter": 4, "Venus": 5,
        "Sun": 3, "Moon": 6, "Mars": 8, "Saturn": 11,
    })
    # Jupiter in Cancer in House 4 is exalted.
    result = YogaCalculator(None, valid).calculate_education_yogas()
    assert names(result) == {"Saraswati Yoga"}

    invalid = chart({
        "Mercury": 3, "Jupiter": 3, "Venus": 3,
        "Sun": 4, "Moon": 6, "Mars": 8, "Saturn": 11,
    })
    assert YogaCalculator(None, invalid).calculate_education_yogas() == []


def test_surya_yogas_exclude_moon_and_report_planet_nature():
    moon_only = chart({
        "Sun": 1, "Moon": 2, "Mars": 4, "Mercury": 5,
        "Jupiter": 6, "Venus": 8, "Saturn": 9,
    })
    assert YogaCalculator(None, moon_only).calculate_surya_yogas() == []

    with_mars = chart({
        "Sun": 1, "Moon": 3, "Mars": 2, "Mercury": 5,
        "Jupiter": 6, "Venus": 8, "Saturn": 9,
    })
    result = YogaCalculator(None, with_mars).calculate_surya_yogas()
    assert names(result) == {"Vesi Yoga"}
    assert result[0]["composition"] == "malefic"


def test_dhana_uses_an_explicit_bphs_special_combination():
    # Capricorn Lagna gives Taurus as House 5. BPHS 41.2 requires Venus in
    # that fifth house and Mars in House 11.
    value = chart({
        "Venus": 5, "Mars": 11, "Sun": 2, "Moon": 3,
        "Mercury": 6, "Jupiter": 8, "Saturn": 9,
    }, asc_sign=9)
    result = YogaCalculator(None, value).calculate_dhana_yogas()
    assert len(result) == 1
    assert result[0]["rule_id"] == "BPHS-41.2"
    assert result[0]["delivery_rule"]["reference"] == "BPHS 41.16"
    assert result[0]["qualification_rule"]["reference"] == "BPHS 41.17"


def test_viparita_returns_the_correct_named_lordship_yoga():
    value = chart({
        "Mercury": 8,  # 6th lord for Aries Lagna
        "Mars": 6,     # 8th lord
        "Jupiter": 12, # 12th lord
        "Sun": 2, "Moon": 3, "Venus": 5, "Saturn": 9,
    })
    result = YogaCalculator(None, value).calculate_viparita_raja_yogas()
    assert names(result) == {"Harsha Yoga", "Sarala Yoga", "Vimala Yoga"}


def test_viparita_honours_malefic_association_branch_outside_dusthana():
    value = chart({
        "Mercury": 5,  # 6th lord for Aries Lagna
        "Saturn": 5,   # classical malefic joins the 6th lord
        "Mars": 2, "Jupiter": 3, "Sun": 4, "Moon": 7, "Venus": 9,
    })
    result = viparita_yogas(
        value,
        lambda house: YogaCalculator(None, value)._get_house_lord(house),
        lambda _house: [],
    )
    harsha = next(row for row in result if row["name"] == "Harsha Yoga")
    assert harsha["formation_branches"] == ["malefic conjunction/aspect"]
    assert harsha["nature_context"]["source"]["reference_label"] == "BPHS 3.11"


def test_dharma_karma_requires_the_lords_together_in_an_auspicious_house():
    # Cancer Lagna: Jupiter rules 9 and Mars rules 10.
    value = chart({
        "Jupiter": 1, "Mars": 1, "Sun": 2, "Moon": 3,
        "Mercury": 6, "Venus": 8, "Saturn": 11,
    }, asc_sign=3)
    assert names(YogaCalculator(None, value).calculate_dharma_karma_yogas()) == {"Dharma-Karma Yoga"}

    value["planets"]["Mars"].update({"house": 2, "sign": value["houses"][1]["sign"]})
    assert YogaCalculator(None, value).calculate_dharma_karma_yogas() == []

    # Phaladeepika 6.37 says mahita-bhava, not Kendra/Trikona. House 2 is a
    # good house under the text's own 1.17 classification.
    value["planets"]["Jupiter"].update({"house": 2, "sign": value["houses"][1]["sign"]})
    result = YogaCalculator(None, value).calculate_dharma_karma_yogas()
    assert names(result) == {"Dharma-Karma Yoga"}
    assert result[0]["classical_name"] == "Raja Yoga of the conjoined 9th and 10th lords"

    # The same conjunction in a difficult house is rejected.
    value["planets"]["Jupiter"].update({"house": 6, "sign": value["houses"][5]["sign"]})
    value["planets"]["Mars"].update({"house": 6, "sign": value["houses"][5]["sign"]})
    assert YogaCalculator(None, value).calculate_dharma_karma_yogas() == []


def test_dharma_karma_does_not_relabel_single_yogakaraka_planet():
    # Taurus Lagna: Saturn owns both Houses 9 and 10. Phaladeepika 6.37 says
    # two lords; this belongs under the separate BPHS 34.13 Yogakaraka rule.
    value = chart({
        "Saturn": 1, "Sun": 2, "Moon": 3, "Mars": 5,
        "Mercury": 6, "Jupiter": 8, "Venus": 11,
    }, asc_sign=1)
    calculator = YogaCalculator(None, value)
    assert calculator.calculate_dharma_karma_yogas() == []
    assert any(row["planets"] == ["Saturn"] for row in calculator.calculate_raj_yogas())


def test_parivartana_uses_phaladeepika_dainya_khala_maha_partition():
    dainya = chart({"Mars": 6, "Mercury": 1})
    assert "Dainya Yoga" in names(YogaCalculator(None, dainya).calculate_parivartana_yogas())

    khala = chart({"Mercury": 5, "Sun": 3})
    assert "Khala Yoga" in names(YogaCalculator(None, khala).calculate_parivartana_yogas())

    maha = chart({"Venus": 5, "Sun": 2})
    assert "Maha Yoga" in names(YogaCalculator(None, maha).calculate_parivartana_yogas())


def test_nabhasa_uses_nala_name_and_suppresses_residual_sankhya():
    value = chart({p: index + 1 for index, p in enumerate(PLANETS)})
    for index, planet in enumerate(PLANETS):
        sign = (2, 5, 8, 11)[index % 4]
        value["planets"][planet].update({"sign": sign, "longitude": sign * 30.0 + 5 + index})
    result = YogaCalculator(None, value).calculate_nabhasa_yogas()
    assert names(result["ashraya_yogas"]) == {"Nala Yoga"}
    assert "sankhya_yogas" not in result


def test_nabhasa_requires_complete_akriti_house_pattern():
    complete = chart({
        "Sun": 1, "Moon": 1, "Mars": 1, "Mercury": 1,
        "Jupiter": 4, "Venus": 4, "Saturn": 4,
    })
    result = YogaCalculator(None, complete).calculate_nabhasa_yogas()
    assert "Gada Yoga" in names(result.get("akriti_yogas", []))

    partial = chart({p: 1 for p in PLANETS})
    result = YogaCalculator(None, partial).calculate_nabhasa_yogas()
    assert "Gada Yoga" not in names(result.get("akriti_yogas", []))


def test_nabhasa_includes_the_previously_missing_dala_family():
    value = chart({
        "Jupiter": 1, "Moon": 1, "Venus": 4, "Mercury": 7,
        "Sun": 2, "Mars": 5, "Saturn": 8,
    })
    # Make Moon waxing and Mercury free of malefic conjunction.
    value["planets"]["Sun"]["longitude"] = 10.0
    value["planets"]["Moon"]["longitude"] = 20.0
    result = YogaCalculator(None, value).calculate_nabhasa_yogas()
    assert "Mala Yoga" in names(result.get("dala_yogas", []))


def test_classical_core_does_not_return_invented_high_medium_low_grades():
    value = chart({
        "Moon": 1, "Jupiter": 4, "Venus": 4,
        "Sun": 2, "Mars": 10, "Mercury": 5, "Saturn": 8,
    })
    calculator = YogaCalculator(None, value)
    groups = [
        calculator.calculate_raj_yogas(), calculator.calculate_dhana_yogas(),
        calculator.calculate_panch_mahapurusha_yogas(), calculator.calculate_gaja_kesari_yoga(),
        calculator.calculate_amala_yoga(), calculator.calculate_viparita_raja_yogas(),
        calculator.calculate_dharma_karma_yogas(), calculator.calculate_chandra_yogas(),
        calculator.calculate_surya_yogas(), calculator.calculate_education_yogas(),
        calculator.calculate_parivartana_yogas(),
    ]
    groups.extend(calculator.calculate_nabhasa_yogas().values())
    assert all(row.get("strength") not in {"High", "Medium", "Low"} for group in groups for row in group)


def test_public_yoga_contract_keeps_keys_but_hides_unsourced_product_labels():
    value = chart({p: index + 1 for index, p in enumerate(PLANETS)})
    result = YogaCalculator(None, value).calculate_all_yogas()
    assert result["career_specific_yogas"] == []
    assert result["health_yogas"] == []
    assert result["marriage_yogas"] == []
    assert "major_doshas" in result
    assert "matru_dosha" in result["major_doshas"]
