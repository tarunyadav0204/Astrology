from backend.calculators.classical_pitri_shapa import (
    calculate_classical_pitri_shapa,
    compact_pitri_shapa_for_ai,
)
from backend.calculators.yoga_calculator import YogaCalculator


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def chart(asc_sign=0, placements=None, degrees=None):
    placements = placements or {}
    degrees = degrees or {}
    defaults = {
        "Sun": 2, "Moon": 3, "Mars": 4, "Mercury": 7, "Jupiter": 9,
        "Venus": 11, "Saturn": 12, "Rahu": 6, "Ketu": 10,
    }
    rows = {}
    for name in PLANETS:
        house = placements.get(name, defaults[name])
        sign = (asc_sign + house - 1) % 12
        degree = degrees.get(name, 15.0)
        rows[name] = {
            "house": house,
            "sign": sign,
            "degree": degree,
            "longitude": sign * 30.0 + degree,
        }
    return {
        "ascendant": asc_sign * 30.0 + 10.0,
        "houses": [{"house": house, "sign": (asc_sign + house - 1) % 12} for house in range(1, 13)],
        "planets": rows,
    }


def matched(result, rule_id):
    return rule_id in result["matched_rule_ids"]


def test_all_eleven_rules_are_explicitly_evaluated():
    result = calculate_classical_pitri_shapa(chart())
    assert [row["rule_id"] for row in result["evaluated_rules"]] == [f"BPHS-PS-{verse}" for verse in range(20, 31)]
    assert result["source"]["verse_numbers"] == "83.20-30"
    assert result["scope"] == "progeny"


def test_verse_20_requires_debilitated_sun_saturn_navamsa_and_both_flanks():
    result = calculate_classical_pitri_shapa(chart(
        2,
        {"Sun": 5, "Mars": 4, "Saturn": 6},
        {"Sun": 12.0},
    ))
    assert matched(result, "BPHS-PS-20")


def test_verse_21_full_solar_chain_matches():
    result = calculate_classical_pitri_shapa(chart(
        0,
        {"Sun": 9, "Mars": 9, "Rahu": 8, "Ketu": 10, "Saturn": 7},
    ))
    assert matched(result, "BPHS-PS-21")


def test_verses_22_to_26_match_only_complete_multi_part_combinations():
    verse_22 = calculate_classical_pitri_shapa(chart(
        1,
        {"Jupiter": 4, "Mercury": 3, "Sun": 3, "Mars": 1, "Saturn": 5},
    ))
    assert matched(verse_22, "BPHS-PS-22")

    verse_23 = calculate_classical_pitri_shapa(chart(
        3,
        {"Moon": 5, "Mars": 2, "Sun": 2, "Rahu": 1, "Saturn": 5},
    ))
    assert matched(verse_23, "BPHS-PS-23")

    verse_24 = calculate_classical_pitri_shapa(chart(
        0,
        {"Jupiter": 5, "Mars": 1, "Saturn": 5},
    ))
    assert matched(verse_24, "BPHS-PS-24")

    verse_25 = calculate_classical_pitri_shapa(chart(
        4,
        {"Mars": 5, "Jupiter": 5, "Rahu": 1, "Saturn": 9},
    ))
    assert matched(verse_25, "BPHS-PS-25")

    verse_26 = calculate_classical_pitri_shapa(chart(
        0,
        {"Jupiter": 8, "Sun": 3, "Saturn": 3, "Mars": 4, "Rahu": 4},
    ))
    assert matched(verse_26, "BPHS-PS-26")


def test_verses_27_to_30_match_their_exact_placement_chains():
    verse_27 = calculate_classical_pitri_shapa(chart(
        0,
        {"Sun": 1, "Mars": 5, "Saturn": 5, "Rahu": 8, "Jupiter": 12},
    ))
    assert matched(verse_27, "BPHS-PS-27")

    verse_28 = calculate_classical_pitri_shapa(chart(
        0,
        {"Sun": 8, "Rahu": 8, "Saturn": 5, "Mars": 1},
    ))
    assert matched(verse_28, "BPHS-PS-28")

    verse_29 = calculate_classical_pitri_shapa(chart(
        1,
        {"Mars": 1, "Jupiter": 5, "Saturn": 8},
    ))
    assert matched(verse_29, "BPHS-PS-29")

    verse_30 = calculate_classical_pitri_shapa(chart(
        0,
        {"Mercury": 5, "Jupiter": 6, "Rahu": 6},
    ))
    assert matched(verse_30, "BPHS-PS-30")


