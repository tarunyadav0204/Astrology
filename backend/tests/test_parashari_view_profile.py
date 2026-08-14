from types import SimpleNamespace

from calculators.chart_calculator import ChartCalculator, resolve_ayanamsha_mode
from charts.chart_cache import build_chart_cache_key


def _birth_data():
    return SimpleNamespace(
        date="1980-04-02",
        time="14:55:00",
        latitude=29.1492,
        longitude=75.7217,
        timezone="UTC+5:30",
    )


def test_true_nodes_only_change_node_positions_under_same_ayanamsha():
    calculator = ChartCalculator({})
    mean_chart = calculator.calculate_chart(_birth_data(), "mean", "lahiri")
    true_chart = calculator.calculate_chart(_birth_data(), "true", "lahiri")

    assert true_chart["planets"]["Sun"]["longitude"] == mean_chart["planets"]["Sun"]["longitude"]
    assert abs(true_chart["planets"]["Rahu"]["longitude"] - mean_chart["planets"]["Rahu"]["longitude"]) > 0.01
    assert abs(true_chart["planets"]["Ketu"]["longitude"] - mean_chart["planets"]["Ketu"]["longitude"]) > 0.01


def test_selectable_ayanamsha_changes_sidereal_positions():
    calculator = ChartCalculator({})
    lahiri = calculator.calculate_chart(_birth_data(), "mean", "lahiri")
    raman = calculator.calculate_chart(_birth_data(), "mean", "raman")

    assert abs(raman["ayanamsa"] - lahiri["ayanamsa"]) > 0.1
    assert abs(raman["planets"]["Sun"]["longitude"] - lahiri["planets"]["Sun"]["longitude"]) > 0.1


def test_profile_specific_cache_keys_cannot_collide():
    mean_key = build_chart_cache_key(
        "parashari-view-divisional-v1",
        "birth-hash",
        division=12,
        ayanamsha="lahiri",
        node_type="mean",
    )
    true_key = build_chart_cache_key(
        "parashari-view-divisional-v1",
        "birth-hash",
        division=12,
        ayanamsha="lahiri",
        node_type="true",
    )
    raman_key = build_chart_cache_key(
        "parashari-view-divisional-v1",
        "birth-hash",
        division=12,
        ayanamsha="raman",
        node_type="mean",
    )

    assert len({mean_key, true_key, raman_key}) == 3


def test_unknown_ayanamsha_is_rejected():
    try:
        resolve_ayanamsha_mode("not-a-standard")
    except ValueError as exc:
        assert "Unsupported ayanamsha" in str(exc)
    else:
        raise AssertionError("unknown ayanamsha was accepted")
