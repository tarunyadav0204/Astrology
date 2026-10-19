"""Chart and all chat adapters must agree on complete natal degree checks."""
import pytest

from calculators.classical_mrityu_bhaga import (
    JATAKA_PARIJATA_SARVARTHA,
    evaluate_mrityu_bhaga,
)
from calculators.mrityu_bhaga_calculator import MrityuBhagaCalculator
from calculators.sniper_points_calculator import SniperPointsCalculator


def sensitive_chart():
    return {
        'ascendant': 0.5,
        'planets': {
            'Sun': {'longitude': 19.5, 'house': 1},
            'Rahu': {'longitude': 13.5, 'house': 1},
            'Ketu': {'longitude': 7.5, 'house': 1},
            'Gulika': {'longitude': 22.5, 'house': 1},
            'Mandi': {'longitude': 22.5, 'house': 1},
        },
    }


def test_chat_and_chart_include_lagna_nodes_and_one_gulika_mandi():
    chart = sensitive_chart()
    display = SniperPointsCalculator(chart, {}, {}).calculate_mrityu_bhaga()
    chat = MrityuBhagaCalculator(chart).analyze_chart_mrityu_bhaga()
    expected = {'Ascendant', 'Sun', 'Rahu', 'Ketu', 'Mandi'}
    assert {r['point'] for r in display['afflicted_points']} == expected
    assert chat['afflicted_points'] == display['afflicted_points']
    assert {r['planet'] for r in chat['planets_in_mrityu']} == expected
    assert chat['total_count'] == 5
    assert chat['table_key'] == display['table_key']
    assert 'Critical health risk' not in chat['overall_risk']


def test_gulika_only_input_is_supported_without_duplicate_counts():
    chart = sensitive_chart()
    del chart['planets']['Mandi']
    assert MrityuBhagaCalculator(chart).analyze_chart_mrityu_bhaga()['total_count'] == 5
    assert evaluate_mrityu_bhaga('Gulika', 22.5)['is_mrityu_bhaga']


def test_missing_coordinate_is_not_treated_as_zero_degree_lagna():
    result = MrityuBhagaCalculator({'planets': {'Moon': {}}}).analyze_chart_mrityu_bhaga()
    assert result['planet_analysis'] == {}
    assert result['total_count'] == 0


@pytest.mark.parametrize('point,degrees', JATAKA_PARIJATA_SARVARTHA.items())
def test_all_sign_boundaries_and_chat_chart_parity(point, degrees):
    for sign, ordinal in enumerate(degrees):
        for offset, matches in ((ordinal - 1, True), (ordinal - .5, True), (ordinal, False)):
            longitude = sign * 30 + offset
            chart = {'planets': {}}
            if point == 'Ascendant':
                chart['ascendant'] = longitude
            else:
                chart['planets'][point] = {'longitude': longitude}
            display = SniperPointsCalculator(chart, {}, {}).calculate_mrityu_bhaga()
            chat = MrityuBhagaCalculator(chart).analyze_chart_mrityu_bhaga()
            assert display['has_affliction'] is matches
            assert chat['afflicted_points'] == display['afflicted_points']
            assert bool(chat['total_count']) is matches


@pytest.mark.parametrize('capability', ['conditions.mrityu_bhaga', 'points.sniper'])
def test_verified_and_calculator_first_tool_paths_match_chart(monkeypatch, capability):
    from chat.calculator_menu import run_calculator
    from calculators.chart_calculator import ChartCalculator
    from calculators.divisional_chart_calculator import DivisionalChartCalculator

    chart = sensitive_chart()
    monkeypatch.setattr(ChartCalculator, 'calculate_chart', lambda *a, **kw: chart)
    monkeypatch.setattr(DivisionalChartCalculator, 'calculate_divisional_chart', lambda *a, **kw: {})
    facts = run_calculator(capability, {})['facts']
    if capability == 'points.sniper':
        facts = facts['mrityu_bhaga']
    assert {r['point'] for r in facts['afflicted_points']} == {'Ascendant', 'Sun', 'Rahu', 'Ketu', 'Mandi'}


def test_instant_compact_payload_keeps_lagna_and_nodes():
    from context_agents.agents.sniper_pts import _compress_mrityu_bhaga

    result = SniperPointsCalculator(sensitive_chart(), {}, {}).calculate_mrityu_bhaga()
    compact = _compress_mrityu_bhaga(result)
    assert {r['p'] for r in compact['r']} == {'Asc', 'Sun', 'Rahu', 'Ketu', 'Mandi'}
