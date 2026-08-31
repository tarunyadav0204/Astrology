from datetime import datetime
from copy import deepcopy

from longevity.calculator import LongevityCalculator, _pair_category


BIRTH = {
    "name": "Calculator Contract",
    "date": "1990-01-15",
    "time": "10:30",
    "place": "Delhi",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "timezone": "Asia/Kolkata",
}

PLANETS = {
    "Sun": {"longitude": 270.0, "sign": 9, "degree": 0.0, "house": 9},
    "Moon": {"longitude": 120.0, "sign": 4, "degree": 0.0, "house": 4},
    "Mars": {"longitude": 45.0, "sign": 1, "degree": 15.0, "house": 1},
    "Mercury": {"longitude": 280.0, "sign": 9, "degree": 10.0, "house": 9},
    "Jupiter": {"longitude": 95.0, "sign": 3, "degree": 5.0, "house": 3},
    "Venus": {"longitude": 310.0, "sign": 10, "degree": 10.0, "house": 10},
    "Saturn": {"longitude": 200.0, "sign": 6, "degree": 20.0, "house": 6},
    "Rahu": {"longitude": 20.0, "sign": 0, "degree": 20.0, "house": 12},
    "Ketu": {"longitude": 200.0, "sign": 6, "degree": 20.0, "house": 6},
}
CHART = {"ascendant": 30.0, "planets": PLANETS}


def test_jaimini_pair_mapping_matches_product_contract():
    assert _pair_category(0, 3) == "Purnayu"  # movable + movable
    assert _pair_category(1, 4) == "Alpayu"  # fixed + fixed
    assert _pair_category(2, 5) == "Madhyayu"  # dual + dual
    assert _pair_category(0, 1) == "Madhyayu"
    assert _pair_category(0, 2) == "Alpayu"
    assert _pair_category(1, 2) == "Purnayu"


def test_hora_lagna_uses_sunrise_elapsed_ghatis_not_sun_moon_algebra():
    calculator = LongevityCalculator(BIRTH, CHART)
    hora = calculator._hora_lagna()
    expected = (hora["sunrise_sun_longitude"] + (hora["elapsed_ghatis"] / 2.5) * 30) % 360
    old_shortcut = (PLANETS["Sun"]["longitude"] + PLANETS["Moon"]["longitude"] - CHART["ascendant"]) % 360
    assert abs(hora["longitude"] - expected) < 1e-8
    assert abs(hora["longitude"] - old_shortcut) > 1e-3
    assert "BPHS Ch. 5.4–5" in hora["derivation"]


def test_pre_sunrise_hora_lagna_counts_from_previous_local_sunrise():
    birth = {**BIRTH, "time": "04:00"}
    hora = LongevityCalculator(birth, CHART)._hora_lagna()
    assert hora["sunrise"].startswith("1990-01-14")
    assert 0 < hora["elapsed_ghatis"] < 60


def test_longevity_result_is_ui_and_chat_ready():
    result = LongevityCalculator(BIRTH, CHART).calculate(
        as_of=datetime(2026, 8, 30), horizon_years=3
    )

    assert result["schema_version"] == "longevity.v2"
    assert result["calculation_convention"]["ashtakavarga_profile"] == "pvr_narasimha_rao"
    assert result["chat_context"]["ashtakavarga_profile"] == "pvr_narasimha_rao"
    assert result["verdict"]["compartment"]["label"] in {"Alpayu", "Madhyayu", "Purnayu"}
    assert result["verdict"]["compartment"]["classical_modifications"]["source"].startswith("Jaimini")
    assert result["safeguards"]["source"].startswith("Brihat Parashara")
    assert len(result["pillars"]) == 3
    assert len(result["maraka_dossier"]["ranked_planets"]) == 9
    assert result["maraka_dossier"]["ranked_planets"][0]["classical_factor_count"] >= result["maraka_dossier"]["ranked_planets"][-1]["classical_factor_count"]
    assert result["chat_context"]["context_type"] == "deterministic_longevity_evidence"
    assert "never predict a death date" in result["chat_context"]["guardrail"]
    assert all(window["label"] != "death" for window in result["crisis_windows"])
    assert all("score" not in window for window in result["crisis_windows"])
    assert "score" not in result["verdict"]["current_activation"]
    assert all(window["convergence"]["classification_basis"].endswith("classical numerical score") for window in result["crisis_windows"])
    assert all(window["level"] != "strong_convergence" for window in result["crisis_windows"] if window["convergence"]["confirmed_systems"] < 3)
    assert all("ad_start" not in window for window in result["crisis_windows"])
    assert all(window["dasha_period"]["boundary_type"] == "actual_antardasha" for window in result["crisis_windows"])
    assert all(not window["convergence"]["micro"]["evidence"] for window in result["crisis_windows"] if not window["components"]["transit_bav"])


