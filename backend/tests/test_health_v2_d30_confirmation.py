from health_v2.divisional_confirmation_engine import D30HealthConfirmationEngine


def _planet(house, sign, dignity="neutral"):
    return {"house": house, "sign": sign, "dignity": dignity}


def test_d30_repeats_intervention_pressure_and_keeps_protection_visible():
    d1 = {
        "planets": {
            "Mars": _planet(8, 11),
            "Saturn": _planet(2, 5),
        }
    }
    d30 = {
        "ascendant": 308.0,  # Aquarius; Saturn is D30 Lagna lord.
        "planets": {
            "Sun": _planet(8, 5),
            "Moon": _planet(10, 7, "debilitated"),
            "Mars": _planet(8, 5),
            "Mercury": _planet(11, 8),
            "Jupiter": _planet(2, 11, "own_sign"),
            "Venus": _planet(4, 1, "own_sign"),
            "Saturn": _planet(2, 11),
            "Rahu": _planet(2, 11),
            "Ketu": _planet(2, 11),
        },
    }
    knee = {
        "stable_id": "health.anatomy.knees",
        "source_planets": ["Saturn"],
        "timing_planets": ["Saturn"],
    }

    result = D30HealthConfirmationEngine(d1, d30).calculate([knee])

    assert result["available"] is True
    assert result["intervention_markers"][0]["type"] == "mars_intervention_repetition"
    assert any(row["type"] == "sun_mars_intervention_confluence" for row in result["intervention_markers"])
    assert sum(row["type"] == "d30_lagna_lord_nodal_pressure" for row in result["pressure_factors"]) == 1
    assert any(row["type"] == "d30_jupiter_protects_lagna_lord" for row in result["protective_factors"])
    confirmation = result["finding_confirmations"]["health.anatomy.knees"]
    assert confirmation["status"] == "pressure_with_protection"
    assert sum(row["type"] == "d30_source_nodal_pressure" for row in confirmation["pressure_factors"]) == 1
    assert any(row["type"] == "d30_jupiter_source_protection" for row in confirmation["protective_factors"])


def test_missing_d30_cannot_create_confirmation():
    result = D30HealthConfirmationEngine({"planets": {}}, None).calculate([])
    assert result == {
        "available": False,
        "role": "confirmation_only",
        "finding_confirmations": {},
        "intervention_markers": [],
        "pressure_factors": [],
        "protective_factors": [],
    }


def test_d30_house_lord_bridge_repeats_anorectal_anatomy_generically():
    """Regression for chart 10323 without chart-id or event-specific logic.

    Aries D30 makes Mars lord of H8.  Mars in H7 therefore carries the H8
    perineum/anal-orifice field into the H7 rectum/anal-canal field.
    """
    d1 = {"planets": {"Mars": _planet(11, 0)}}
    d30 = {
        "ascendant": 4.0,  # Aries
        "planets": {
            "Sun": _planet(3, 2),
            "Moon": _planet(4, 3),
            "Mars": _planet(7, 6),
            "Mercury": _planet(6, 5),
            "Jupiter": _planet(9, 8),
            "Venus": _planet(2, 1),
            "Saturn": _planet(10, 9),
            "Rahu": _planet(5, 4),
            "Ketu": _planet(11, 10),
        },
    }
    finding = {
        "stable_id": "health.anatomy.anorectal_and_pelvic_region",
        "label": "Anorectal and pelvic region anatomical vulnerability",
        "body_zones": ["anorectal and pelvic region"],
        "source_planets": ["Mars"],
        "timing_planets": ["Mars"],
    }

    result = D30HealthConfirmationEngine(d1, d30).calculate([finding])

    house_link = next(
        row for row in result["house_lord_links"]
        if row["source_house"] == 8
    )
    assert (house_link["planet"], house_link["destination_house"]) == ("Mars", 7)
    confirmation = result["finding_confirmations"][finding["stable_id"]]
    anatomy_link = next(
        row for row in confirmation["anatomical_links"]
        if row["source_house"] == 8 and row["destination_house"] == 7
    )
    assert set(anatomy_link["matched_source_anatomy"]) >= {"anal orifice", "perineum"}
    assert set(anatomy_link["matched_destination_anatomy"]) >= {"anal canal", "rectum"}
    assert anatomy_link["pathology"] == [
        "inflammation", "suppuration", "tissue injury", "surgical intervention",
    ]
    assert confirmation["status"] == "anatomy_repeated"
    assert any(
        row["type"] == "d30_mars_dusthana_lord_anatomical_bridge"
        and row["source_house"] == 8
        and row["destination_house"] == 7
        for row in result["intervention_markers"]
    )


def test_d30_house_lord_bridge_works_for_non_anorectal_non_mars_pattern():
    """The resolver must work for every house/lord, not one learned event."""
    d1 = {"planets": {"Saturn": _planet(2, 9)}}
    d30 = {
        "ascendant": 94.0,  # Cancer; H10 is Aries, ruled by Mars.
        "planets": {
            "Sun": _planet(1, 3),
            "Moon": _planet(4, 6),
            "Mars": _planet(9, 11),
            "Mercury": _planet(3, 5),
            "Jupiter": _planet(6, 8),
            "Venus": _planet(11, 1),
            "Saturn": _planet(10, 0),
            "Rahu": _planet(2, 4),
            "Ketu": _planet(8, 10),
        },
    }
    # Saturn is a D1 carrier and, as lord of Cancer D30's H7/H8 signs, carries
    # those domains into H10 (knees). The same resolver must surface that
    # destination anatomy without a Mars- or anorectal-specific branch.
    knee = {
        "stable_id": "health.anatomy.knees",
        "label": "Knees anatomical vulnerability",
        "body_zones": ["knees"],
        "source_planets": ["Saturn"],
        "timing_planets": ["Saturn"],
    }
    result = D30HealthConfirmationEngine(d1, d30).calculate([knee])
    confirmation = result["finding_confirmations"][knee["stable_id"]]
    assert any(
        row["planet"] == "Saturn"
        and row["destination_house"] == 10
        and "knees" in row["matched_destination_anatomy"]
        for row in confirmation["anatomical_links"]
    )

    eye = {
        **knee,
        "stable_id": "health.anatomy.eyes",
        "label": "Eye anatomical vulnerability",
        "body_zones": ["eyes"],
    }
    unrelated = D30HealthConfirmationEngine(d1, d30).calculate([eye])
    assert unrelated["finding_confirmations"][eye["stable_id"]]["anatomical_links"] == []
