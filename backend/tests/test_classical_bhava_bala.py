from calculators.classical_bhava_bala import (
    _occupation_adjustment,
    _sign_form,
    _time_sign_adjustment,
    calculate_bhava_dig_bala,
)


def test_parasharas_light_pune_sample_non_lord_columns():
    """Cross-check PL 7.0.3 Sample Report 2, 30 Aug 1991 05:23 Pune.

    The lord column follows the selected Shadbala convention, so this test locks
    the four independent Bhava columns printed by PL rather than hiding a
    convention difference inside a broad total tolerance.
    """
    from types import SimpleNamespace
    from calculators.chart_calculator import ChartCalculator
    from calculators.divisional_chart_calculator import DivisionalChartCalculator
    from calculators.classical_bhava_bala import calculate_classical_bhava_bala

    birth = {
        "date": "1991-08-30", "time": "05:23:00", "timezone": "Asia/Kolkata",
        "latitude": 18.75, "longitude": 73.75,
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    chart["divisions"] = DivisionalChartCalculator(chart).calculate_all_divisional_charts()
    rows = calculate_classical_bhava_bala(birth, chart)

    expected_dig = [0, 20, 40, 30, 40, 20, 30, 10, 10, 60, 50, 50]
    expected_drishti = [-20, -10, 5, 67, 65, 19, 110, 69, 59, 31, -7, -20]
    expected_occupancy = [60, 0, -60, 0, 0, 0, -60, 0, 0, 0, 0, 0]
    expected_phase = [15, 0, 0, 0, 0, 15, 15, 0, 0, 15, 15, 0]
    for index in range(12):
        row = rows[str(index + 1)]
        assert abs(row["dig_bala"] - expected_dig[index]) < 0.1
        assert abs(row["drishti_bala"] - expected_drishti[index]) < 1.5
        assert row["planets_in_bala"] == expected_occupancy[index]
        assert row["day_night_bala"] == expected_phase[index]


def test_sign_forms_follow_bphs_half_sign_rules():
    assert _sign_form(8 * 30 + 14.99) == "biped"
    assert _sign_form(8 * 30 + 15.00) == "quadruped"
    assert _sign_form(9 * 30 + 14.99) == "quadruped"
    assert _sign_form(9 * 30 + 15.00) == "water"
    assert _sign_form(3 * 30) == "insect"
    assert _sign_form(11 * 30) == "water"


def test_bhava_dig_bala_uses_form_specific_zero_point():
    # Equal Bhava madhyas with Gemini rising. Biped Gemini in Lagna lies 180°
    # from its zero point (the seventh), hence the full 60 virupas.
    madhyas = [(60.0 + index * 30.0) % 360.0 for index in range(12)]
    value, form, reference = calculate_bhava_dig_bala(madhyas[0], madhyas)
    assert (value, form, reference) == (60.0, "biped", 7)


def test_occupation_adjustments_are_per_classical_planet():
    value, details = _occupation_adjustment(["Jupiter", "Mercury", "Sun", "Venus", "Rahu"])
    assert value == 60.0
    assert {row["planet"] for row in details} == {"Jupiter", "Mercury", "Sun"}


def test_day_night_adjustments_use_rising_classes_and_twilight_duals():
    assert _time_sign_adjustment(4, "day") == 15.0       # Leo, Seershodaya
    assert _time_sign_adjustment(0, "night") == 15.0     # Aries, Prishtodaya
    assert _time_sign_adjustment(11, "twilight") == 15.0 # Pisces, dual
    assert _time_sign_adjustment(11, "night") == 0.0