def test_longevity_uses_selected_ashtakavarga_reduction_profile_end_to_end():
    result = LongevityCalculator(
        BIRTH,
        CHART,
        ashtakavarga_profile="parasharas_light_7",
    ).calculate(as_of=datetime(2026, 8, 30), horizon_years=1)

    convention = result["calculation_convention"]
    timing = result["maraka_dossier"]["sensitive_points"]["ashtakavarga_timing"]
    assert convention["ashtakavarga_profile"] == "parasharas_light_7"
    assert convention["count_ascendant_as_occupant"] is True
    assert convention["mixed_higher_empty_rule"] == "subtract_occupied_value"
    assert timing["reduction_profile"] == "parasharas_light_7"
    assert result["chat_context"]["ashtakavarga_profile"] == "parasharas_light_7"


def test_jaimini_jupiter_vriddhi_is_one_whole_compartment():
    chart = deepcopy(CHART)
    chart["ascendant"] = 0.0
    chart["planets"]["Jupiter"].update({"sign": 0, "longitude": 5.0})
    chart["planets"]["Venus"].update({"sign": 1, "longitude": 45.0})
    chart["planets"]["Moon"].update({"sign": 11, "longitude": 350.0})
    chart["planets"]["Sun"].update({"sign": 9, "longitude": 270.0})
    chart["planets"]["Rahu"].update({"sign": 2, "longitude": 70.0})
    chart["planets"]["Ketu"].update({"sign": 8, "longitude": 250.0})
    calculator = LongevityCalculator(BIRTH, chart)
    result = calculator._jaimini_kakshya_modification(
        "Madhyayu", [{"verdict": "Alpayu"}, {"verdict": "Alpayu"}, {"verdict": "Madhyayu"}]
    )
    assert result["final_compartment"] == "Purnayu"
    assert result["net_shift"] == 1
    assert result["rules"][1]["applied"] is True


def test_jaimini_saturn_hrasa_and_own_sign_exception_are_traceable():
    chart = deepcopy(CHART)
    chart["ascendant"] = 0.0
    chart["planets"]["Sun"].update({"sign": 0, "longitude": 5.0})
    chart["planets"]["Moon"].update({"sign": 4, "longitude": 125.0})
    chart["planets"]["Mars"].update({"sign": 1, "longitude": 45.0})
    chart["planets"]["Mercury"].update({"sign": 10, "longitude": 310.0})
    chart["planets"]["Jupiter"].update({"sign": 3, "longitude": 95.0})
    chart["planets"]["Venus"].update({"sign": 2, "longitude": 75.0})
    chart["planets"]["Saturn"].update({"sign": 5, "longitude": 170.0})
    chart["planets"]["Rahu"].update({"sign": 8, "longitude": 250.0})
    chart["planets"]["Ketu"].update({"sign": 2, "longitude": 70.0})
    calculator = LongevityCalculator(BIRTH, chart)
    pair_rows = [{"verdict": "Alpayu"}, {"verdict": "Madhyayu"}, {"verdict": "Madhyayu"}]
    reduced = calculator._jaimini_kakshya_modification("Madhyayu", pair_rows)
    assert reduced["final_compartment"] == "Alpayu"
    assert reduced["rules"][0]["applied"] is True

    calculator.planets["Saturn"].update({"sign": 9, "longitude": 290.0})
    protected = calculator._jaimini_kakshya_modification("Madhyayu", pair_rows)
    assert protected["final_compartment"] == "Madhyayu"
    assert protected["rules"][0]["exception"] == "own_or_exalted"


