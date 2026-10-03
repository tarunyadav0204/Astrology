from types import SimpleNamespace

from calculators.chart_calculator import ChartCalculator, resolve_ayanamsha_mode
from calculators.real_transit_calculator import RealTransitCalculator
from calculators.transit_calculator import TransitCalculator
from panchang.panchang_calculator import PanchangCalculator
from shared.dasha_calculator import DashaCalculator
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


def test_professional_dashboard_ayanamsha_catalog_is_calculable():
    calculator = ChartCalculator({})
    modes = (
        "lahiri", "raman", "krishnamurti", "yukteshwar", "true_chitra",
        "true_revati", "true_pushya", "jn_bhasin", "kp_291",
        "lahiri_1940", "lahiri_icrc",
    )

    charts = {
        mode: calculator.calculate_chart(_birth_data(), "mean", mode)
        for mode in modes
    }

    assert set(charts) == set(modes)
    assert all("calculation_profile" not in chart for chart in charts.values())
    assert len({round(chart["ayanamsa"], 6) for chart in charts.values()}) >= 7


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


def test_legacy_default_clients_keep_lahiri_results_after_an_alternate_profile_call():
    birth = _birth_data()
    chart_calculator = ChartCalculator({})
    baseline_chart = chart_calculator.calculate_chart(birth)
    chart_calculator.calculate_chart(birth, "true", "raman")
    repeated_chart = chart_calculator.calculate_chart(birth)

    assert "calculation_profile" not in baseline_chart
    assert baseline_chart["ascendant"] == repeated_chart["ascendant"]
    assert baseline_chart["planets"]["Moon"]["longitude"] == repeated_chart["planets"]["Moon"]["longitude"]

    baseline_panchang = PanchangCalculator().calculate_birth_panchang(vars(birth))
    PanchangCalculator("raman").calculate_birth_panchang(vars(birth))
    repeated_panchang = PanchangCalculator().calculate_birth_panchang(vars(birth))
    assert "calculation_profile" not in baseline_panchang
    assert baseline_panchang["nakshatra"]["number"] == repeated_panchang["nakshatra"]["number"]
    assert baseline_panchang["nakshatra"]["pada"] == repeated_panchang["nakshatra"]["pada"]


def test_legacy_constructor_and_method_signatures_remain_valid():
    birth = _birth_data()
    transit = TransitCalculator({}).calculate_transits(
        birth,
        "2026-09-19T09:00:23+00:00",
    )

    assert set(transit) == {"planets", "houses", "ayanamsa", "ascendant"}
    assert RealTransitCalculator().ayanamsha_key == "lahiri"
    assert DashaCalculator().ayanamsha_key == "lahiri"
