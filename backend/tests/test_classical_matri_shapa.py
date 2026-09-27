from backend.calculators.classical_matri_shapa import (
    calculate_classical_matri_shapa,
    compact_matri_shapa_for_ai,
)
from backend.calculators.yoga_calculator import YogaCalculator


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def chart(asc_sign=0, placements=None, degrees=None):
    placements = placements or {}
    degrees = degrees or {}
    defaults = {"Sun": 2, "Moon": 3, "Mars": 4, "Mercury": 7, "Jupiter": 9, "Venus": 11, "Saturn": 12, "Rahu": 6, "Ketu": 10}
    rows = {}
    for name in PLANETS:
        house = placements.get(name, defaults[name])
        sign = (asc_sign + house - 1) % 12
        degree = degrees.get(name, 15.0)
        rows[name] = {"house": house, "sign": sign, "degree": degree, "longitude": sign * 30.0 + degree}
    return {
        "ascendant": asc_sign * 30.0 + 10.0,
        "houses": [{"house": house, "sign": (asc_sign + house - 1) % 12} for house in range(1, 13)],
        "planets": rows,
    }


def matched(result, verse):
    return f"BPHS-MS-{verse}" in result["matched_rule_ids"]


def test_all_thirteen_rules_are_explicit_and_progeny_scoped():
    result = calculate_classical_matri_shapa(chart())
    assert [row["rule_id"] for row in result["evaluated_rules"]] == [f"BPHS-MS-{verse}" for verse in range(34, 47)]
    assert result["source"]["verse_numbers"] == "83.34-46"
    assert result["scope"] == "progeny"


def test_verses_34_to_39_match_only_their_complete_chains():
    # Pisces: Moon rules H5; debilitated Moon satisfies the verse-34 alternative.
    assert matched(calculate_classical_matri_shapa(chart(11, {"Moon": 9, "Mars": 4, "Saturn": 5})), 34)
    # Cancer: Scorpio is H5, so Moon is both in H5 and debilitated.
    assert matched(calculate_classical_matri_shapa(chart(3, {"Moon": 5, "Saturn": 11, "Mars": 4})), 35)
    # Aries: fifth lord Sun in H6; lagna lord Mars debilitated in Cancer/H4; Moon joins Saturn.
    assert matched(calculate_classical_matri_shapa(chart(0, {"Sun": 6, "Mars": 4, "Moon": 2, "Saturn": 2})), 36)
    # Taurus Moon at 1 degree occupies a Saturn-ruled Capricorn navamsha.
    assert matched(calculate_classical_matri_shapa(chart(0, {"Sun": 6, "Moon": 2, "Mars": 1, "Saturn": 5}, {"Moon": 1.0})), 37)
    assert matched(calculate_classical_matri_shapa(chart(11, {"Moon": 5, "Saturn": 5, "Rahu": 5, "Mars": 5})), 38)
    # Leo: Mars rules H4.
    assert matched(calculate_classical_matri_shapa(chart(4, {"Mars": 2, "Saturn": 2, "Rahu": 2, "Sun": 5, "Moon": 1})), 39)


def test_verses_40_to_46_match_only_their_complete_chains():
    assert matched(calculate_classical_matri_shapa(chart(1, {"Venus": 6, "Mercury": 6, "Sun": 8, "Jupiter": 1, "Saturn": 1})), 40)
    assert matched(calculate_classical_matri_shapa(chart(2, {"Mars": 1, "Saturn": 1, "Mercury": 12, "Moon": 5, "Jupiter": 5, "Rahu": 5})), 41)
    assert matched(calculate_classical_matri_shapa(chart(0, {"Mars": 12, "Ketu": 2, "Moon": 7, "Rahu": 4, "Saturn": 5, "Sun": 10}, {"Sun": 20.0, "Moon": 5.0})), 42)
    assert matched(calculate_classical_matri_shapa(chart(1, {"Mercury": 8, "Jupiter": 5, "Sun": 6, "Moon": 6})), 43)
    assert matched(calculate_classical_matri_shapa(chart(3, {"Mars": 1, "Rahu": 1, "Moon": 5, "Saturn": 5})), 44)
    assert matched(calculate_classical_matri_shapa(chart(2, {"Mars": 1, "Rahu": 5, "Sun": 8, "Saturn": 12, "Mercury": 6})), 45)
    assert matched(calculate_classical_matri_shapa(chart(0, {"Mars": 8, "Rahu": 8, "Jupiter": 8, "Saturn": 5, "Moon": 5})), 46)


def test_moon_or_fourth_house_affliction_alone_is_not_matri_shapa():
    result = calculate_classical_matri_shapa(chart(0, {"Moon": 4, "Saturn": 4, "Rahu": 5}))
    assert result["present"] is False
    assert "not relabelled" in result["summary"]


def test_yoga_contract_and_chat_compaction_are_additive():
    value = chart(0, {"Mars": 8, "Rahu": 8, "Jupiter": 8, "Saturn": 5, "Moon": 5})
    result = YogaCalculator(None, value).calculate_major_doshas()
    assert result["matru_dosha"]["method"] == "bphs_matri_shapa_83_34_46"
    assert matched(result["matru_dosha"], 46)
    payload = {"major_doshas": result, "raj_yogas": []}
    compact = compact_matri_shapa_for_ai(payload)
    assert "evaluated_rules" in payload["major_doshas"]["matru_dosha"]
    assert "evaluated_rules" not in compact["major_doshas"]["matru_dosha"]


def test_janam_kundli_dosha_table_includes_matri_shapa_without_changing_contract():
    from backend.reports.assembly.janam_kundli_page_assembler import _dosha_table

    canonical = calculate_classical_matri_shapa(
        chart(0, {"Mars": 8, "Rahu": 8, "Jupiter": 8, "Saturn": 5, "Moon": 5})
    )
    table = _dosha_table({"matru_dosha": canonical}, "en")
    row = next(row for row in table["rows"] if row[0] == "Mātṛ-śāpa · progeny check")

    assert row[1] == "Yes"
    assert "83.46" in row[2]