def test_jaimini_saturn_hrasa_requires_malefic_influence_in_selected_profile():
    chart = deepcopy(CHART)
    chart["ascendant"] = 0.0
    chart["planets"]["Saturn"].update({"sign": 5, "longitude": 170.0})
    chart["planets"]["Rahu"].update({"sign": 3, "longitude": 110.0})
    chart["planets"]["Ketu"].update({"sign": 9, "longitude": 290.0})
    calculator = LongevityCalculator(BIRTH, chart)
    result = calculator._jaimini_kakshya_modification(
        "Madhyayu", [{"verdict": "Alpayu"}, {"verdict": "Madhyayu"}, {"verdict": "Madhyayu"}]
    )
    assert result["final_compartment"] == "Madhyayu"
    assert result["rules"][0]["applied"] is False
    assert "requires malefic influence" in result["rules"][0]["interpretive_profile"]


def test_moon_in_lagna_or_seventh_gives_moon_saturn_pair_precedence():
    chart = deepcopy(CHART)
    chart["ascendant"] = 30.0
    chart["planets"]["Moon"].update({"sign": 1, "longitude": 35.0})
    result = LongevityCalculator(BIRTH, chart).calculate(as_of=datetime(2026, 8, 30), horizon_years=1)
    moon_saturn = result["pillars"][0]["pairs"][1]["verdict"]
    assert result["verdict"]["compartment"]["pair_majority"] == moon_saturn
    assert "2.1.9" in result["verdict"]["compartment"]["selection_rule"]


def test_shared_lagna_and_eighth_lord_uses_eighth_from_eighth_lord():
    chart = deepcopy(CHART)
    chart["ascendant"] = 0.0  # Aries: Mars rules both Lagna and the eighth.
    result = LongevityCalculator(BIRTH, chart).calculate(as_of=datetime(2026, 8, 30), horizon_years=1)
    first_pair = result["pillars"][0]["pairs"][0]
    assert first_pair["label"] == "Lagnesha + 8th-from-8th Lord"
    assert "eighth from the eighth" in first_pair["right"]["derivation"]


def test_parent_views_rotate_native_houses_and_include_d12_confirmation():
    expectations = {
        "mother": {"base": 4, "eighth": 11, "third": 6, "marakas": (5, 10), "karaka": "Moon"},
        "father": {"base": 9, "eighth": 4, "third": 11, "marakas": (10, 3), "karaka": "Sun"},
    }
    for subject, expected in expectations.items():
        result = LongevityCalculator(BIRTH, CHART, subject=subject).calculate(
            as_of=datetime(2026, 8, 30), horizon_years=3
        )
        points = result["maraka_dossier"]["sensitive_points"]
        assert result["subject"]["key"] == subject
        assert result["subject"]["derived_house"] == expected["base"]
        assert result["subject"]["natural_karaka"] == expected["karaka"]
        assert points["parental_eighth"]["native_house"] == expected["eighth"]
        assert points["parental_third"]["native_house"] == expected["third"]
        assert points["derived_maraka_second"]["native_house"] == expected["marakas"][0]
        assert points["derived_maraka_seventh"]["native_house"] == expected["marakas"][1]
        assert points["d12_confirmation"]["parent_eighth"]
        assert result["safeguards"]["applicable"] is False
        assert all("native_house" in row for row in result["maraka_dossier"]["ranked_planets"])
        assert all(window["level"] != "critical" for window in result["crisis_windows"] if not window["parent_corroboration"]["d12_stress_present"])
        assert result["chat_context"]["subject"] == subject