def test_sun_rahu_saturn_or_ninth_house_affliction_alone_is_not_pitri_shapa():
    result = calculate_classical_pitri_shapa(chart(
        0,
        {"Sun": 2, "Rahu": 2, "Saturn": 9, "Ketu": 3, "Mars": 4, "Jupiter": 7, "Mercury": 11},
    ))
    assert result["present"] is False
    assert result["matched_rules"] == []
    assert "not relabelled" in result["summary"]


def test_multiple_verses_are_returned_as_corroboration_without_invented_severity():
    result = calculate_classical_pitri_shapa(chart(
        0,
        {"Sun": 8, "Rahu": 8, "Saturn": 5, "Jupiter": 5, "Mars": 1},
    ))
    assert {"BPHS-PS-24", "BPHS-PS-28"}.issubset(result["matched_rule_ids"])
    assert result["corroborating_factors"]["multiple_classical_rules_match"] >= 2
    assert "severity" not in result
    assert "strength" not in result


def test_benefic_context_is_reported_without_cancelling_a_matched_verse():
    result = calculate_classical_pitri_shapa(chart(
        0,
        {"Mercury": 5, "Jupiter": 6, "Rahu": 6, "Venus": 11},
    ))
    assert matched(result, "BPHS-PS-30")
    assert any(row["planet"] == "Venus" and row["relation"] == "aspects_house_5" for row in result["protective_factors"])
    assert result["present"] is True
    assert "do not cancel" in result["protection_note"]


def test_legacy_major_dosha_key_returns_canonical_result():
    value = chart(0, {"Mercury": 5, "Jupiter": 6, "Rahu": 6})
    result = YogaCalculator(None, value).calculate_major_doshas()
    assert set(result) == {"mangal_dosha", "kaal_sarp_dosha", "pitra_dosha", "matru_dosha"}
    assert result["pitra_dosha"]["method"] == "bphs_pitri_shapa_83_20_30"
    assert "BPHS-PS-30" in result["pitra_dosha"]["matched_rule_ids"]


def test_chat_context_prunes_unmatched_rule_ledger_without_mutating_api_result():
    full_result = calculate_classical_pitri_shapa(chart())
    payload = {"major_doshas": {"pitra_dosha": full_result}, "raj_yogas": []}
    compact = compact_pitri_shapa_for_ai(payload)

    assert "evaluated_rules" in payload["major_doshas"]["pitra_dosha"]
    assert "evaluated_rules" not in compact["major_doshas"]["pitra_dosha"]
    assert compact["major_doshas"]["pitra_dosha"]["source"] == full_result["source"]
    assert compact["raj_yogas"] == []


def test_karma_context_uses_canonical_result_without_gulika_or_broad_ancestral_claim():
    from backend.calculators.karma_context_builder import KarmaContextBuilder

    builder = KarmaContextBuilder.__new__(KarmaContextBuilder)
    builder.chart_data = chart(0, {"Mercury": 5, "Jupiter": 6, "Rahu": 6})
    result = builder._analyze_pitru_dosha()

    assert result["method"] == "bphs_pitri_shapa_83_20_30"
    assert result["has_ancestral_debt"] is False  # legacy key retained without a broader debt claim
    assert result["pitri_shapa_present"] is True
    assert "not part" in result["gulika_factor"]
    assert "broader ancestral effects are not inferred" in result["karmic_meaning"]


def test_report_labels_the_result_as_progeny_scoped_pitri_shapa():
    from backend.reports.assembly.janam_kundli_page_assembler import _dosha_table

    canonical = calculate_classical_pitri_shapa(chart())
    table = _dosha_table({"pitra_dosha": canonical}, "en")
    pitri_row = next(row for row in table["rows"] if row[0] == "Pitṛ-śāpa · progeny check")
    assert pitri_row[0] == "Pitṛ-śāpa · progeny check"
    assert "eleven complete" in pitri_row[2]
