from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from ai.parallel_chat.prompt_blocks import _parashari_json_footer  # noqa: E402
from calculators.yogi_calculator import YogiCalculator  # noqa: E402


def _chart(sun: float, moon: float) -> dict:
    return {
        "planets": {
            "Sun": {"longitude": sun, "house": 1, "sign": int(sun // 30)},
            "Moon": {"longitude": moon, "house": 2, "sign": int(moon // 30)},
        },
        "houses": [{"house_number": house, "sign": house - 1} for house in range(1, 13)],
    }


def test_classical_yogi_formula_and_three_distinct_planet_roles() -> None:
    # 100 + 200 + 93°20′ = 33°20′; Avayogi is five stars ahead = 100°.
    result = YogiCalculator(_chart(100.0, 200.0)).calculate_yogi_points({})

    assert math.isclose(result["yogi"]["longitude"], 33.3333333333, abs_tol=1e-8)
    assert result["yogi"]["nakshatra_name"] == "Krittika"
    assert result["yogi"]["lord"] == "Sun"  # nakshatra lord
    assert result["yogi"]["sign_lord"] == "Venus"
    assert result["duplicate_yogi"]["lord"] == "Venus"  # sign lord

    assert math.isclose(result["avayogi"]["longitude"], 100.0, abs_tol=1e-8)
    assert result["avayogi"]["nakshatra_name"] == "Pushya"
    assert result["avayogi"]["lord"] == "Saturn"  # nakshatra lord


def test_uses_existing_chart_longitudes_without_recomputing_ephemeris() -> None:
    result = YogiCalculator(_chart(100.0, 200.0)).calculate_yogi_points({
        "date": "not-a-date",
        "time": "not-a-time",
    })
    assert result["calculation_basis"]["source"] == "chart_sidereal_longitudes"


def test_nakshatra_boundaries_and_longitude_wrap_are_stable() -> None:
    span = 360.0 / 27.0
    before = YogiCalculator._nakshatra_details(span - 1e-9)
    boundary = YogiCalculator._nakshatra_details(span)
    wrapped = YogiCalculator._nakshatra_details(360.0)

    assert before["nakshatra_name"] == "Ashwini"
    assert boundary["nakshatra_name"] == "Bharani"
    assert wrapped["nakshatra_name"] == "Ashwini"


def test_tithi_dagdha_is_not_invented_from_avayogi_plus_twelve_degrees() -> None:
    result = YogiCalculator(_chart(100.0, 200.0)).calculate_yogi_points({})

    assert result["paksha_tithi_number"] == 9
    assert [row["sign_name"] for row in result["tithi_dagdha_rashis"]] == ["Leo", "Scorpio"]
    assert all("longitude" not in row for row in result["tithi_dagdha_rashis"])


def test_purnima_and_amavasya_have_no_tithi_dagdha_signs() -> None:
    # A 168-degree elongation is the 15th tithi in its paksha.
    result = YogiCalculator(_chart(10.0, 178.0)).calculate_yogi_points({})
    assert result["paksha_tithi_number"] == 15
    assert result["tithi_dagdha_rashis"] == []
    assert result["dagdha_rashi"] is None


def test_iyer_dagdha_entries_that_differ_in_secondary_tables() -> None:
    assert YogiCalculator.TITHI_DAGDHA_SIGNS[10] == (4, 7)  # Leo, Scorpio
    assert YogiCalculator.TITHI_DAGDHA_SIGNS[13] == (1, 4)  # Taurus, Leo


def test_matches_astrovision_lifesign_published_reference_chart() -> None:
    # Astro-Vision reference: 14-Feb-1987 06:30 Chennai, Chitra Paksha.
    # Its report publishes these exact sidereal luminary positions and output.
    sun = 301 + 6 / 60 + 56 / 3600
    moon = 123 + 0 / 60 + 55 / 3600
    result = YogiCalculator(_chart(sun, moon)).calculate_yogi_points({})

    assert math.isclose(result["yogi"]["longitude"], 157 + 27 / 60 + 52 / 3600, abs_tol=1 / 3600)
    assert result["yogi"]["nakshatra_name"] == "Uttara Phalguni"
    assert result["yogi"]["lord"] == "Sun"
    assert result["duplicate_yogi"]["lord"] == "Mercury"
    assert result["avayogi"]["nakshatra_name"] == "Anuradha"
    assert result["avayogi"]["lord"] == "Saturn"
    assert [row["sign_name"] for row in result["tithi_dagdha_rashis"]] == ["Libra", "Capricorn"]


def test_matches_parasharas_light_7_published_reference_chart() -> None:
    # Parashara's Light 7 sample: 23-Apr-1990 06:15 Chennai.
    result = YogiCalculator({"planets": {}, "houses": []}).calculate_yogi_points({
        "date": "1990-04-23",
        "time": "06:15:00",
        "latitude": 13.0833333333,
        "longitude": 80.2833333333,
        "timezone": "Asia/Kolkata",
    })

    assert math.isclose(result["yogi"]["longitude"], 80 + 48 / 60 + 19 / 3600, abs_tol=2 / 3600)
    assert result["yogi"]["lord"] == "Jupiter"
    assert result["duplicate_yogi"]["lord"] == "Mercury"
    assert result["avayogi"]["lord"] == "Sun"
    assert [row["sign_name"] for row in result["tithi_dagdha_rashis"]] == ["Taurus", "Leo"]


def test_chat_prompt_keeps_duplicate_yogi_and_tithi_dagdha_distinct() -> None:
    prompt = _parashari_json_footer()
    assert "Duplicate Yogi" in prompt
    assert "sign lord of that same point" in prompt
    assert "Tithi Dagdha Rashis" in prompt
    assert "separate tithi-derived modifier" in prompt
