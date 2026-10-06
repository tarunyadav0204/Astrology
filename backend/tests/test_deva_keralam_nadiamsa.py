import json

import pytest

from classical_rules.deva_keralam.nadiamsa import (
    DevaKeralamTableError,
    build_deva_keralam_fact_set,
    calculate_nadiamsa,
    load_nadiamsa_table,
)


def test_pinned_table_is_complete_and_source_versioned():
    table = load_nadiamsa_table()
    assert table.table_key == "deva_keralam.santhanam_book_1.table_1.v1"
    assert set(table.names_by_ordinal) == set(range(1, 151))
    assert table.names_by_ordinal[1] == "Vasudha"
    assert table.names_by_ordinal[15] == "Kutilaa"
    assert table.names_by_ordinal[76] == "Mahaamaayaa"
    assert table.names_by_ordinal[150] == "Parameswari"
    assert "printed pages ix-xiii" in table.source_reference


@pytest.mark.parametrize(
    ("longitude", "modality", "physical", "ordinal", "name"),
    [
        (0.01, "movable", 1, 1, "Vasudha"),
        (29.99, "movable", 150, 150, "Parameswari"),
        (30.01, "fixed", 1, 150, "Parameswari"),
        (59.99, "fixed", 150, 1, "Vasudha"),
        (60.01, "dual", 1, 76, "Mahaamaayaa"),
        (75.01, "dual", 76, 1, "Vasudha"),
    ],
)
def test_table_one_order_is_applied_by_sign_modality(longitude, modality, physical, ordinal, name):
    result = calculate_nadiamsa(longitude, subject="Moon")
    assert result.sign_modality == modality
    assert result.physical_division == physical
    assert result.ordinal == ordinal
    assert result.name == name


def test_former_and_latter_halves_are_six_arcminutes_each():
    former = calculate_nadiamsa(10.05, subject="Jupiter")
    latter = calculate_nadiamsa(10.15, subject="Jupiter")
    exact_midpoint = calculate_nadiamsa(10.1, subject="Jupiter")

    assert former.physical_division == latter.physical_division == 51
    assert former.half == "former"
    assert latter.half == "latter"
    assert exact_midpoint.half == "latter"
    assert exact_midpoint.on_half_boundary is True
    assert exact_midpoint.birth_time_precision_warning is True


def test_sign_ingress_belongs_to_new_sign_without_float_boundary_drift():
    result = calculate_nadiamsa(30.0, subject="Sun")
    assert result.sign_name == "Taurus"
    assert result.degree_in_sign == 0.0
    assert result.physical_division == 1
    assert result.ordinal == 150
    assert result.on_division_boundary is True


def test_boundary_distance_and_uncertainty_are_explicit():
    secure = calculate_nadiamsa(
        10.05,
        subject="ascendant",
        longitude_uncertainty_arcseconds=120,
    )
    crossing = calculate_nadiamsa(
        10.05,
        subject="ascendant",
        longitude_uncertainty_arcseconds=180,
    )
    unknown = calculate_nadiamsa(10.05, subject="ascendant")

    assert secure.distance_to_division_boundary_arcseconds == pytest.approx(180.0)
    assert secure.distance_to_half_boundary_arcseconds == pytest.approx(180.0)
    assert secure.precision_status == "verified_within_boundary"
    assert secure.birth_time_precision_warning is False
    assert crossing.precision_status == "crosses_boundary"
    assert crossing.birth_time_precision_warning is True
    assert unknown.precision_status == "unverified"
    assert unknown.birth_time_precision_warning is True


def test_planetary_position_does_not_claim_a_birth_time_warning_by_default():
    result = calculate_nadiamsa(125.03, subject="Jupiter")
    assert result.precision_status == "ephemeris_position"
    assert result.birth_time_precision_warning is False


def test_incomplete_or_ocr_damaged_table_fails_closed(tmp_path):
    invalid = {
        "schema_version": "test",
        "table_key": "incomplete",
        "edition": "test",
        "source": {"reference": "test page"},
        "ordering": {
            "movable": "1_to_150",
            "fixed": "150_to_1",
            "dual": "76_to_150_then_1_to_75",
        },
        "names": [{"ordinal": 1, "source_name": "Vasudha"}],
    }
    path = tmp_path / "incomplete.json"
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(DevaKeralamTableError, match="ordinals 1..150"):
        calculate_nadiamsa(0.01, table_path=path)


def test_chart_adapter_is_opt_in_non_mutating_and_source_carrying():
    chart = {
        "ascendant": 0.05,
        "planets": {
            "Sun": {"longitude": 30.01},
            "Moon": {"longitude": 60.01},
            "Missing": {"sign": 4},
        },
    }
    before = json.loads(json.dumps(chart))
    facts = build_deva_keralam_fact_set(
        chart, ascendant_longitude_uncertainty_arcseconds=60
    )

    assert chart == before
    assert facts.require("deva_keralam.ascendant.nadiamsa.name").value == "Vasudha"
    assert facts.require("deva_keralam.Sun.nadiamsa.name").value == "Parameswari"
    assert facts.require("deva_keralam.Moon.nadiamsa.name").value == "Mahaamaayaa"
    assert facts.get("deva_keralam.Missing.nadiamsa.name") is None
    source = facts.require("deva_keralam.ascendant.nadiamsa.ordinal")
    assert source.source_rules == ("DEVA_KERALAM.BOOK_1.TABLE_1.NADIAMSA_ORDER",)
    assert source.calculator_bindings == (
        "classical_rules.deva_keralam.nadiamsa.calculate_nadiamsa",
    )


@pytest.mark.parametrize("longitude", [None, "not-a-number", float("nan"), float("inf")])
def test_invalid_longitudes_fail_instead_of_fabricating_a_position(longitude):
    with pytest.raises(ValueError):
        calculate_nadiamsa(longitude)
